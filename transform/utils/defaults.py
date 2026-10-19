"""
Defaults de tipado y validación por flow_type.
Se usan como fallback cuando el flow_config no trae los campos.
Fase: 3 — Transform Layer
"""

NORMALIZE_DEFAULTS = {
    "items": {
        "campos_float": ["peso", "volumen", "costo", "precio", "iva"],
        "campos_int": [
            "vence", "use_expiration_date", "expiration_time",
            "ind_compra", "ind_venta", "ind_manufactura",
        ],
        "campos_fecha": [],
        "campos_obligatorios": ["referencia", "descripcion"],
        "campos_default_cero": [],
        "campos_mayor_cero": [],
    },
    "customer": {
        "campos_float": [],
        "campos_int": [],
        "campos_fecha": [],
        "campos_obligatorios": ["nombre", "identificacion"],
        "campos_default_cero": [],
        "campos_mayor_cero": [],
    },
    "supplier": {
        "campos_float": [],
        "campos_int": [],
        "campos_fecha": [],
        "campos_obligatorios": ["nombre", "identificacion"],
        "campos_default_cero": [],
        "campos_mayor_cero": [],
    },
    "purchases": {
        "campos_float": ["cantidad", "precio_unitario", "impuesto"],
        "campos_int": [],
        "campos_fecha": ["fecha_entrega"],
        "campos_obligatorios": [
            "compra", "producto", "proveedor", "sucursal_proveedor",
            "fecha_entrega", "estado", "almacen",
        ],
        "campos_default_cero": ["precio_unitario"],
        "campos_mayor_cero": ["cantidad"],
    },
    "sales": {
        "campos_float": ["cantidad_pedida", "precio_unitario", "impuesto"],
        "campos_int": [],
        "campos_fecha": ["fecha_pedido"],
        "campos_obligatorios": [
            "pedido", "producto", "cliente", "sucursal_cliente",
            "fecha_pedido", "estado", "almacen",
        ],
        "campos_default_cero": ["precio_unitario"],
        "campos_mayor_cero": ["cantidad_pedida"],
    },
}


def get_normalize_config(flow_config, flow_type):
    """Extrae config de tipado/validación del flow_config con fallback a defaults."""
    defaults = NORMALIZE_DEFAULTS.get(flow_type, {})
    return {
        "campos_float": set(flow_config.get("campos_float", defaults.get("campos_float", []))),
        "campos_int": set(flow_config.get("campos_int", defaults.get("campos_int", []))),
        "campos_fecha": set(flow_config.get("campos_fecha", defaults.get("campos_fecha", []))),
        "campos_obligatorios": flow_config.get("campos_obligatorios", defaults.get("campos_obligatorios", [])),
        "campos_default_cero": set(flow_config.get("campos_default_cero", defaults.get("campos_default_cero", []))),
        "campos_mayor_cero": set(flow_config.get("campos_mayor_cero", defaults.get("campos_mayor_cero", []))),
    }
