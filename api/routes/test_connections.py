from fastapi import APIRouter, Depends, HTTPException
from api.dependencies import get_db
from api.auth import require_role

router = APIRouter(prefix="/clients/{client_id}/test", tags=["Test Connections"])


@router.post("/erp")
def test_erp_connection(
    client_id: int,
    db=Depends(get_db),
    current_user=Depends(require_role("superadmin", "admin"))
):
    cursor = db.cursor()

    # Obtener client_slug y erp_type de la BD
    cursor.execute(
        "SELECT client_id, erp_type FROM clients WHERE id = %s AND is_active = true",
        (client_id,)
    )
    client = cursor.fetchone()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado o desactivado")

    try:
        from config.loader import ConfigLoader
        from main import build_connector

        # Cargar credenciales de GCP
        loader = ConfigLoader(client_id=client["client_id"])
        config = loader.load_config()

        if not config:
            return {
                "code": 400,
                "success": False,
                "msg": "No se pudieron cargar las credenciales de GCP"
            }

        # Instanciar conector y probar
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


@router.post("/odoo")
def test_odoo_connection(
    client_id: int,
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
        from config.loader import ConfigLoader
        from connection.jsonrpc import JsonRPC

        # Cargar credenciales de GCP
        loader = ConfigLoader(client_id=client["client_id"])
        config = loader.load_config()

        if not config:
            return {
                "code": 400,
                "success": False,
                "msg": "No se pudieron cargar las credenciales de GCP"
            }

        # Instanciar JsonRPC y probar
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