"""
pruebasF4_ws.py — Pruebas de integracion Fase 4 Core Layer (SIESA WS)
Ejecutar en wms-servertest con ENV=staging
Secret GCP: integrador-pruebaws (ERP OrgComercia + Odoo pruebas)

Enfoque: Simula JSONs flow_config como vendrian del front.
Cada escenario ejecuta el flujo completo: connector -> transform -> core -> Odoo.

Uso:
  python pruebasF4_ws.py              -> corre todos los escenarios
  python pruebasF4_ws.py items        -> solo flow items
  python pruebasF4_ws.py clientes     -> solo flow clientes
  python pruebasF4_ws.py proveedores  -> solo flow proveedores
  python pruebasF4_ws.py compras      -> solo flow compras
  python pruebasF4_ws.py ventas       -> solo flow ventas
  python pruebasF4_ws.py resolve      -> solo resolve_missing_masters
  python pruebasF4_ws.py limpieza     -> solo limpieza
"""
import os
import sys
import traceback

os.environ["ENV"] = "staging"

from config.loader import ConfigLoader
from config.logger import IntegradorLogger
from connection.siesa_enterprise import SiesaEnterprise
from connection.jsonrpc import JsonRPC
from transform.transform_ws import TransformWS
from core.process_items import ProcessItems
from core.process_partners import ProcessPartners
from core.process_purchases import ProcessPurchases
from core.process_sales import ProcessSales
from core.resolve_missing_masters import resolve_missing_masters

# ============================================================
# CONFIGURACION
# ============================================================
CLIENT_ID = "pruebaws"
PREFIJO = "TEST-F4WS"

# Contadores
passed = 0
failed = 0
errors = []


def ok(test_id, msg):
    global passed
    passed += 1
    print(f"  [OK] {test_id}: {msg}")


def fail(test_id, msg):
    global failed
    failed += 1
    errors.append(f"{test_id}: {msg}")
    print(f"  [FAIL] {test_id}: {msg}")


def info(msg):
    print(f"  [INFO] {msg}")


def header(titulo):
    print(f"\n{'='*60}")
    print(f"  {titulo}")
    print(f"{'='*60}")


# ============================================================
# FLOW CONFIGS — Simulan lo que vendria del front/BD
# ============================================================
# NOTA: Los SQL usan id_cia=1 (OrgComercia). Si no retorna datos,
# ajustar el id_cia o los filtros segun el ERP del secret.
# Los alias son CANONICOS (como debe configurarlos el front).

SQL_ITEMS = (
    'SET QUOTED_IDENTIFIER OFF;'
    ' SELECT TOP 10'
    ' ISNULL(f120_id, "") AS referencia,'
    ' REPLACE(ISNULL(f120_descripcion, "SIN DESCRIPCION"), CHAR(39), "") AS descripcion,'
    ' ISNULL((SELECT TOP 1 b.f131_id FROM t131_mc_items_barras b'
    '         WHERE b.f131_rowid_item_ext = f121_rowid ORDER BY b.f131_ts DESC), "") AS codigo_barras,'
    ' ISNULL(TRIM(f120_id_unidad_inventario), "UNID") AS unidad,'
    ' ISNULL(CAST(f122_peso AS VARCHAR(12)), "0") AS peso,'
    ' CAST(ISNULL(f122_volumen, "0") AS VARCHAR(10)) AS volumen,'
    ' "0" AS costo,'
    ' 0 AS precio,'
    ' 0 AS iva,'
    ' CASE f120_ind_lote WHEN 1 THEN "lot" WHEN 2 THEN "lot" ELSE "none" END AS tracking,'
    ' ISNULL(f120_vida_util, 0) AS vence,'
    ' ISNULL(TRIM(t_cat.f106_descripcion), "") AS categoria'
    ' FROM t120_mc_items'
    ' LEFT JOIN t121_mc_items_extensiones'
    '     ON (f121_rowid_item = f120_rowid AND f121_id_cia = f120_id_cia)'
    ' LEFT JOIN t122_mc_items_unidades'
    '     ON (f120_rowid = f122_rowid_item AND f122_id_unidad = f120_id_unidad_inventario)'
    ' LEFT JOIN t125_mc_items_criterios AS t_cat_link'
    '     ON (f120_rowid = t_cat_link.f125_rowid_item AND t_cat_link.f125_id_plan = "001")'
    ' LEFT JOIN t106_mc_criterios_item_mayores AS t_cat'
    '     ON (t_cat_link.f125_id_criterio_mayor = t_cat.f106_id'
    '         AND t_cat_link.f125_id_plan = t_cat.f106_id_plan'
    '         AND t_cat_link.f125_id_cia = t_cat.f106_id_cia)'
    ' WHERE f120_id_cia = 1'
    ' ORDER BY f120_id ASC;'
    ' SET QUOTED_IDENTIFIER ON;'
)

FLOW_ITEMS = {
    "flow_name": "items",
    "flow_type": "items",
    "sql": SQL_ITEMS,
    "uom_mapping": {
        "UND": "Unidades",
        "und": "Unidades",
        "UNID": "Unidades",
        "KG": "kg",
        "kgs": "kg",
        "LT": "lt",
    },
}

FLOW_ITEMS_VACIO = {
    "flow_name": "items",
    "flow_type": "items",
    "sql": 'SELECT TOP 0 "x" AS referencia, "x" AS descripcion, "x" AS unidad',
}

FLOW_ITEMS_SQL_ERROR = {
    "flow_name": "items",
    "flow_type": "items",
    "sql": "SELEC MAL ESCRITO FROM tabla_inexistente",
}

SQL_CLIENTES = (
    'SET QUOTED_IDENTIFIER OFF;'
    ' SELECT DISTINCT TOP 5'
    ' TRIM(f200_nit) AS identificacion,'
    ' f201_id_sucursal AS sucursal,'
    ' CONCAT(f200_razon_social, " - ", f201_id_sucursal) AS nombre,'
    ' TRIM(f015_email) AS email,'
    ' TRIM(f015_telefono) AS telefono,'
    ' TRIM(f015_direccion1) AS direccion,'
    ' TRIM(f015_cod_postal) AS codigo_postal,'
    ' TRIM(f013_descripcion) AS ciudad,'
    ' TRIM(f012_descripcion) AS departamento,'
    ' TRIM(f011_descripcion) AS pais'
    ' FROM t201_mm_clientes'
    ' INNER JOIN t200_mm_terceros'
    '     ON (f200_rowid = f201_rowid_tercero AND f200_id_cia = f201_id_cia AND f200_ind_estado = 1)'
    ' INNER JOIN t015_mm_contactos'
    '     ON (f201_rowid_contacto = f015_rowid AND f201_id_cia = f015_id_cia)'
    ' INNER JOIN t011_mm_paises ON (f011_id = f015_id_pais)'
    ' INNER JOIN t012_mm_deptos ON (f012_id_pais = f015_id_pais AND f012_id = f015_id_depto)'
    ' INNER JOIN t013_mm_ciudades'
    '     ON (f013_id_pais = f015_id_pais AND f013_id_depto = f015_id_depto AND f013_id = f015_id_ciudad)'
    ' WHERE f201_id_cia = 1'
    ' ORDER BY 1 ASC;'
    ' SET QUOTED_IDENTIFIER ON;'
)

FLOW_CLIENTES = {
    "flow_name": "partners",
    "flow_type": "customer",
    "sql": SQL_CLIENTES,
    "sucursal_hierarchy": False,
    "country_id": 49,
    "identification_type_id": 5,
}

FLOW_CLIENTES_JERARQUIA = {
    **FLOW_CLIENTES,
    "sucursal_hierarchy": True,
    "sucursal_padre": "001",
}

SQL_PROVEEDORES = (
    'SET QUOTED_IDENTIFIER OFF;'
    ' SELECT TOP 5'
    ' TRIM(f200_nit) AS identificacion,'
    ' f202_id_sucursal AS sucursal,'
    ' CONCAT(f200_razon_social, " - ", f202_id_sucursal) AS nombre,'
    ' TRIM(f015_email) AS email,'
    ' TRIM(f015_telefono) AS telefono,'
    ' TRIM(f015_direccion1) AS direccion,'
    ' TRIM(f015_cod_postal) AS codigo_postal,'
    ' TRIM(f013_descripcion) AS ciudad,'
    ' TRIM(f012_descripcion) AS departamento,'
    ' TRIM(f011_descripcion) AS pais'
    ' FROM t202_mm_proveedores'
    ' INNER JOIN t200_mm_terceros'
    '     ON (f200_rowid = f202_rowid_tercero AND f200_id_cia = f202_id_cia AND f200_ind_estado = 1)'
    ' INNER JOIN t015_mm_contactos'
    '     ON (f202_rowid_contacto = f015_rowid AND f202_id_cia = f015_id_cia)'
    ' INNER JOIN t011_mm_paises ON (f011_id = f015_id_pais)'
    ' INNER JOIN t012_mm_deptos ON (f012_id_pais = f015_id_pais AND f012_id = f015_id_depto)'
    ' INNER JOIN t013_mm_ciudades'
    '     ON (f013_id_pais = f015_id_pais AND f013_id_depto = f015_id_depto AND f013_id = f015_id_ciudad)'
    ' WHERE f202_id_cia = 1'
    ' ORDER BY 1 ASC;'
    ' SET QUOTED_IDENTIFIER ON;'
)

FLOW_PROVEEDORES = {
    "flow_name": "partners",
    "flow_type": "supplier",
    "sql": SQL_PROVEEDORES,
    "country_id": 49,
    "identification_type_id": 5,
}

SQL_COMPRAS = (
    'SET QUOTED_IDENTIFIER OFF;'
    ' SELECT TOP 10'
    ' CONCAT(TRIM(f420_id_tipo_docto), f420_id_co, "-", f420_consec_docto) AS compra,'
    ' TRIM(tercero.f200_nit) AS proveedor,'
    ' TRIM(f202_id_sucursal) AS sucursal_proveedor,'
    ' "" AS referencia_compra,'
    ' CONVERT(VARCHAR, f420_fecha_ts_creacion, 23) AS fecha_entrega,'
    ' "draft" AS estado,'
    ' 1 AS almacen,'
    ' f120_id AS producto,'
    ' CAST(f421_precio_unitario AS DECIMAL(18, 2)) AS precio_unitario,'
    ' CAST(f421_cant_pedida AS INTEGER) AS cantidad,'
    ' ISNULL(CAST(f423_tasa AS DECIMAL(12,2)), 19) AS impuesto,'
    ' f150_id AS bodega_siesa'
    ' FROM t420_cm_oc_docto'
    ' INNER JOIN t202_mm_proveedores'
    '     ON (f420_rowid_tercero_facturar = f202_rowid_tercero'
    '         AND f420_id_sucursal_facturar = f202_id_sucursal'
    '         AND f420_id_cia = f202_id_cia)'
    ' INNER JOIN t200_mm_terceros AS tercero'
    '     ON (f420_rowid_tercero_facturar = tercero.f200_rowid'
    '         AND tercero.f200_rowid = f202_rowid_tercero'
    '         AND tercero.f200_id_cia = f202_id_cia)'
    ' INNER JOIN t421_cm_oc_movto'
    '     ON (f421_rowid_oc_docto = f420_rowid AND f421_id_cia = f420_id_cia)'
    ' INNER JOIN t121_mc_items_extensiones'
    '     ON (f121_rowid = f421_rowid_item_ext AND f121_id_cia = f421_id_cia)'
    ' INNER JOIN t120_mc_items'
    '     ON (f120_rowid = f121_rowid_item AND f120_id_cia = f121_id_cia)'
    ' INNER JOIN t150_mc_bodegas'
    '     ON (f421_rowid_bodega = f150_rowid)'
    ' LEFT JOIN t423_cm_oc_movto_imp'
    '     ON (f423_rowid_oc_movto = f421_rowid AND f423_id_cia = f421_id_cia'
    '         AND f423_id_llave_impuesto_desc IS NOT NULL)'
    ' WHERE f420_id_cia = 1'
    '     AND f420_ind_estado IN ("1", "2")'
    ' ORDER BY f420_consec_docto DESC;'
    ' SET QUOTED_IDENTIFIER ON;'
)

FLOW_COMPRAS = {
    "flow_name": "compras",
    "flow_type": "purchases",
    "sql": SQL_COMPRAS,
    "warehouse_mapping": {},
}

SQL_TRANSFERENCIA_ENTRADA = (
    'SET QUOTED_IDENTIFIER OFF;'
    ' SELECT TOP 10'
    ' CONCAT(TRIM(T350.f350_id_tipo_docto), TRIM(T350.f350_id_co), "-", T350.f350_consec_docto) AS compra,'
    ' "123456789" AS proveedor,'
    ' "001" AS sucursal_proveedor,'
    ' "" AS referencia_compra,'
    ' ISNULL(CONVERT(VARCHAR, t350.f350_fecha, 23), "") AS fecha_entrega,'
    ' "draft" AS estado,'
    ' 1 AS almacen,'
    ' T120.f120_id AS producto,'
    ' 0 AS precio_unitario,'
    ' T470.f470_cant_base AS cantidad,'
    ' 0 AS impuesto,'
    ' "" AS bodega_siesa'
    ' FROM t350_co_docto_contable T350'
    ' INNER JOIN t450_cm_docto_invent T450 ON T350.f350_rowid = T450.f450_rowid_docto'
    ' INNER JOIN t150_mc_bodegas T150E ON T150E.f150_rowid = T450.f450_rowid_bodega_entrada'
    ' INNER JOIN t470_cm_movto_invent T470 ON T470.f470_rowid_docto = T350.f350_rowid'
    ' INNER JOIN t121_mc_items_extensiones T121 ON T121.f121_rowid = T470.f470_rowid_item_ext'
    ' INNER JOIN t120_mc_items T120 ON T120.f120_rowid = T121.f121_rowid_item'
    ' WHERE t350.f350_id_tipo_docto = "TM"'
    '     AND T350.f350_id_cia = 1'
    '     AND T350.f350_fecha_ts_creacion > CONVERT(VARCHAR, DATEADD(day, -30, GETDATE()), 23)'
    ' ORDER BY T350.f350_fecha_ts_creacion DESC;'
    ' SET QUOTED_IDENTIFIER ON;'
)

FLOW_TRANSFERENCIA_ENTRADA = {
    "flow_name": "transferencia_entrada",
    "flow_type": "purchases",
    "sql": SQL_TRANSFERENCIA_ENTRADA,
    "warehouse_mapping": {},
}

SQL_DEVOLUCION_IN = (
    'SET QUOTED_IDENTIFIER OFF;'
    ' SELECT TOP 10'
    ' CONCAT(TRIM(T350.f350_id_tipo_docto), TRIM(T350.f350_id_co), "-", T350.f350_consec_docto) AS compra,'
    ' t200.f200_nit AS proveedor,'
    ' ISNULL((SELECT TOP 1 f202_id_sucursal FROM t202_mm_proveedores'
    '         WHERE f202_rowid_tercero = t200.f200_rowid ORDER BY f202_id_sucursal ASC), "001") AS sucursal_proveedor,'
    ' "" AS referencia_compra,'
    ' ISNULL(CONVERT(VARCHAR, t350.f350_fecha, 23), "") AS fecha_entrega,'
    ' "draft" AS estado,'
    ' 1 AS almacen,'
    ' RTRIM(t120.f120_id) AS producto,'
    ' 0 AS precio_unitario,'
    ' t470.f470_cant_1 AS cantidad,'
    ' 0 AS impuesto,'
    ' t150.f150_id AS bodega_siesa'
    ' FROM t350_co_docto_contable t350'
    ' INNER JOIN t470_cm_movto_invent t470 ON t470.f470_rowid_docto = t350.f350_rowid'
    ' INNER JOIN t121_mc_items_extensiones t121 ON t470.f470_rowid_item_ext = t121.f121_rowid'
    ' INNER JOIN t120_mc_items t120 ON t120.f120_rowid = t121.f121_rowid_item'
    ' INNER JOIN t150_mc_bodegas t150 ON t470.f470_rowid_bodega = t150.f150_rowid'
    ' INNER JOIN t200_mm_terceros t200 ON t200.f200_rowid = t350.f350_rowid_tercero'
    ' WHERE t350.f350_id_tipo_docto IN ("DEV")'
    '     AND T350.f350_id_cia = 1'
    '     AND T350.f350_fecha_ts_creacion > CONVERT(VARCHAR, DATEADD(day, -30, GETDATE()), 23)'
    ' ORDER BY T350.f350_fecha_ts_creacion DESC;'
    ' SET QUOTED_IDENTIFIER ON;'
)

FLOW_DEVOLUCION_IN = {
    "flow_name": "devolucion_in",
    "flow_type": "purchases",
    "sql": SQL_DEVOLUCION_IN,
    "warehouse_mapping": {},
}

SQL_VENTAS = (
    'SET QUOTED_IDENTIFIER OFF;'
    ' SELECT TOP 10'
    ' CONCAT(TRIM(t430.f430_id_co), TRIM(t430.f430_id_tipo_docto), t430.f430_consec_docto) AS pedido,'
    ' TRIM(t200.f200_nit) AS cliente,'
    ' TRIM(t201.f201_id_sucursal) AS sucursal_cliente,'
    ' ISNULL(CONVERT(VARCHAR, t430.f430_id_fecha, 23), "") AS fecha_pedido,'
    ' "draft" AS estado,'
    ' 1 AS almacen,'
    ' TRIM(RTRIM(v121.v121_id_item)) AS producto,'
    ' t431.f431_cant1_pedida AS cantidad_pedida,'
    ' t431.f431_precio_unitario_base AS precio_unitario,'
    ' "" AS impuesto,'
    ' "" AS zona,'
    ' "" AS vendedor,'
    ' "" AS condicion_pago,'
    ' TRIM(t430.f430_notas) AS observacion,'
    ' TRIM(t431.f431_id_unidad_medida) AS unidad_medida,'
    ' TRIM(t150.f150_id) AS bodega_siesa'
    ' FROM t201_mm_clientes t201'
    ' INNER JOIN t200_mm_terceros t200'
    '     ON t201.f201_rowid_tercero = t200.f200_rowid AND t201.f201_id_cia = t200.f200_id_cia'
    ' INNER JOIN t430_cm_pv_docto t430'
    '     ON t200.f200_id_cia = t430.f430_id_cia AND t200.f200_rowid = t430.f430_rowid_tercero_fact'
    '        AND t201.f201_id_sucursal = t430.f430_id_sucursal_fact'
    ' INNER JOIN t431_cm_pv_movto t431'
    '     ON t431.f431_rowid_pv_docto = t430.f430_rowid AND t430.f430_id_cia = t431.f431_id_cia'
    ' INNER JOIN t150_mc_bodegas t150'
    '     ON t150.f150_rowid = t431.f431_rowid_bodega'
    ' INNER JOIN v121'
    '     ON v121.v121_id_cia = t431.f431_id_cia AND t431.f431_rowid_item_ext = v121.v121_rowid_item_ext'
    ' WHERE t430.f430_id_cia = 1'
    '     AND t430.f430_ind_estado = 2'
    '     AND CAST(t430.f430_fecha_ts_creacion AS DATETIME) >= DATEADD(day, -30, GETDATE())'
    ' ORDER BY 1 DESC;'
    ' SET QUOTED_IDENTIFIER ON;'
)

FLOW_VENTAS = {
    "flow_name": "ventas",
    "flow_type": "sales",
    "sql": SQL_VENTAS,
    "warehouse_mapping": {},
}

SQL_FACTURAS = (
    'SET QUOTED_IDENTIFIER OFF;'
    ' SELECT TOP 10'
    ' CONCAT(TRIM(f350_id_tipo_docto), f350_id_co, "-", f350_consec_docto) AS pedido,'
    ' LTRIM(RTRIM(cliente.f200_nit)) AS cliente,'
    ' LTRIM(RTRIM(f201_id_sucursal)) AS sucursal_cliente,'
    ' CONVERT(varchar, f350_fecha, 23) AS fecha_pedido,'
    ' "draft" AS estado,'
    ' 1 AS almacen,'
    ' LTRIM(RTRIM(f120_id)) AS producto,'
    ' CAST(f470_cant_1 AS INTEGER) AS cantidad_pedida,'
    ' CAST(f470_precio_uni AS DECIMAL(18, 2)) AS precio_unitario,'
    ' "" AS impuesto,'
    ' "" AS zona,'
    ' "" AS vendedor,'
    ' LTRIM(RTRIM(f461_id_cond_pago)) AS condicion_pago,'
    ' "" AS observacion,'
    ' f470_id_unidad_medida AS unidad_medida,'
    ' TRIM(f150_id) AS bodega_siesa'
    ' FROM t350_co_docto_contable'
    ' INNER JOIN t461_cm_docto_factura_venta ON (f461_rowid_docto = f350_rowid)'
    ' INNER JOIN t470_cm_movto_invent ON (f470_rowid_docto_fact = f461_rowid_docto)'
    ' INNER JOIN t200_mm_terceros AS cliente ON (f461_rowid_tercero_fact = f200_rowid)'
    ' INNER JOIN t201_mm_clientes'
    '     ON (cliente.f200_rowid = f201_rowid_tercero AND f201_id_sucursal = f461_id_sucursal_fact)'
    ' INNER JOIN t121_mc_items_extensiones ON (f470_rowid_item_ext = f121_rowid)'
    ' INNER JOIN t120_mc_items ON (f121_rowid_item = f120_rowid)'
    ' INNER JOIN t150_mc_bodegas ON (f470_rowid_bodega = f150_rowid)'
    ' WHERE f350_id_tipo_docto IN ("FAC", "FPZ")'
    '     AND f350_id_cia = 1'
    '     AND CAST(f350_fecha_ts_creacion AS DATETIME) >= DATEADD(day, -30, GETDATE())'
    ' ORDER BY f350_consec_docto DESC;'
    ' SET QUOTED_IDENTIFIER ON;'
)

FLOW_FACTURAS = {
    "flow_name": "facturas",
    "flow_type": "sales",
    "sql": SQL_FACTURAS,
    "warehouse_mapping": {},
}

# Flow configs SIN TOP para resolve_missing_masters (trae todos del ERP, filtra en Python)
FLOW_ITEMS_RESOLVE = {
    **FLOW_ITEMS,
    "sql": SQL_ITEMS.replace(" TOP 10", ""),
}

FLOW_PROVEEDORES_RESOLVE = {
    **FLOW_PROVEEDORES,
    "sql": SQL_PROVEEDORES.replace(" TOP 5", ""),
}

FLOW_CLIENTES_RESOLVE = {
    **FLOW_CLIENTES,
    "sql": SQL_CLIENTES.replace(" TOP 5", ""),
}


# ============================================================
# PARTE 0 — Setup
# ============================================================
def setup():
    global config, odoo, connector, transform, logger

    header("SETUP")

    config = ConfigLoader(CLIENT_ID).load_config()
    config["client_id"] = CLIENT_ID
    logger = IntegradorLogger(client_id=CLIENT_ID)

    print(f"  URL Odoo:  {config['odoo']['url']}")
    print(f"  DB Odoo:   {config['odoo']['database']}")
    print(f"  ERP tipo:  {config['erp']['tipo']}")
    print(f"  ERP URL:   {config['erp']['url']}")

    odoo = JsonRPC(config)
    if odoo.authenticate():
        ok("SETUP", "Autenticacion Odoo OK")
    else:
        fail("SETUP", "Autenticacion Odoo FALLO")
        sys.exit(1)

    connector = SiesaEnterprise(config)
    status, msg = connector.test_connection()
    if status:
        ok("SETUP", f"Conexion SIESA WS OK - {msg}")
    else:
        fail("SETUP", f"Conexion SIESA WS FALLO - {msg}")
        print("  Las pruebas E2E fallaran sin conexion al ERP")

    transform = TransformWS(config)
    ok("SETUP", "TransformWS instanciado")


# ============================================================
# ESCENARIOS ITEMS
# ============================================================
def test_items():
    header("FLOW: ITEMS")

    # I1: Feliz — flujo completo E2E
    info("I1: Items feliz - SQL trae TOP 10 productos del ERP")
    data = transform.get_flow(connector, FLOW_ITEMS["flow_name"], FLOW_ITEMS)
    info(f"Transform retorno {len(data)} registros")
    if not data:
        fail("I1", "Transform retorno 0 registros - verificar SQL e id_cia")
        return

    # Mostrar muestra del primer registro
    info(f"Muestra primer registro: {list(data[0].keys())}")
    info(f"  referencia={data[0].get('referencia')}, descripcion={data[0].get('descripcion')[:50] if data[0].get('descripcion') else '?'}")

    processor = ProcessItems(odoo, config, FLOW_ITEMS)
    result = processor.process(data)
    info(f"Resultado: {result}")

    if result["creados"] + result["actualizados"] > 0:
        ok("I1", f"Items E2E: {result['creados']} creados, {result['actualizados']} actualizados")
    else:
        fail("I1", f"No se creo ni actualizo nada: {result}")

    # I3: Actualizacion — correr el mismo flow otra vez
    info("I3: Items actualizacion - mismos datos, segunda corrida")
    result2 = ProcessItems(odoo, config, FLOW_ITEMS).process(data)
    info(f"Resultado segunda corrida: {result2}")

    if result2["actualizados"] > 0 and result2["creados"] == 0:
        ok("I3", f"Actualizacion correcta: {result2['actualizados']} actualizados, 0 creados")
    elif result2["actualizados"] > 0:
        ok("I3", f"Parcial: {result2['actualizados']} actualizados, {result2['creados']} creados (puede haber fallado en I1)")
    else:
        fail("I3", f"Esperaba actualizados > 0: {result2}")

    # Verificar en Odoo que tracking no cambio
    ref_check = data[0].get("referencia", "")
    if ref_check:
        ok_v, prods = odoo.search_read(
            "product.template", [["default_code", "=", ref_check]], ["tracking", "name"]
        )
        if ok_v and prods:
            info(f"Verificacion Odoo: {ref_check} -> tracking={prods[0].get('tracking')}, name={prods[0].get('name')[:40]}")

    # I5: SQL vacio
    info("I5: Items SQL vacio - query retorna 0 registros")
    data_vacio = transform.get_flow(connector, FLOW_ITEMS_VACIO["flow_name"], FLOW_ITEMS_VACIO)
    result_vacio = ProcessItems(odoo, config, FLOW_ITEMS_VACIO).process(data_vacio)
    if result_vacio["creados"] == 0 and "error" not in result_vacio:
        ok("I5", f"SQL vacio manejado sin error: {result_vacio}")
    else:
        fail("I5", f"Resultado inesperado: {result_vacio}")

    # I6: SQL con error
    info("I6: Items SQL con error de sintaxis")
    data_error = transform.get_flow(connector, FLOW_ITEMS_SQL_ERROR["flow_name"], FLOW_ITEMS_SQL_ERROR)
    if data_error == []:
        ok("I6", "SQL con error -> transform retorno [] sin explotar")
    else:
        fail("I6", f"Esperaba [], obtuvo {len(data_error)} registros")

    result_error = ProcessItems(odoo, config, FLOW_ITEMS_SQL_ERROR).process(data_error)
    if result_error["creados"] == 0:
        ok("I6b", "Core no exploto con datos vacios")
    else:
        fail("I6b", f"Resultado inesperado: {result_error}")


# ============================================================
# ESCENARIOS PARTNERS - CLIENTES
# ============================================================
def test_clientes():
    header("FLOW: CLIENTES")

    # P1: Feliz
    info("P1: Clientes feliz - SQL trae TOP 5 del ERP")
    data = transform.get_flow(connector, FLOW_CLIENTES["flow_name"], FLOW_CLIENTES)
    info(f"Transform retorno {len(data)} registros")
    if not data:
        fail("P1", "Transform retorno 0 registros")
        return

    info(f"Muestra: identificacion={data[0].get('identificacion')}, nombre={data[0].get('nombre')[:40] if data[0].get('nombre') else '?'}")

    result = ProcessPartners(odoo, config, FLOW_CLIENTES).process(data)
    info(f"Resultado: {result}")

    if result["creados"] + result["actualizados"] > 0:
        ok("P1", f"Clientes E2E: {result['creados']} creados, {result['actualizados']} actualizados")
    else:
        fail("P1", f"No se creo ni actualizo nada: {result}")

    # Verificar ranks
    if data:
        vat_check = data[0].get("identificacion", "")
        if vat_check:
            ok_v, parts = odoo.search_read(
                "res.partner", [["vat", "=", vat_check]], ["customer_rank", "supplier_rank"]
            )
            if ok_v and parts:
                info(f"Verificacion: {vat_check} -> customer_rank={parts[0].get('customer_rank')}, supplier_rank={parts[0].get('supplier_rank')}")

    # P2: Actualizacion — segunda corrida
    info("P2: Clientes actualizacion - segunda corrida")
    result2 = ProcessPartners(odoo, config, FLOW_CLIENTES).process(data)
    info(f"Resultado segunda corrida: {result2}")

    if result2["actualizados"] > 0 and result2["creados"] == 0:
        ok("P2", f"Actualizacion correcta: {result2['actualizados']} actualizados")
    elif result2["actualizados"] > 0:
        ok("P2", f"Parcial: {result2['actualizados']} actualizados, {result2['creados']} creados")
    else:
        fail("P2", f"Esperaba actualizados > 0: {result2}")

    # P3: Jerarquia (solo si hay datos con misma identificacion y distintas sucursales)
    info("P3: Clientes con jerarquia")
    data_jer = transform.get_flow(connector, FLOW_CLIENTES_JERARQUIA["flow_name"], FLOW_CLIENTES_JERARQUIA)
    if data_jer:
        result3 = ProcessPartners(odoo, config, FLOW_CLIENTES_JERARQUIA).process(data_jer)
        info(f"Resultado jerarquia: {result3}")
        ok("P3", f"Jerarquia ejecutada: {result3['creados']} creados, {result3['actualizados']} actualizados")
    else:
        info("P3: Sin datos para jerarquia - skip")


# ============================================================
# ESCENARIOS PARTNERS - PROVEEDORES
# ============================================================
def test_proveedores():
    header("FLOW: PROVEEDORES")

    # P5: Feliz
    info("P5: Proveedores feliz - SQL trae TOP 5 del ERP")
    data = transform.get_flow(connector, FLOW_PROVEEDORES["flow_name"], FLOW_PROVEEDORES)
    info(f"Transform retorno {len(data)} registros")
    if not data:
        fail("P5", "Transform retorno 0 registros")
        return

    result = ProcessPartners(odoo, config, FLOW_PROVEEDORES).process(data)
    info(f"Resultado: {result}")

    if result["creados"] + result["actualizados"] > 0:
        ok("P5", f"Proveedores E2E: {result['creados']} creados, {result['actualizados']} actualizados")
    else:
        fail("P5", f"No se creo ni actualizo nada: {result}")

    # Verificar supplier_rank
    if data:
        vat_check = data[0].get("identificacion", "")
        if vat_check:
            ok_v, parts = odoo.search_read(
                "res.partner", [["vat", "=", vat_check]], ["customer_rank", "supplier_rank"]
            )
            if ok_v and parts:
                if parts[0].get("supplier_rank", 0) >= 1:
                    ok("P5b", f"supplier_rank >= 1 para {vat_check}")
                else:
                    fail("P5b", f"supplier_rank = {parts[0].get('supplier_rank')} para {vat_check}")


# ============================================================
# ESCENARIOS COMPRAS
# ============================================================
def test_compras():
    header("FLOW: COMPRAS")

    # C1: Compras feliz
    info("C1: Compras feliz - SQL de OC reales")
    data = transform.get_flow(connector, FLOW_COMPRAS["flow_name"], FLOW_COMPRAS)
    info(f"Transform retorno {len(data)} registros")
    if not data:
        fail("C1", "Transform retorno 0 registros - sin OCs recientes en el ERP")
        info("Probando con datos sinteticos para validar el core...")
        data = _datos_sinteticos_compras()
        if not data:
            return

    info(f"Muestra: compra={data[0].get('compra')}, producto={data[0].get('producto')}, proveedor={data[0].get('proveedor')}")

    # Resolve missing masters antes de procesar compras (como en produccion)
    info("Resolviendo maestros faltantes antes de crear compras...")
    resolve_result = resolve_missing_masters(
        odoo, connector, transform,
        data_purchases=data,
        data_sales=[],
        flow_configs={"items": FLOW_ITEMS_RESOLVE, "supplier": FLOW_PROVEEDORES_RESOLVE},
        config=config, logger=logger
    )
    info(f"Resolve: {resolve_result['productos_faltantes']} productos faltantes, "
         f"{resolve_result['productos_resueltos']} resueltos, "
         f"{resolve_result['proveedores_faltantes']} proveedores faltantes, "
         f"{resolve_result['proveedores_resueltos']} resueltos")
    if resolve_result.get("no_resueltos"):
        info(f"No resueltos: {len(resolve_result['no_resueltos'])}")

    result = ProcessPurchases(odoo, config, FLOW_COMPRAS).process(data)
    info(f"Resultado: {result}")

    if result["creados"] > 0:
        ok("C1", f"Compras E2E: {result['creados']} ordenes creadas")
    elif result["descartados"] > 0:
        ok("C1", f"Compras: {result['descartados']} ya existian (duplicadas)")
    elif result.get("fallidos"):
        fail("C1", f"Fallidos: {result['fallidos'][:3]}")
    else:
        fail("C1", f"Resultado inesperado: {result}")

    # C3: Duplicadas — segunda corrida
    info("C3: Compras duplicadas - segunda corrida")
    result2 = ProcessPurchases(odoo, config, FLOW_COMPRAS).process(data)
    info(f"Resultado segunda corrida: {result2}")

    if result2["descartados"] > 0 and result2["creados"] == 0:
        ok("C3", f"Duplicadas descartadas: {result2['descartados']} descartados, 0 creados")
    else:
        fail("C3", f"Esperaba descartados > 0, creados = 0: {result2}")

    # C9: Transferencia entrada — SQL distinto, mismo flow_type
    info("C9: Transferencia entrada - flow_name distinto, mismo ProcessPurchases")
    data_transf = transform.get_flow(connector, FLOW_TRANSFERENCIA_ENTRADA["flow_name"], FLOW_TRANSFERENCIA_ENTRADA)
    info(f"Transform retorno {len(data_transf)} registros")
    if data_transf:
        result_transf = ProcessPurchases(odoo, config, FLOW_TRANSFERENCIA_ENTRADA).process(data_transf)
        info(f"Resultado transferencia: {result_transf}")
        ok("C9", f"Transferencia entrada: {result_transf['creados']} creadas, {result_transf.get('descartados', 0)} descartadas")
    else:
        info("C9: Sin transferencias recientes - skip")

    # C10: Devolucion entrada
    info("C10: Devolucion entrada - flow_name distinto")
    data_dev = transform.get_flow(connector, FLOW_DEVOLUCION_IN["flow_name"], FLOW_DEVOLUCION_IN)
    info(f"Transform retorno {len(data_dev)} registros")
    if data_dev:
        result_dev = ProcessPurchases(odoo, config, FLOW_DEVOLUCION_IN).process(data_dev)
        info(f"Resultado devolucion: {result_dev}")
        ok("C10", f"Devolucion entrada: {result_dev['creados']} creadas")
    else:
        info("C10: Sin devoluciones recientes - skip")


def _datos_sinteticos_compras():
    """Genera datos sinteticos si el ERP no tiene OCs recientes."""
    # Buscar un producto y proveedor que existan en Odoo
    ok_p, prods = odoo.search_read("product.product", [], ["default_code"], limit=1)
    ok_s, supps = odoo.search_read("res.partner", [["supplier_rank", ">", 0]], ["vat", "sucursal"], limit=1)
    if not (ok_p and prods and ok_s and supps):
        info("No hay producto ni proveedor en Odoo para datos sinteticos")
        return []

    return [{
        "compra": f"{PREFIJO}-OC-SINT-001",
        "producto": prods[0]["default_code"],
        "proveedor": supps[0]["vat"],
        "sucursal_proveedor": supps[0].get("sucursal", "001"),
        "fecha_entrega": "2026-08-15",
        "estado": "draft",
        "almacen": "1",
        "cantidad": 5.0,
        "precio_unitario": 100.0,
        "impuesto": 19.0,
        "bodega_siesa": "",
    }]


# ============================================================
# ESCENARIOS VENTAS
# ============================================================
def test_ventas():
    header("FLOW: VENTAS")

    # V1: Ventas feliz
    info("V1: Ventas feliz - SQL de pedidos reales")
    data = transform.get_flow(connector, FLOW_VENTAS["flow_name"], FLOW_VENTAS)
    info(f"Transform retorno {len(data)} registros")
    if not data:
        fail("V1", "Transform retorno 0 registros - sin pedidos recientes")
        info("Probando con datos sinteticos...")
        data = _datos_sinteticos_ventas()
        if not data:
            return

    info(f"Muestra: pedido={data[0].get('pedido')}, producto={data[0].get('producto')}, cliente={data[0].get('cliente')}")

    # Resolve missing masters antes de procesar ventas (como en produccion)
    info("Resolviendo maestros faltantes antes de crear ventas...")
    resolve_result = resolve_missing_masters(
        odoo, connector, transform,
        data_purchases=[],
        data_sales=data,
        flow_configs={"items": FLOW_ITEMS_RESOLVE, "customer": FLOW_CLIENTES_RESOLVE},
        config=config, logger=logger
    )
    info(f"Resolve: {resolve_result['productos_faltantes']} productos faltantes, "
         f"{resolve_result['productos_resueltos']} resueltos, "
         f"{resolve_result['clientes_faltantes']} clientes faltantes, "
         f"{resolve_result['clientes_resueltos']} resueltos")
    if resolve_result.get("no_resueltos"):
        info(f"No resueltos: {len(resolve_result['no_resueltos'])}")

    result = ProcessSales(odoo, config, FLOW_VENTAS).process(data)
    info(f"Resultado: {result}")

    if result["creados"] > 0:
        ok("V1", f"Ventas E2E: {result['creados']} pedidos creados")
    elif result["descartados"] > 0:
        ok("V1", f"Ventas: {result['descartados']} ya existian")
    elif result.get("fallidos"):
        fail("V1", f"Fallidos: {result['fallidos'][:3]}")
    else:
        fail("V1", f"Resultado inesperado: {result}")

    # V3: Duplicadas
    info("V3: Ventas duplicadas - segunda corrida")
    result2 = ProcessSales(odoo, config, FLOW_VENTAS).process(data)
    if result2["descartados"] > 0 and result2["creados"] == 0:
        ok("V3", f"Duplicadas: {result2['descartados']} descartados, 0 creados")
    else:
        fail("V3", f"Esperaba descartados > 0: {result2}")

    # Verificar zona y note
    if data and data[0].get("pedido"):
        ok_v, orders = odoo.search_read(
            "sale.order", [["name", "=", data[0]["pedido"]]], ["delivery_zone_id", "note", "warehouse_id"]
        )
        if ok_v and orders:
            info(f"Verificacion Odoo: pedido={data[0]['pedido']} -> zone={orders[0].get('delivery_zone_id')}, note={str(orders[0].get('note', ''))[:50]}")

    # V9: Facturas — SQL distinto
    info("V9: Facturas - flow_name distinto, mismo ProcessSales")
    data_fac = transform.get_flow(connector, FLOW_FACTURAS["flow_name"], FLOW_FACTURAS)
    info(f"Transform retorno {len(data_fac)} registros")
    if data_fac:
        result_fac = ProcessSales(odoo, config, FLOW_FACTURAS).process(data_fac)
        info(f"Resultado facturas: {result_fac}")
        ok("V9", f"Facturas: {result_fac['creados']} creadas, {result_fac.get('descartados', 0)} descartadas")
    else:
        info("V9: Sin facturas recientes - skip")


def _datos_sinteticos_ventas():
    """Genera datos sinteticos si el ERP no tiene pedidos recientes."""
    ok_p, prods = odoo.search_read("product.product", [], ["default_code"], limit=1)
    ok_c, clis = odoo.search_read("res.partner", [["customer_rank", ">", 0]], ["vat", "sucursal"], limit=1)
    if not (ok_p and prods and ok_c and clis):
        info("No hay producto ni cliente en Odoo para datos sinteticos")
        return []

    return [{
        "pedido": f"{PREFIJO}-PED-SINT-001",
        "producto": prods[0]["default_code"],
        "cliente": clis[0]["vat"],
        "sucursal_cliente": clis[0].get("sucursal", "001"),
        "fecha_pedido": "2026-08-15",
        "estado": "draft",
        "almacen": "1",
        "cantidad_pedida": 3.0,
        "precio_unitario": 50.0,
        "zona": f"{PREFIJO}-ZONA-SINT",
        "vendedor": "",
        "condicion_pago": "",
        "observacion": "Pedido sintetico de prueba",
        "bodega_siesa": "",
    }]


# ============================================================
# ESCENARIOS RESOLVE MISSING MASTERS
# ============================================================
def test_resolve():
    header("FLOW: RESOLVE MISSING MASTERS")

    # R1: Todo existe
    info("R1: Todo existe - maestros ya cargados")
    # Buscar un producto y proveedor que ya esten en Odoo
    ok_p, prods = odoo.search_read("product.product", [], ["default_code"], limit=1)
    ok_s, supps = odoo.search_read("res.partner", [["supplier_rank", ">", 0]], ["vat", "sucursal"], limit=1)

    if ok_p and prods and ok_s and supps:
        result = resolve_missing_masters(
            odoo, connector, transform,
            data_purchases=[{
                "producto": prods[0]["default_code"],
                "proveedor": supps[0]["vat"],
                "sucursal_proveedor": supps[0].get("sucursal", "001"),
            }],
            data_sales=[],
            flow_configs={"items": FLOW_ITEMS, "supplier": FLOW_PROVEEDORES},
            config=config, logger=logger
        )
        info(f"Resultado: {result}")
        if result["productos_faltantes"] == 0:
            ok("R1", "Todo existe -> 0 faltantes")
        else:
            fail("R1", f"Esperaba 0 faltantes: {result}")
    else:
        info("R1: No hay datos en Odoo para probar - skip")

    # R3: Producto que no existe
    info("R3: Producto que el ERP tampoco tiene")
    result3 = resolve_missing_masters(
        odoo, connector, transform,
        data_purchases=[{
            "producto": "NOEXISTE-XYZ-IMPOSIBLE-999",
            "proveedor": supps[0]["vat"] if ok_s and supps else "123",
            "sucursal_proveedor": "001",
        }],
        data_sales=[],
        flow_configs={"items": FLOW_ITEMS},
        config=config, logger=logger
    )
    info(f"Resultado: {result3}")
    if result3["productos_faltantes"] >= 1:
        ok("R3", f"Producto faltante detectado, no_resueltos={len(result3.get('no_resueltos', []))}")
    else:
        fail("R3", f"Esperaba faltantes: {result3}")


# ============================================================
# LIMPIEZA
# ============================================================
def limpieza():
    header("LIMPIEZA")

    modelos = [
        ("sale.order", [["name", "like", f"{PREFIJO}%"]], "Pedidos de venta"),
        ("purchase.order", [["name", "like", f"{PREFIJO}%"]], "Ordenes de compra"),
        ("product.barcode.multi", [["name", "like", f"{PREFIJO}%"]], "Barcodes multi"),
        ("product.template", [["default_code", "like", f"{PREFIJO}%"]], "Productos"),
        ("res.partner", [["vat", "like", f"{PREFIJO}%"]], "Partners"),
        ("product.category", [["name", "like", f"{PREFIJO}%"]], "Categorias"),
        ("uom.uom", [["name", "like", f"{PREFIJO}%"]], "UOMs"),
        ("res.country.state", [["name", "like", f"{PREFIJO}%"]], "Departamentos"),
        ("partner.delivery.zone", [["name", "like", f"{PREFIJO}%"]], "Zonas"),
    ]

    for modelo, domain, label in modelos:
        try:
            ok_s, records = odoo.search_read(modelo, domain, ["id"])
            if ok_s and records:
                for r in records:
                    odoo.unlink(modelo, [r["id"]])
                print(f"  Eliminados {len(records)} {label}")
            else:
                print(f"  Sin {label} que limpiar")
        except Exception as e:
            print(f"  Error limpiando {label}: {e}")

    print(f"\n  Log: /var/log/integrador/{CLIENT_ID}.log")


# ============================================================
# RESUMEN
# ============================================================
def resumen():
    header("RESUMEN")
    print(f"  Pasaron:  {passed}")
    print(f"  Fallaron: {failed}")
    if errors:
        print(f"\n  Errores:")
        for e in errors:
            print(f"    [FAIL] {e}")


# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    parte = sys.argv[1] if len(sys.argv) > 1 else "all"

    setup()

    partes = {
        "items": test_items,
        "clientes": test_clientes,
        "proveedores": test_proveedores,
        "compras": test_compras,
        "ventas": test_ventas,
        "resolve": test_resolve,
        "limpieza": limpieza,
    }

    if parte == "all":
        try:
            test_items()
            test_clientes()
            test_proveedores()
            test_compras()
            test_ventas()
            test_resolve()
            resumen()
        except Exception as e:
            print(f"\nError fatal: {e}")
            traceback.print_exc()
        finally:
            resp = input("\nEjecutar limpieza? (s/n): ")
            if resp.lower() == "s":
                limpieza()
    elif parte in partes:
        try:
            partes[parte]()
            if parte != "limpieza":
                resumen()
        except Exception as e:
            print(f"\nError fatal: {e}")
            traceback.print_exc()
    else:
        print(f"Parte '{parte}' no reconocida.")
        print(f"Opciones: all, {', '.join(partes.keys())}")
 