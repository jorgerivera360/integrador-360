"""
Provisioning — Endpoints para onboarding de clientes
Responsabilidades:
- Guardar credenciales en GCP Secret Manager + fallback local
- Provisionar contenedor Docker (modificar docker-compose.yml + levantar)
- Consultar estado del contenedor
Fase: 9-10 — Frontend (Onboarding)
"""
import os
import json
import subprocess
import yaml
import threading
from fastapi import APIRouter, Depends, HTTPException
from api.dependencies import get_db
from api.auth import require_role
from api.schemas.credentials import CredentialsSaveRequest, ERP_CREDENTIAL_SCHEMAS

router = APIRouter(prefix="/clients/{client_id}", tags=["Provisioning"])

COMPOSE_PATH = os.getenv("COMPOSE_PATH", "/opt/integrador/docker-compose.yml")
DOCKER_IMAGE = os.getenv("DOCKER_IMAGE", "integrador-360")
GCP_KEY_PATH = os.getenv("GCP_KEY_HOST_PATH", "/etc/integrador/gcp-key.json")
CREDENTIALS_HOST_PATH = os.getenv("CREDENTIALS_HOST_PATH", "/etc/integrador/credentials")
LOGS_HOST_PATH = os.getenv("LOGS_HOST_PATH", "/var/log/integrador")
_compose_lock = threading.Lock()


# --- Helpers ---

def _get_client(cursor, client_id: int) -> dict:
    cursor.execute(
        "SELECT id, client_id, erp_type, is_active FROM clients WHERE id = %s",
        (client_id,)
    )
    client = cursor.fetchone()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return client


# --- POST /clients/{id}/credentials ---

@router.post("/credentials")
def save_credentials(
    client_id: int,
    body: CredentialsSaveRequest,
    db=Depends(get_db),
    current_user=Depends(require_role("superadmin", "admin"))
):
    cursor = db.cursor()
    client = _get_client(cursor, client_id)
    slug = client["client_id"]
    erp_type = client["erp_type"]

    # Validar credenciales ERP según el tipo (excel no tiene ERP)
    if erp_type != "excel":
        schema_class = ERP_CREDENTIAL_SCHEMAS.get(erp_type)
        if not schema_class:
            raise HTTPException(status_code=400, detail=f"erp_type '{erp_type}' no soportado")
        try:
            schema_class(**body.erp)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Credenciales ERP inválidas: {e}")

    # Armar payload del secret (sin client_id, igual que los existentes)
    secret_payload = {
        "erp": body.erp if erp_type != "excel" else {},
        "odoo": body.odoo.model_dump()
    }

    # 1. Guardar en GCP Secret Manager
    try:
        from google.cloud import secretmanager

        gcp_client = secretmanager.SecretManagerServiceClient()
        project_id = os.getenv("GCP_PROJECT_ID")
        secret_id = f"integrador-{slug}"
        parent = f"projects/{project_id}"
        secret_name = f"{parent}/secrets/{secret_id}"

        # Crear secret o agregar versión si ya existe
        try:
            gcp_client.create_secret(
                request={
                    "parent": parent,
                    "secret_id": secret_id,
                    "secret": {"replication": {"automatic": {}}},
                }
            )
        except Exception:
            # Ya existe — está bien, solo agregamos versión
            pass

        gcp_client.add_secret_version(
            request={
                "parent": secret_name,
                "payload": {"data": json.dumps(secret_payload).encode("UTF-8")},
            }
        )
        gcp_saved = True
    except Exception as e:
        gcp_saved = False
        gcp_error = str(e)

    # 2. Guardar fallback local siempre
    try:
        from config.loader import ConfigLoader
        loader = ConfigLoader(client_id=slug)
        loader.save_credentials(secret_payload)
        local_saved = True
    except Exception:
        local_saved = False

    if not gcp_saved and not local_saved:
        return {
            "success": False,
            "msg": f"No se pudieron guardar las credenciales: {gcp_error}"
        }

    return {
        "success": True,
        "secret_name": f"integrador-{slug}",
        "gcp": gcp_saved,
        "local": local_saved,
        "msg": "Credenciales guardadas exitosamente"
    }


# --- POST /clients/{id}/provision ---

@router.post("/provision")
def provision_container(
    client_id: int,
    db=Depends(get_db),
    current_user=Depends(require_role("superadmin", "admin"))
):
    cursor = db.cursor()
    client = _get_client(cursor, client_id)
    slug = client["client_id"]

    # Verificar que existan credenciales
    try:
        from config.loader import ConfigLoader
        loader = ConfigLoader(client_id=slug)
        if not loader.credentials_exist():
            config = loader.load_config()
            if not config:
                raise HTTPException(
                    status_code=400,
                    detail="No hay credenciales guardadas. Guarde las credenciales primero."
                )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="No hay credenciales guardadas. Guarde las credenciales primero."
        )

    service_name = f"integrador-{slug}"

    # Leer, modificar y escribir docker-compose.yml con lock
    with _compose_lock:
        try:
            with open(COMPOSE_PATH, "r") as f:
                compose = yaml.safe_load(f)
        except FileNotFoundError:
            raise HTTPException(status_code=500, detail=f"No se encontró {COMPOSE_PATH}")

        if service_name in compose.get("services", {}):
            raise HTTPException(status_code=409, detail=f"El contenedor '{service_name}' ya existe en docker-compose.yml")

        compose["services"][service_name] = {
            "image": DOCKER_IMAGE,
            "container_name": service_name,
            "restart": "unless-stopped",
            "environment": [
                f"CLIENT_ID={slug}",
                "DATABASE_URL=${DATABASE_URL}",
                "ENV=${ENV}",
                "GCP_PROJECT_ID=${GCP_PROJECT_ID}",
                "GOOGLE_APPLICATION_CREDENTIALS=${GOOGLE_APPLICATION_CREDENTIALS}",
            ],
            "volumes": [
                f"{GCP_KEY_PATH}:{GCP_KEY_PATH}:ro",
                f"{CREDENTIALS_HOST_PATH}:{CREDENTIALS_HOST_PATH}",
                f"{LOGS_HOST_PATH}:{LOGS_HOST_PATH}",
            ],
        }

        try:
            with open(COMPOSE_PATH, "w") as f:
                yaml.dump(compose, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error escribiendo docker-compose.yml: {e}")

    # Levantar el contenedor (cwd = directorio del compose para que resuelva ${VARS})
    compose_dir = os.path.dirname(COMPOSE_PATH)
    try:
        result = subprocess.run(
            ["docker", "compose", "-f", COMPOSE_PATH, "up", "-d", service_name],
            capture_output=True, text=True, timeout=60,
            cwd=compose_dir,
        )
        if result.returncode != 0:
            return {
                "success": False,
                "msg": f"docker compose up falló: {result.stderr.strip()}"
            }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "msg": "Timeout al levantar el contenedor (60s)"
        }
    except FileNotFoundError:
        return {
            "success": False,
            "msg": "docker compose no está disponible en el contenedor API"
        }

    return {
        "success": True,
        "container": service_name,
        "msg": f"Contenedor '{service_name}' creado y levantado exitosamente"
    }


# --- GET /clients/{id}/provision/status ---

# --- GET /clients/{id}/credentials/status ---

@router.get("/credentials/status")
def get_credentials_status(
    client_id: int,
    db=Depends(get_db),
    current_user=Depends(require_role("superadmin", "admin", "viewer"))
):
    cursor = db.cursor()
    client = _get_client(cursor, client_id)
    slug = client["client_id"]

    # Verificar GCP
    gcp_exists = False
    try:
        from google.cloud import secretmanager

        gcp_client = secretmanager.SecretManagerServiceClient()
        project_id = os.getenv("GCP_PROJECT_ID")
        secret_name = f"projects/{project_id}/secrets/integrador-{slug}/versions/latest"
        gcp_client.access_secret_version(request={"name": secret_name})
        gcp_exists = True
    except Exception:
        gcp_exists = False

    # Verificar local
    credentials_path = os.getenv("CREDENTIALS_PATH", "/etc/integrador/credentials")
    local_path = os.path.join(credentials_path, f"integrador-{slug}.json")
    local_exists = os.path.exists(local_path)

    return {
        "exists": gcp_exists or local_exists,
        "gcp": gcp_exists,
        "local": local_exists,
        "secret_name": f"integrador-{slug}",
    }


# --- GET /clients/{id}/provision/status ---

@router.get("/provision/status")
def get_provision_status(
    client_id: int,
    db=Depends(get_db),
    current_user=Depends(require_role("superadmin", "admin", "viewer"))
):
    cursor = db.cursor()
    client = _get_client(cursor, client_id)
    slug = client["client_id"]
    service_name = f"integrador-{slug}"

    # Verificar si existe en docker-compose.yml
    in_compose = False
    try:
        with open(COMPOSE_PATH, "r") as f:
            compose = yaml.safe_load(f)
        in_compose = service_name in compose.get("services", {})
    except Exception:
        pass

    # Verificar si el contenedor existe y su estado
    container_status = None
    container_exists = False
    try:
        result = subprocess.run(
            ["docker", "inspect", "--format", "{{.State.Status}}", service_name],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            container_exists = True
            container_status = result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    return {
        "exists": in_compose or container_exists,
        "in_compose": in_compose,
        "container_running": container_exists,
        "status": container_status,
        "container": service_name,
    }


# --- DELETE /clients/{id}/credentials ---

@router.delete("/credentials")
def delete_credentials(
    client_id: int,
    db=Depends(get_db),
    current_user=Depends(require_role("superadmin", "admin"))
):
    cursor = db.cursor()
    client = _get_client(cursor, client_id)
    slug = client["client_id"]

    gcp_result = cleanup_gcp_secret(slug)
    local_result = cleanup_local_credentials(slug)

    exito = gcp_result.get("success") or local_result.get("success")
    return {
        "success": exito,
        "gcp": gcp_result,
        "local": local_result,
        "msg": "Credenciales eliminadas" if exito else "No se pudieron eliminar las credenciales"
    }


# --- DELETE /clients/{id}/provision ---

@router.delete("/provision")
def delete_provision(
    client_id: int,
    db=Depends(get_db),
    current_user=Depends(require_role("superadmin", "admin"))
):
    cursor = db.cursor()
    client = _get_client(cursor, client_id)
    slug = client["client_id"]

    result = cleanup_container(slug)
    return {
        "success": result.get("success", False),
        "detail": result,
        "msg": f"Contenedor 'integrador-{slug}' eliminado" if result.get("success") else "No se pudo eliminar el contenedor"
    }


# --- Funciones de cleanup (usadas por DELETE /clients/{id} y endpoints individuales) ---

def cleanup_gcp_secret(slug: str) -> dict:
    """Elimina el secret integrador-{slug} de GCP Secret Manager."""
    try:
        from google.cloud import secretmanager

        gcp_client = secretmanager.SecretManagerServiceClient()
        project_id = os.getenv("GCP_PROJECT_ID")
        secret_name = f"projects/{project_id}/secrets/integrador-{slug}"
        gcp_client.delete_secret(request={"name": secret_name})
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


def cleanup_local_credentials(slug: str) -> dict:
    """Elimina el archivo local de credenciales."""
    try:
        credentials_path = os.getenv("CREDENTIALS_PATH", "/etc/integrador/credentials")
        file_path = os.path.join(credentials_path, f"integrador-{slug}.json")
        if os.path.exists(file_path):
            os.remove(file_path)
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


def cleanup_container(slug: str) -> dict:
    """Baja el contenedor y lo quita del docker-compose.yml."""
    service_name = f"integrador-{slug}"
    result_info = {"container": service_name}

    # 1. Bajar el contenedor (docker directo, no compose — funciona aunque ya no esté en el yml)
    try:
        stop = subprocess.run(
            ["docker", "stop", service_name],
            capture_output=True, text=True, timeout=30
        )
        rm = subprocess.run(
            ["docker", "rm", "-f", service_name],
            capture_output=True, text=True, timeout=30
        )
        result_info["stopped"] = stop.returncode == 0 or rm.returncode == 0
    except Exception as e:
        result_info["stopped"] = False
        result_info["stop_error"] = str(e)

    # 2. Quitar del docker-compose.yml
    with _compose_lock:
        try:
            with open(COMPOSE_PATH, "r") as f:
                compose = yaml.safe_load(f)

            if service_name in compose.get("services", {}):
                del compose["services"][service_name]
                with open(COMPOSE_PATH, "w") as f:
                    yaml.dump(compose, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
                result_info["removed_from_compose"] = True
            else:
                result_info["removed_from_compose"] = False
        except Exception as e:
            result_info["removed_from_compose"] = False
            result_info["compose_error"] = str(e)

    result_info["success"] = result_info.get("stopped", False) or result_info.get("removed_from_compose", False)
    return result_info