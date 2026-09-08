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
            "image": "integrador-360",
            "container_name": service_name,
            "restart": "unless-stopped",
            "environment": [
                f"CLIENT_ID={slug}",
                f"DATABASE_URL={os.getenv('DATABASE_URL')}",
                f"ENV={os.getenv('ENV', 'prod')}",
                f"GCP_PROJECT_ID={os.getenv('GCP_PROJECT_ID', 'hale-treat-398215')}",
                "GOOGLE_APPLICATION_CREDENTIALS=/etc/integrador/gcp-key.json",
            ],
            "volumes": [
                "/etc/integrador/gcp-key.json:/etc/integrador/gcp-key.json:ro",
                "/etc/integrador/credentials:/etc/integrador/credentials",
                "/var/log/integrador:/var/log/integrador",
            ],
        }

        try:
            with open(COMPOSE_PATH, "w") as f:
                yaml.dump(compose, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error escribiendo docker-compose.yml: {e}")

    # Levantar el contenedor
    try:
        result = subprocess.run(
            ["docker", "compose", "-f", COMPOSE_PATH, "up", "-d", service_name],
            capture_output=True, text=True, timeout=60
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

@router.get("/provision/status")
def get_provision_status(
    client_id: int,
    db=Depends(get_db),
    current_user=Depends(require_role("superadmin", "admin", "viewer"))
):
    cursor = db.cursor()
    client = _get_client(cursor, client_id)
    slug = client["client_id"]
    container_name = f"integrador-{slug}"

    # Verificar si el contenedor existe y su estado
    try:
        result = subprocess.run(
            ["docker", "inspect", "--format", "{{.State.Status}}", container_name],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            return {
                "exists": False,
                "status": None,
                "container": container_name
            }

        status = result.stdout.strip()
        return {
            "exists": True,
            "status": status,
            "container": container_name
        }

    except (subprocess.TimeoutExpired, FileNotFoundError):
        return {
            "exists": False,
            "status": None,
            "container": container_name,
            "msg": "No se pudo consultar Docker"
        }