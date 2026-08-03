"""
pruebasF3.py — Pruebas de integración Fase 3 (Transform Layer)
Ejecutar en wms-servertest con ENV=staging
Prueba: items para los 3 ERPs con flow_configs simulados del front
Simula el flujo real: BD → main.py extrae flow_name/flow_type → transform
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

    # Alias canónicos obligatorios
    obligatorios = ["referencia", "descripcion"]
    print(f"\n  Campos obligatorios:")
    for campo in obligatorios:
        estado = "OK" if campo in ejemplo and ejemplo[campo] else "FALTA"
        print(f"    [{estado}] {campo}: {ejemplo.get(campo, '???')!r}")

    # Tipos float
    campos_float = ["peso", "volumen", "costo", "precio", "iva"]
    print(f"\n  Campos float:")
    for campo in campos_float:
        if campo in ejemplo:
            tipo_ok = isinstance(ejemplo[campo], float)
            estado = "OK" if tipo_ok else "ERROR"
            print(f"    [{estado}] {campo}: {ejemplo[campo]!r} ({type(ejemplo[campo]).__name__})")

    # Tipos int
    campos_int = ["vence", "use_expiration_date", "expiration_time",
                "ind_compra", "ind_venta", "ind_manufactura"]
    print(f"\n  Campos int:")
    for campo in campos_int:
        if campo in ejemplo:
            tipo_ok = isinstance(ejemplo[campo], int)
            estado = "OK" if tipo_ok else "ERROR"
            print(f"    [{estado}] {campo}: {ejemplo[campo]!r} ({type(ejemplo[campo]).__name__})")

    # Muestra de 3 registros
    print(f"\n  Muestra (3 registros):")
    for i, row in enumerate(resultado[:3]):
        ref = row.get("referencia", "?")
        desc = str(row.get("descripcion", "?"))[:40]
        cat = row.get("categoria", "?")
        tracking = row.get("tracking", "?")
        print(f"    [{i+1}] {ref} | {desc} | cat={cat} | tracking={tracking}")


def ejecutar_flow(transform, connector, json_bd, erp_name, mostrar_crudo=False, fn_crudo=None):
    """
    Simula el flujo real de main.py:
    1. Extrae flow_name y flow_type del JSON de BD
    2. El resto es flow_config para transform
    3. Llama transform.get_flow(connector, flow_name, flow_config)
    """
    # main.py extraería estos del JSON
    flow_name = json_bd.pop("flow_name")
    flow_type = json_bd.pop("flow_type")
    flow_config = json_bd  # lo que queda es el flow_config

    print(f"  flow_name: {flow_name}")
    print(f"  flow_type: {flow_type}")

    # Opcionalmente mostrar datos crudos de la API
    if mostrar_crudo and fn_crudo:
        fn_crudo(connector, flow_config)

    # Transform — como lo llamaría main.py
    print(f"\n  Ejecutando transform.get_flow(connector, '{flow_name}', flow_config)...")
    resultado = transform.get_flow(connector, flow_name, flow_config)

    # Validar resultado
    validar_items(resultado, erp_name)

    # En main.py seguiría: _dispatch_flow(resultado, flow_type, odoo, token, config)
    print(f"\n  [Siguiente paso] _dispatch_flow(data, '{flow_type}', odoo, token, config)")

    return True


# ============================================================
#  1. SIESA WS — Fénix — Items
# ============================================================

def test_ws_items():
    separador("1. SIESA WS — Fénix — Items")
    try:
        loader = ConfigLoader()
        config = loader.load_credentials("fenix")
        connector = SiesaEnterprise(config)
        transform = TransformWS(config)

        # JSON tal cual vendría de BD
        json_bd = {
            "flow_name": "items",
            "flow_type": "items",
            "sql": """
                SET QUOTED_IDENTIFIER OFF;
                SELECT TOP 50
                    ISNULL(f120_id, '') AS referencia,
                    REPLACE(ISNULL(f120_descripcion, 'SIN DESCRIPCION'), CHAR(39), '') AS descripcion,
                    ISNULL((SELECT TOP 1 b.f131_id
                            FROM t131_mc_items_barras b
                            WHERE b.f131_rowid_item_ext = f121_rowid
                            ORDER BY b.f131_ts DESC), '') AS codigo_barras,
                    ISNULL(STUFF((SELECT ', ' + b2.f131_id
                            FROM t131_mc_items_barras b2
                            WHERE b2.f131_rowid_item_ext = f121_rowid
                            AND b2.f131_id NOT IN (
                                SELECT TOP 1 b3.f131_id
                                FROM t131_mc_items_barras b3
                                WHERE b3.f131_rowid_item_ext = f121_rowid
                                ORDER BY b3.f131_ts DESC)
                            FOR XML PATH('')), 1, 2, ''), '') AS codigos_extras,
                    '0' AS costo,
                    ISNULL(TRIM(f120_id_unidad_inventario), 'UNID') AS unidad,
                    ISNULL(CAST(f122_peso AS VARCHAR(12)), '0') AS peso,
                    CAST(ISNULL(f122_volumen, '0') AS VARCHAR(10)) AS volumen,
                    0 AS iva,
                    0 AS precio,
                    ISNULL(TRIM(t_linea_desc.f106_descripcion), '') AS categoria,
                    ISNULL(TRIM(t_marca_desc.f106_descripcion), '') AS marca,
                    'lot' AS tracking,
                    1 AS use_expiration_date,
                    ISNULL(f120_vida_util, 0) AS vence
                FROM t120_mc_items
                LEFT JOIN t121_mc_items_extensiones
                    ON (f121_rowid_item = f120_rowid AND f121_id_cia = f120_id_cia)
                LEFT JOIN t122_mc_items_unidades
                    ON (f120_rowid = f122_rowid_item AND f122_id_unidad = f120_id_unidad_inventario)
                LEFT JOIN t125_mc_items_criterios AS t_linea
                    ON (f120_rowid = t_linea.f125_rowid_item AND t_linea.f125_id_plan = '003')
                LEFT JOIN t106_mc_criterios_item_mayores AS t_linea_desc
                    ON (t_linea.f125_id_criterio_mayor = t_linea_desc.f106_id
                        AND t_linea.f125_id_plan = t_linea_desc.f106_id_plan
                        AND t_linea.f125_id_cia = t_linea_desc.f106_id_cia)
                LEFT JOIN t125_mc_items_criterios AS t_marca
                    ON (f120_rowid = t_marca.f125_rowid_item AND t_marca.f125_id_plan = '005')
                LEFT JOIN t106_mc_criterios_item_mayores AS t_marca_desc
                    ON (t_marca.f125_id_criterio_mayor = t_marca_desc.f106_id
                        AND t_marca.f125_id_plan = t_marca_desc.f106_id_plan
                        AND t_marca.f125_id_cia = t_marca_desc.f106_id_cia)
                WHERE f120_id_cia = 7
                ORDER BY f120_id ASC;
                SET QUOTED_IDENTIFIER ON;
            """
        }

        return ejecutar_flow(transform, connector, json_bd, "WS/Fenix")

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
        loader = ConfigLoader()
        config = loader.load_credentials("oit")
        connector = SiesaConnekta(config)
        transform = TransformConnekta(config)

        # JSON tal cual vendría de BD
        json_bd = {
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

        def mostrar_crudo(connector, flow_config):
            print("  Probando conexión cruda para ver campos de la API...")
            status, raw = connector.get(
                endpoint=flow_config["query_desc"],
                params={
                    "query_desc": flow_config["query_desc"],
                    "no_paginar": False,
                    "single_page": True
                }
            )
            if status and raw:
                print(f"  API retornó {len(raw)} registros")
                print(f"  Campos de la API: {list(raw[0].keys())}")
                print(f"  Ejemplo crudo: {raw[0]}")
            else:
                print(f"  [!] API no retornó datos: {raw}")

        return ejecutar_flow(transform, connector, json_bd, "Connekta/OIT",
                            mostrar_crudo=True, fn_crudo=mostrar_crudo)

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
        loader = ConfigLoader()
        config = loader.load_credentials("fabercastell")
        connector = SAP(config)
        transform = TransformSAP(config)

        # JSON tal cual vendría de BD
        json_bd = {
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

        def mostrar_crudo(connector, flow_config):
            print("  Probando login SAP...")
            if not connector.session_id:
                if not connector.login_api():
                    print("  [FALLO] No se pudo autenticar en SAP")
                    return
            print("  Login OK")
            print("  Obteniendo registros crudos para ver campos...")
            status, raw = connector.get(
                endpoint="Items",
                params={"filter": flow_config["filter"]}
            )
            if status and raw:
                print(f"  API retornó {len(raw)} registros")
                print(f"  Campos de la API: {list(raw[0].keys())}")
            else:
                print(f"  [!] API no retornó datos: {raw}")

        return ejecutar_flow(transform, connector, json_bd, "SAP/FaberCastell",
                            mostrar_crudo=True, fn_crudo=mostrar_crudo)

    except Exception as e:
        print(f"  [FALLO] SAP Items: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================
#  MAIN
# ============================================================

if __name__ == "__main__":
    print("\n" + "="*80)
    print("  PRUEBAS FASE 3 — Transform Layer — Items")
    print("  ENV: staging | Logs: /var/log/integrador/")
    print("="*80)

    resultados = {}

    resultados["WS/Fenix"] = test_ws_items()
    resultados["Connekta/OIT"] = test_connekta_items()
    resultados["SAP/FaberCastell"] = test_sap_items()

    separador("RESUMEN")
    for erp, ok in resultados.items():
        estado = "PASO" if ok else "FALLO"
        print(f"  {erp}: {estado}")

    print(f"\n  Logs en: /var/log/integrador/")
    print(f"  Buscar: _normalize_items, fallidos, validate_record\n")