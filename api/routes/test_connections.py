from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from api.dependencies import get_db
from api.auth import require_role
from api.schemas.credentials import TestConnectionRequest

router = APIRouter(tags=["Test Connections"])


# --- POST /test/erp (sin cliente, solo con credenciales del body) ---

@router.post("/test/erp")
def test_erp_standalone(
    body: TestConnectionRequest,
    current_user=Depends(require_role("superadmin", "admin"))
):
    if not body.erp or not body.erp.get("tipo"):
        raise HTTPException(status_code=400, detail="Se requiere 'erp' con campo 'tipo' en el body")

    try:
        from main import build_connector

        erp_type = body.erp.pop("tipo")
        config = {
            "erp": body.erp,
            "odoo": {},
            "client_id": "test",
        }
        connector = build_connector(erp_type, config)
        status, message = connector.test_connection()

        return {
            "code": 200 if status else 400,
            "success": status,
            "erp_type": erp_type,
            "msg": message,
        }
    except Exception as e:
        return {
            "code": 500,
            "success": False,
            "msg": f"Error al probar conexión ERP: {str(e)}",
        }


# --- POST /test/odoo (sin cliente, solo con credenciales del body) ---

@router.post("/test/odoo")
def test_odoo_standalone(
    body: TestConnectionRequest,
    current_user=Depends(require_role("superadmin", "admin"))
):
    if not body.odoo:
        raise HTTPException(status_code=400, detail="Se requieren credenciales WMS en el body")

    try:
        from connection.jsonrpc import JsonRPC

        config = {
            "erp": {},
            "odoo": body.odoo.model_dump(),
            "client_id": "test",
        }
        odoo = JsonRPC(config)
        status, message = odoo.test_connection()

        return {
            "code": 200 if status else 400,
            "success": status,
            "odoo_url": config["odoo"]["url"],
            "msg": message,
        }
    except Exception as e:
        return {
            "code": 500,
            "success": False,
            "msg": f"Error al probar conexión WMS: {str(e)}",
        }


# --- POST /clients/{id}/test/erp (con cliente existente) ---

@router.post("/clients/{client_id}/test/erp")
def test_erp_connection(
    client_id: int,
    body: Optional[TestConnectionRequest] = None,
    db=Depends(get_db),
    current_user=Depends(require_role("superadmin", "admin"))
):
    cursor = db.cursor()

    cursor.execute(
        "SELECT client_id, erp_type FROM clients WHERE id = %s AND is_active = true",
        (client_id,)
    )
    client = cursor.fetchone()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado o desactivado")

    try:
        from main import build_connector

        # Si vienen credenciales en el body, usar esas
        if body and body.erp:
            config = {
                "erp": body.erp,
                "odoo": {},
                "client_id": client["client_id"]
            }
        else:
            # Cargar de GCP como siempre
            from config.loader import ConfigLoader
            loader = ConfigLoader(client_id=client["client_id"])
            config = loader.load_config()

            if not config:
                return {
                    "code": 400,
                    "success": False,
                    "msg": "No se pudieron cargar las credenciales de GCP"
                }
            config["client_id"] = client["client_id"]

        connector = build_connector(client["erp_type"], config)
        status, message = connector.test_connection()

        return {
            "code": 200 if status else 400,
            "success": status,
            "erp_type": client["erp_type"],
            "msg": message
        }

    except Exception as e:
        return {
            "code": 500,
            "success": False,
            "msg": f"Error al probar conexión ERP: {str(e)}"
        }


@router.post("/clients/{client_id}/test/odoo")
def test_odoo_connection(
    client_id: int,
    body: Optional[TestConnectionRequest] = None,
    db=Depends(get_db),
    current_user=Depends(require_role("superadmin", "admin"))
):
    cursor = db.cursor()

    cursor.execute(
        "SELECT client_id FROM clients WHERE id = %s AND is_active = true",
        (client_id,)
    )
    client = cursor.fetchone()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado o desactivado")

    try:
        from connection.jsonrpc import JsonRPC

        # Si vienen credenciales en el body, usar esas
        if body and body.odoo:
            config = {
                "erp": {},
                "odoo": body.odoo.model_dump(),
                "client_id": client["client_id"]
            }
        else:
            # Cargar de GCP como siempre
            from config.loader import ConfigLoader
            loader = ConfigLoader(client_id=client["client_id"])
            config = loader.load_config()

            if not config:
                return {
                    "code": 400,
                    "success": False,
                    "msg": "No se pudieron cargar las credenciales de GCP"
                }
            config["client_id"] = client["client_id"]

        odoo = JsonRPC(config)
        status, message = odoo.test_connection()

        return {
            "code": 200 if status else 400,
            "success": status,
            "odoo_url": config["odoo"]["url"],
            "msg": message
        }

    except Exception as e:
        return {
            "code": 500,
            "success": False,
            "msg": f"Error al probar conexión Odoo: {str(e)}"
        }