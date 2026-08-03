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
        "valor_por_campo": valor_por_campo,
        "valor_por_lista": valor_por_lista,
        "doc_name_por_rango": doc_name_por_rango,
        "sap_field_combined": sap_field_combined,
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

    compra = str(row.get(campo_compra, "")).strip().lower() in ("true", "si", "1")
    manufactura = str(row.get(campo_manufactura, "")).strip().lower() in ("true", "si", "1")
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
    return separador.join(v for v in valores if v)

def valor_por_campo(row: dict, params: dict, logger=None):

    campo = params.get("campo_origen", "")
    valor_esperado = params.get("valor", "")
    texto_si = params.get("si", "")
    texto_no = params.get("no", "")

    valor_actual = str(row.get(campo, "")).strip()

    return texto_si if valor_actual == valor_esperado else texto_no

def valor_por_lista(row: dict, params: dict, logger=None):

    campo = params.get("campo_origen", "")
    lista = params.get("lista", [])
    texto_si = params.get("si", "")
    texto_no = params.get("no", "")

    valor_actual = row.get(campo)

    # Comparar con el tipo original (int para ItemsGroupCode, str para otros)
    if valor_actual in lista:
        return texto_si

    # Fallback: comparar como string por si el tipo no matchea
    if str(valor_actual).strip() in [str(v) for v in lista]:
        return texto_si

    return texto_no

def doc_name_por_rango(row: dict, params: dict, logger=None):

    campo = params.get("campo_origen", "")
    rangos = params.get("rangos", {})
    separador = params.get("separador", "-")

    valor = row.get(campo)
    try:
        numero = int(valor)
    except (TypeError, ValueError):
        if logger:
            logger.warning(
                f"doc_name_por_rango: campo '{campo}' no es numérico: '{valor}'"
            )
        return ""

    for rango_key, prefijo in rangos.items():
        partes = str(rango_key).split("-")
        if len(partes) == 2:
            try:
                inicio = int(partes[0])
                fin = int(partes[1])
                if inicio <= numero <= fin:
                    return f"{prefijo}{separador}{numero}"
            except ValueError:
                continue

    if logger:
        logger.warning(
            f"doc_name_por_rango: DocNum {numero} no cae en ningún rango configurado"
        )
    return ""

def sap_field_combined(row: dict, params: dict, logger=None):

    campo1 = params.get("campo1", "")
    campo2 = params.get("campo2", "")
    valor_esperado = params.get("valor_esperado", "")
    texto_ambos = params.get("texto_ambos", "")
    texto_solo_uno = params.get("texto_solo_uno", "")

    val1 = str(row.get(campo1, "")).strip()
    val2 = str(row.get(campo2, "")).strip()

    if val1 == valor_esperado and val2 == valor_esperado:
        return texto_ambos
    return texto_solo_uno