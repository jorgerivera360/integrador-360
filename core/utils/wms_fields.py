"""
wms_fields — Carga y aplica campos WMS dinámicos desde BD.
El catálogo define qué campos del transform se incluyen en el payload de Odoo.
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor


def _get_db_url():
    return os.environ.get(
        "DATABASE_URL",
        "postgresql://integrador:integrador360@localhost:5432/integrador"
    )


def cargar_wms_mappings(modelo, logger=None):
    """Carga los mappings activos para un modelo de Odoo.

    Retorna dict con dos keys:
        cabecera: lista de {campo_origen, campo_destino, tipo_valor, valor_default}
        linea:    lista de {campo_origen, campo_destino, tipo_valor, valor_default}
    """
    resultado = {"cabecera": [], "linea": []}
    try:
        conn = psycopg2.connect(_get_db_url())
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            """SELECT campo_origen, campo_destino, ubicacion, tipo_valor, valor_default
               FROM wms_field_mappings
               WHERE is_active = true AND %s = ANY(modelos)
               ORDER BY ubicacion, campo_origen""",
            (modelo,)
        )
        for row in cursor.fetchall():
            resultado[row["ubicacion"]].append({
                "campo_origen": row["campo_origen"],
                "campo_destino": row["campo_destino"],
                "tipo_valor": row["tipo_valor"],
                "valor_default": row["valor_default"],
            })
        conn.close()
        if logger:
            total = len(resultado["cabecera"]) + len(resultado["linea"])
            if total:
                logger.info(
                    f"WMS Fields | {modelo}: {len(resultado['cabecera'])} cabecera, "
                    f"{len(resultado['linea'])} linea"
                )
    except Exception as e:
        if logger:
            logger.warning(f"WMS Fields | No se pudo cargar mappings para {modelo}: {e}")
    return resultado


def convertir_valor(valor, tipo_valor):
    """Convierte un valor al tipo indicado."""
    if valor is None:
        return None
    try:
        if tipo_valor == "entero":
            return int(float(valor))
        if tipo_valor == "decimal":
            return float(valor)
        if tipo_valor == "booleano":
            return str(valor).lower() in ("true", "1", "si", "yes")
        return str(valor)
    except (ValueError, TypeError):
        return str(valor)


def aplicar_wms_fields(payload, fila, mappings_ubicacion, logger=None):
    """Agrega campos del catálogo WMS al payload.

    Args:
        payload: dict del payload (cabecera o línea) que se va a enviar a Odoo
        fila: dict de la fila del transform (tiene los campos origen)
        mappings_ubicacion: lista de mappings de una ubicación ('cabecera' o 'linea')
    """
    for m in mappings_ubicacion:
        valor = fila.get(m["campo_origen"])
        if valor is not None and str(valor).strip() != "":
            payload[m["campo_destino"]] = convertir_valor(valor, m["tipo_valor"])
        elif m["valor_default"] is not None:
            payload[m["campo_destino"]] = convertir_valor(m["valor_default"], m["tipo_valor"])
