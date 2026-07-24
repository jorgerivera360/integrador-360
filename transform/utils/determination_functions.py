"""
Catálogo cerrado de funciones de determinación.
Usadas por TransformConnekta._apply_conditionals() en modo B (función).
Cada función recibe (row, params, logger) y retorna el valor calculado.
Fase: 3 — Transform Layer
"""
import re


def get_determination_function(name: str, logger=None):

    catalog = {
        "route_compra_manufactura_prefijo": route_compra_manufactura_prefijo,
        "extraer_prefijo": extraer_prefijo,
        "concatenar_campos": concatenar_campos,
    }
    fn = catalog.get(name)
    if fn is None and logger:
        logger.error(
            f"get_determination_function: función '{name}' no existe en el catálogo. "
            f"Funciones disponibles: {list(catalog.keys())}"
        )
    return fn


def route_compra_manufactura_prefijo(row: dict, params: dict, logger=None):

    campo_compra = params.get("campo_compra", "")
    campo_manufactura = params.get("campo_manufactura", "")
    campo_referencia = params.get("campo_referencia", "")
    prefijo = params.get("prefijo_manufactura", "")

    compra = str(row.get(campo_compra, "")).strip() == "True"
    manufactura = str(row.get(campo_manufactura, "")).strip() == "True"
    referencia = str(row.get(campo_referencia, "")).strip()

    if prefijo and referencia.startswith(prefijo):
        manufactura = True

    if compra and manufactura:
        return "Buy,Fabricación"
    elif manufactura:
        return "Fabricación"
    elif compra:
        return "Buy"

    if logger:
        logger.info(
            f"route_compra_manufactura_prefijo: sin ruta para referencia '{referencia}' "
            f"(compra={compra}, manufactura={manufactura})"
        )
    return ""


def extraer_prefijo(row: dict, params: dict, logger=None):

    campo = params.get("campo_origen", "")
    valor = str(row.get(campo, "")).strip()

    if not valor:
        if logger:
            logger.warning(
                f"extraer_prefijo: campo '{campo}' vacío o ausente en el registro"
            )
        return ""

    match = re.match(r"^([A-Za-z]+)", valor)
    if not match and logger:
        logger.warning(
            f"extraer_prefijo: no se encontró prefijo alfabético en '{valor}'"
        )
    return match.group(1) if match else ""


def concatenar_campos(row: dict, params: dict, logger=None):

    campos = params.get("campos", [])
    separador = params.get("separador", "")

    if not campos:
        if logger:
            logger.warning("concatenar_campos: lista de campos vacía")
        return ""

    valores = [str(row.get(campo, "")).strip() for campo in campos]
    return separador.join(valores)