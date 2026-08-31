"""
Catálogo declarativo de funciones de determinación.
Usadas por TransformConnekta/TransformSAP._apply_conditionals() en modo función.
Cada función recibe (row, params, logger) y retorna el valor calculado.
El catálogo incluye metadata (label, descripcion, params) que el endpoint
GET /catalog/determination-functions expone al frontend.
Fase: 3 — Transform Layer
"""
import re


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


# ============================================================
# CATÁLOGO DECLARATIVO
# ============================================================

CATALOG = {
    "route_compra_manufactura_prefijo": {
        "fn": route_compra_manufactura_prefijo,
        "label": "Ruta compra/manufactura por prefijo",
        "descripcion": "Determina la ruta logística del producto en Odoo (Buy, Fabricación o ambas). Evalúa los indicadores de compra y manufactura del ERP y verifica si la referencia comienza con un prefijo específico para forzar manufactura.",
        "params": [
            {"name": "campo_compra", "required": True, "descripcion": "Campo del ERP que indica si el producto se compra. Acepta 'True', 'SI' o '1'."},
            {"name": "campo_manufactura", "required": True, "descripcion": "Campo del ERP que indica si el producto se manufactura."},
            {"name": "campo_referencia", "required": True, "descripcion": "Campo con la referencia del producto. Se verifica si empieza con el prefijo."},
            {"name": "prefijo_manufactura", "required": True, "descripcion": "Prefijo que fuerza manufactura. Ej: 'PT' hace que 'PT001' sea manufactura."},
        ],
    },
    "extraer_prefijo": {
        "fn": extraer_prefijo,
        "label": "Extraer prefijo alfabético",
        "descripcion": "Extrae las letras iniciales consecutivas de un campo. Ejemplo: 'PT001' → 'PT', 'MP1234' → 'MP', '12345' → ''.",
        "params": [
            {"name": "campo_origen", "required": True, "descripcion": "Campo del cual se extraen las letras iniciales."},
        ],
    },
    "concatenar_campos": {
        "fn": concatenar_campos,
        "label": "Concatenar campos",
        "descripcion": "Une el valor de varios campos en un solo texto con un separador. Campos vacíos se omiten. Ejemplo: CO, TipoDocto, ConsecDocto con '-' → '001-TEM-123'.",
        "params": [
            {"name": "campos", "required": True, "descripcion": "Lista de nombres de campos a unir, separados por coma."},
            {"name": "separador", "required": False, "descripcion": "Carácter entre cada valor. Por defecto vacío."},
        ],
    },
    "valor_por_campo": {
        "fn": valor_por_campo,
        "label": "Valor según campo",
        "descripcion": "Compara el valor de un campo con un valor esperado. Si coincide asigna un texto, si no coincide asigna otro.",
        "params": [
            {"name": "campo_origen", "required": True, "descripcion": "Campo cuyo valor se compara."},
            {"name": "valor", "required": True, "descripcion": "Valor exacto contra el que se compara. Sensible a mayúsculas."},
            {"name": "si", "required": True, "descripcion": "Texto que se asigna cuando coincide."},
            {"name": "no", "required": True, "descripcion": "Texto que se asigna cuando NO coincide."},
        ],
    },
    "valor_por_lista": {
        "fn": valor_por_lista,
        "label": "Valor según lista",
        "descripcion": "Verifica si el valor de un campo está en una lista. Si está asigna un texto, si no asigna otro. Funciona con números y texto.",
        "params": [
            {"name": "campo_origen", "required": True, "descripcion": "Campo cuyo valor se busca en la lista."},
            {"name": "lista", "required": True, "descripcion": "Valores permitidos separados por coma. Ej: '307,313,315' o 'A,B,C'."},
            {"name": "si", "required": True, "descripcion": "Texto cuando el valor SÍ está en la lista."},
            {"name": "no", "required": True, "descripcion": "Texto cuando el valor NO está en la lista."},
        ],
    },
    "doc_name_por_rango": {
        "fn": doc_name_por_rango,
        "label": "Nombre de documento por rango",
        "descripcion": "Arma el nombre del documento combinando un prefijo con el número. El prefijo se elige según el rango numérico. Ejemplo: DocNum 3565, rango 1-10000000 con prefijo 'OCNAL' → 'OCNAL-3565'.",
        "params": [
            {"name": "campo_origen", "required": True, "descripcion": "Campo con el número del documento. Debe ser numérico."},
            {"name": "rangos", "required": True, "descripcion": "Rangos con prefijos en formato 'inicio-fin:prefijo', separados por coma. Ej: '1-10000000:OCNAL,10000001-20000000:OCIMP'."},
            {"name": "separador", "required": False, "descripcion": "Carácter entre prefijo y número. Por defecto '-'."},
        ],
    },
    "sap_field_combined": {
        "fn": sap_field_combined,
        "label": "Combinación de campos SAP",
        "descripcion": "Evalúa dos campos contra un valor esperado. Si ambos coinciden asigna un texto, si no asigna otro. Ejemplo: U_FB_EnviarWMS y U_FB_EnviarProdWMS ambos 'Y' → 'Producto Terminado, Producción'.",
        "params": [
            {"name": "campo1", "required": True, "descripcion": "Primer campo a evaluar."},
            {"name": "campo2", "required": True, "descripcion": "Segundo campo a evaluar."},
            {"name": "valor_esperado", "required": True, "descripcion": "Valor que ambos campos deben tener."},
            {"name": "texto_ambos", "required": True, "descripcion": "Texto cuando ambos coinciden."},
            {"name": "texto_solo_uno", "required": True, "descripcion": "Texto cuando solo uno o ninguno coincide."},
        ],
    },
}


def get_determination_function(name: str, logger=None):
    entry = CATALOG.get(name)
    if entry is None:
        if logger:
            logger.error(
                f"get_determination_function: función '{name}' no existe en el catálogo. "
                f"Funciones disponibles: {list(CATALOG.keys())}"
            )
        return None
    return entry["fn"]