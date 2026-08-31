"""
Catálogo — endpoints de enumeraciones y funciones del sistema.
GET /catalog/determination-functions
GET /catalog/flow-types
GET /catalog/erp-types
"""
from fastapi import APIRouter
from transform.utils.determination_functions import CATALOG

router = APIRouter(prefix="/catalog", tags=["catalog"])


@router.get("/determination-functions")
def get_determination_functions():
    result = []
    for name, entry in CATALOG.items():
        result.append({
            "name": name,
            "label": entry["label"],
            "descripcion": entry["descripcion"],
            "params": entry["params"],
        })
    return {"code": 200, "result": result}


@router.get("/flow-types")
def get_flow_types():
    return {"code": 200, "result": [
        {"value": "items", "label": "Productos"},
        {"value": "customer", "label": "Clientes"},
        {"value": "supplier", "label": "Proveedores"},
        {"value": "purchases", "label": "Compras"},
        {"value": "sales", "label": "Ventas"},
    ]}


@router.get("/erp-types")
def get_erp_types():
    return {"code": 200, "result": [
        {"value": "ws", "label": "SIESA WS"},
        {"value": "connekta", "label": "SIESA Connekta"},
        {"value": "sap", "label": "SAP B1"},
        {"value": "excel", "label": "Excel"},
    ]}