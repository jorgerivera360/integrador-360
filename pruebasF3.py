"""
pruebasF3.py — Pruebas de integración Fase 3 (Transform Layer)
Ejecutar en wms-servertest con ENV=staging
Prueba: items para los 3 ERPs con flow_configs simulados del front
Simula el flujo real: Front envia JSON → main.py extrae client_id,
carga credenciales, inyecta client_id, extrae flow_name/flow_type → transform
"""
import os
os.environ["ENV"] = "staging"

from config.loader import ConfigLoader
from connection.siesa_enterprise import SiesaEnterprise
from connection.siesa_connekta import SiesaConnekta
from connection.sap import SAP
from transform.transform_ws import TransformWS
from transform.transform_connekta import TransformConnekta
from transform.transform_sap import TransformSAP


def separador(titulo):
    print(f"\n{'='*80}")
    print(f"  {titulo}")
    print(f"{'='*80}\n")


def validar_items(resultado, erp_name):
    if not resultado:
        print(f"  [!] {erp_name}: sin resultados")
        return

    print(f"  [{erp_name}] {len(resultado)} registros procesados")

    ejemplo = resultado[0]
    print(f"\n  Primer registro completo:")
    for k, v in ejemplo.items():
        print(f"    {k}: {v!r} ({type(v).__name__})")

    obligatorios = ["referencia", "descripcion"]
    print(f"\n  Campos obligatorios:")
    for campo in obligatorios:
        estado = "OK" if campo in ejemplo and ejemplo[campo] else "FALTA"
        print(f"    [{estado}] {campo}: {ejemplo.get(campo, '???')!r}")

    campos_float = ["peso", "volumen", "costo", "precio", "iva"]
    print(f"\n  Campos float:")
    for campo in campos_float:
        if campo in ejemplo:
            tipo_ok = isinstance(ejemplo[campo], float)
            estado = "OK" if tipo_ok else "ERROR"
            print(f"    [{estado}] {campo}: {ejemplo[campo]!r} ({type(ejemplo[campo]).__name__})")

    campos_int = ["vence", "use_expiration_date", "expiration_time",
                "ind_compra", "ind_venta", "ind_manufactura"]
    print(f"\n  Campos int:")
    for campo in campos_int:
        if campo in ejemplo:
            tipo_ok = isinstance(ejemplo[campo], int)
            estado = "OK" if tipo_ok else "ERROR"
            print(f"    [{estado}] {campo}: {ejemplo[campo]!r} ({type(ejemplo[campo]).__name__})")

    print(f"\n  Muestra (3 registros):")
    for i, row in enumerate(resultado[:3]):
        ref = row.get("referencia", "?")
        desc = str(row.get("descripcion", "?"))[:40]
        cat = row.get("categoria", "?")
        tracking = row.get("tracking", "?")
        print(f"    [{i+1}] {ref} | {desc} | cat={cat} | tracking={tracking}")


def ejecutar_flow(json_front, erp_name, mostrar_crudo=False):
    """
    Simula el flujo real de main.py:
    1. Front envia JSON con client_id + flow_name + flow_type + config del flow
    2. main.py extrae client_id → carga credenciales → inyecta client_id
    3. Instancia connector y transform segun erp.tipo
    4. Extrae flow_name y flow_type del JSON
    5. Llama transform.get_flow(connector, flow_name, flow_config)
    6. Pasaria flow_type a _dispatch_flow() (no implementado aun)
    """

    # --- Paso 1: main.py extrae client_id del JSON del front ---
    client_id = json_front.pop("client_id")
    flow_name = json_front.pop("flow_name")
    flow_type = json_front.pop("flow_type")
    flow_config = json_front  # lo que queda

    print(f"  client_id: {client_id}")
    print(f"  flow_name: {flow_name}")
    print(f"  flow_type: {flow_type}")

    # --- Paso 2: cargar credenciales y armar config ---
    config = ConfigLoader(client_id).load_config()
    config["client_id"] = client_id

    erp_tipo = config["erp"]["tipo"]
    print(f"  erp.tipo: {erp_tipo}")

    # --- Paso 3: instanciar connector y transform (build_connector / build_transform) ---
    if erp_tipo == "ws":
        connector = SiesaEnterprise(config)
        transform = TransformWS(config)
    elif erp_tipo == "connekta":
        connector = SiesaConnekta(config)
        transform = TransformConnekta(config)
    elif erp_tipo == "sap":
        connector = SAP(config)
        transform = TransformSAP(config)
    else:
        print(f"  [FALLO] ERP tipo '{erp_tipo}' no soportado")
        return False

    # --- Opcional: mostrar datos crudos de la API ---
    if mostrar_crudo and erp_tipo == "connekta":
        print("\n  Datos crudos de la API (1 pagina)...")
        status, raw = connector.get(
            endpoint=flow_config["query_desc"],
            params={
                "query_desc": flow_config["query_desc"],
                "no_paginar": False,
                "single_page": True
            }
        )
        if status and raw:
            print(f"  API retorno {len(raw)} registros")
            print(f"  Campos de la API: {list(raw[0].keys())}")
            print(f"  Ejemplo crudo: {raw[0]}")
        else:
            print(f"  [!] API no retorno datos: {raw}")

    elif mostrar_crudo and erp_tipo == "sap":
        print("\n  Login SAP...")
        if not connector.login_api():
            print("  [FALLO] No se pudo autenticar en SAP")
            return False
        print("  Login OK — obteniendo campos crudos...")
        status, raw = connector.get(
            endpoint=flow_config["endpoint"],
            params={"filter": flow_config.get("filter", "")}
        )
        if status and raw:
            print(f"  API retorno {len(raw)} registros")
            print(f"  Campos de la API: {list(raw[0].keys())}")
        else:
            print(f"  [!] API no retorno datos: {raw}")

    # --- Paso 4: transform ---
    print(f"\n  Ejecutando transform.get_flow(connector, '{flow_name}', flow_config)...")
    resultado = transform.get_flow(connector, flow_name, flow_config)

    validar_items(resultado, erp_name)

    print(f"\n  [Siguiente paso] _dispatch_flow(data, '{flow_type}', odoo, token, config)")

    return True


# ============================================================
#  1. SIESA WS — Fénix — Items
# ============================================================

def test_ws_items():
    separador("1. SIESA WS — Fenix — Items")
    try:
        json_front = {
            "client_id": "fenix",
            "flow_name": "items",
            "flow_type": "items",
            "sql": """
                SET QUOTED_IDENTIFIER OFF;
                SELECT TOP 50
                    ISNULL(f120_id, "") AS referencia,
                    ISNULL(f120_descripcion, "") AS descripcion,
                    ISNULL((SELECT TOP 1 b.f131_id FROM t131_mc_items_barras b WHERE b.f131_rowid_item_ext = f121_rowid ORDER BY b.f131_ts DESC), "") AS codigo_barras,
                    ISNULL(STUFF((SELECT ", " + b2.f131_id FROM t131_mc_items_barras b2 WHERE b2.f131_rowid_item_ext = f121_rowid AND b2.f131_id NOT IN (SELECT TOP 1 b3.f131_id FROM t131_mc_items_barras b3 WHERE
                b3.f131_rowid_item_ext = f121_rowid ORDER BY b3.f131_ts DESC) FOR XML PATH("")), 1, 2, ""), "") AS codigos_extras,
                    "0" AS costo,
                    ISNULL(TRIM(f120_id_unidad_inventario), "UNID") AS unidad,
                    ISNULL(CAST(f122_peso AS VARCHAR(12)), "0") AS peso,
                    CAST(ISNULL(f122_volumen, "0") AS VARCHAR(10)) AS volumen,
                    0 AS iva,
                    0 AS precio,
                    ISNULL(TRIM(t_linea_desc.f106_descripcion), "") AS categoria,
                    ISNULL(TRIM(t_marca_desc.f106_descripcion), "") AS marca,
                    CASE f120_ind_lote WHEN 1 THEN "lot" WHEN 2 THEN "lot" ELSE "none" END AS tracking,
                    1 AS use_expiration_date,
                    ISNULL(f120_vida_util, 0) AS vence
                FROM t120_mc_items
                LEFT JOIN t121_mc_items_extensiones
                    ON (f121_rowid_item = f120_rowid AND f121_id_cia = f120_id_cia)
                LEFT JOIN t122_mc_items_unidades
                    ON (f120_rowid = f122_rowid_item AND f122_id_unidad = f120_id_unidad_inventario)
                LEFT JOIN t125_mc_items_criterios AS t_linea ON (f120_rowid = t_linea.f125_rowid_item AND t_linea.f125_id_plan = "003")
                LEFT JOIN t106_mc_criterios_item_mayores AS t_linea_desc ON (t_linea.f125_id_criterio_mayor = t_linea_desc.f106_id AND t_linea.f125_id_plan = t_linea_desc.f106_id_plan AND t_linea.f125_id_cia =
                t_linea_desc.f106_id_cia)
                LEFT JOIN t125_mc_items_criterios AS t_marca ON (f120_rowid = t_marca.f125_rowid_item AND t_marca.f125_id_plan = "005")
                LEFT JOIN t106_mc_criterios_item_mayores AS t_marca_desc ON (t_marca.f125_id_criterio_mayor = t_marca_desc.f106_id AND t_marca.f125_id_plan = t_marca_desc.f106_id_plan AND t_marca.f125_id_cia =
                t_marca_desc.f106_id_cia)
                WHERE f120_id_cia = 7
                ORDER BY f120_id ASC;
                SET QUOTED_IDENTIFIER ON;
            """
        }

        return ejecutar_flow(json_front, "WS/Fenix")

    except Exception as e:
        print(f"  [FALLO] WS Items: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================
#  2. SIESA Connekta — OIT — Items
# ============================================================

def test_connekta_items():
    separador("2. SIESA Connekta — OIT — Items")
    try:
        json_front = {
            "client_id": "oit",
            "flow_name": "items",
            "flow_type": "items",
            "query_desc": "productosysolucionesquimicas_items_wms",
            "parametros": "",
            "paginacion": True,
            "mapping": {
                "referencia": "referencia",
                "descripcion": "descripcion",
                "codigo_barras": "codigo_barras",
                "categoria": "categoria",
                "linea": "marca",
                "costo": "costo",
                "precio": "precio",
                "unidad": "unidad",
                "peso": "peso",
                "volumen": "volumen",
                "lote": "tracking",
                "vence": "vence"
            },
            "hardcodes": {
                "impuesto": 19.0,
                "codigos_extras": "",
                "use_expiration_date": 0
            },
            "conditionals": [
                {
                    "tipo": "reglas",
                    "campo_origen": "tracking",
                    "campo_destino": "tracking",
                    "reglas": [
                        {"si": "SI", "entonces": "lot"},
                        {"si": "Si", "entonces": "lot"},
                        {"si": "1", "entonces": "lot"}
                    ],
                    "default": "none"
                }
            ]
        }

        return ejecutar_flow(json_front, "Connekta/OIT", mostrar_crudo=True)

    except Exception as e:
        print(f"  [FALLO] Connekta Items: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================
#  3. SAP B1 — Faber Castell — Items
# ============================================================

def test_sap_items():
    separador("3. SAP B1 — Faber Castell — Items")
    try:
        json_front = {
            "client_id": "fabercastell",
            "flow_name": "items",
            "flow_type": "items",
            "endpoint": "Items",
            "filter": "U_FB_EnviarWMS eq 'Y' and ItemType eq 'itItems'",
            "mapping": {
                "ItemCode": "referencia",
                "ItemName": "descripcion",
                "BarCode": "codigo_barras",
                "U_FB_EANWMS": "codigos_extras",
                "ItemsGroupCode_resolved": "categoria",
                "ProdStdCost": "costo",
                "InventoryUOM": "unidad",
                "SalesUnitWeight": "peso",
                "SalesUnitVolume": "volumen"
            },
            "hardcodes": {
                "tracking": "lot",
                "vence": 0,
                "precio": 0,
                "impuesto": 0,
                "use_expiration_date": 0,
                "marca": ""
            },
            "conditionals": [
                {
                    "tipo": "funcion",
                    "campo_destino": "sap_field",
                    "funcion": "sap_field_combined",
                    "params": {
                        "campo1": "U_FB_EnviarWMS",
                        "campo2": "U_FB_EnviarProdWMS",
                        "valor_esperado": "Y",
                        "texto_ambos": "Producto Terminado, Produccion",
                        "texto_solo_uno": "Producto Terminado"
                    }
                }
            ]
        }

        return ejecutar_flow(json_front, "SAP/FaberCastell", mostrar_crudo=True)

    except Exception as e:
        print(f"  [FALLO] SAP Items: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================
#  SIESA WS — Pruebas de error de configuración (B4-B7)
# ============================================================

def test_ws_errores_config():
    separador("WS — B4: SQL sin resultados")
    try:
        json_b4 = {
            "client_id": "fenix",
            "flow_name": "items",
            "flow_type": "items",
            "sql": "SELECT TOP 0 f120_id AS referencia, f120_descripcion AS descripcion FROM t120_mc_items WHERE f120_id_cia = 7"
        }
        result = ejecutar_flow(dict(json_b4), "WS/B4-SinResultados")
        print(f"  Resultado: {'OK - retorno vacio sin crash' if result else 'FALLO'}")
    except Exception as e:
        print(f"  [FALLO] B4: {e}")

    separador("WS — B5: SQL invalido")
    try:
        json_b5 = {
            "client_id": "fenix",
            "flow_name": "items",
            "flow_type": "items",
            "sql": "SELEC MAL QUERY INVALIDO"
        }
        result = ejecutar_flow(dict(json_b5), "WS/B5-SQLInvalido")
        print(f"  Resultado: {'OK - manejo error sin crash' if result else 'OK - retorno False sin crash'}")
    except Exception as e:
        print(f"  [FALLO] B5 crasheo: {e}")

    separador("WS — B6: flow_name no soportado")
    try:
        json_b6 = {
            "client_id": "fenix",
            "flow_name": "inventario",
            "flow_type": "items",
            "sql": "SELECT 1 AS referencia"
        }
        result = ejecutar_flow(dict(json_b6), "WS/B6-FlowNoSoportado")
        print(f"  Resultado: {'OK - manejo error sin crash' if result else 'OK - retorno False sin crash'}")
    except Exception as e:
        print(f"  [FALLO] B6 crasheo: {e}")

    separador("WS — B7: flow_config sin SQL")
    try:
        json_b7 = {
            "client_id": "fenix",
            "flow_name": "items",
            "flow_type": "items"
        }
        result = ejecutar_flow(dict(json_b7), "WS/B7-SinSQL")
        print(f"  Resultado: {'OK - manejo error sin crash' if result else 'OK - retorno False sin crash'}")
    except Exception as e:
        print(f"  [FALLO] B7 crasheo: {e}")

def test_ws_errores_datos():
    separador("WS — B1-B3: Registros con datos malos mezclados con buenos")
    try:
        json_front = {
            "client_id": "fenix",
            "flow_name": "items",
            "flow_type": "items",
            "sql": """
                SET QUOTED_IDENTIFIER OFF;
                SELECT TOP 3
                    f120_id AS referencia,
                    f120_descripcion AS descripcion,
                    0 AS costo,
                    ISNULL(TRIM(f120_id_unidad_inventario), "UNID") AS unidad,
                    CAST(ISNULL(f122_peso, 0) AS VARCHAR(12)) AS peso,
                    CAST(ISNULL(f122_volumen, 0) AS VARCHAR(10)) AS volumen,
                    0 AS iva,
                    0 AS precio,
                    ISNULL(f120_vida_util, 0) AS vence,
                    1 AS use_expiration_date
                FROM t120_mc_items
                LEFT JOIN t122_mc_items_unidades
                    ON (f120_rowid = f122_rowid_item AND f122_id_unidad = f120_id_unidad_inventario)
                WHERE f120_id_cia = 7

                UNION ALL

                SELECT NULL AS referencia, "Producto sin ref" AS descripcion,
                    0 AS costo, "UNID" AS unidad, "0" AS peso, "0" AS volumen,
                    0 AS iva, 0 AS precio, 0 AS vence, 1 AS use_expiration_date

                UNION ALL

                SELECT "REF-TEST" AS referencia, NULL AS descripcion,
                    0 AS costo, "UNID" AS unidad, "0" AS peso, "0" AS volumen,
                    0 AS iva, 0 AS precio, 0 AS vence, 1 AS use_expiration_date

                UNION ALL

                SELECT "REF-PESO-MAL" AS referencia, "Producto peso invalido" AS descripcion,
                    0 AS costo, "UNID" AS unidad, "abc" AS peso, "xyz" AS volumen,
                    0 AS iva, 0 AS precio, 0 AS vence, 1 AS use_expiration_date;

                SET QUOTED_IDENTIFIER ON;
            """
        }

        return ejecutar_flow(json_front, "WS/B1-B3-DatosMalos")

    except Exception as e:
        print(f"  [FALLO] B1-B3: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\n" + "="*80)
    print("  PRUEBAS FASE 3 — Transform Layer — WS Errores Datos")
    print("  ENV: staging | Logs: /var/log/integrador/")
    print("="*80)

    test_ws_errores_datos()

    print(f"\n  Revisa: /var/log/integrador/fenix.log")