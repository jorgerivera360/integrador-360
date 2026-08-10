"""
pruebasF4_connekta.py — Pruebas de integracion Fase 4 Core Layer (SIESA Connekta)
Ejecutar en wms-servertest con ENV=staging
Secret GCP: integrador-pruebackt (ERP Tito Pabon Connekta + Odoo pruebas)

Enfoque: Simula JSONs flow_config como vendrian del front.
Cada escenario ejecuta el flujo completo: connector REST -> transform (mapping+hardcodes+conditionals) -> core -> Odoo.

Uso:
  python pruebasF4_connekta.py              -> corre todos los escenarios
  python pruebasF4_connekta.py items        -> solo flow items
  python pruebasF4_connekta.py clientes     -> solo flow clientes
  python pruebasF4_connekta.py proveedores  -> solo flow proveedores
  python pruebasF4_connekta.py compras      -> solo flow compras
  python pruebasF4_connekta.py ventas       -> solo flow ventas
  python pruebasF4_connekta.py limpieza     -> solo limpieza
"""
import os
import sys
import traceback
from datetime import datetime, timedelta

os.environ["ENV"] = "staging"

from config.loader import ConfigLoader
from config.logger import IntegradorLogger
from connection.siesa_connekta import SiesaConnekta
from connection.jsonrpc import JsonRPC
from transform.transform_connekta import TransformConnekta
from core.process_items import ProcessItems
from core.process_partners import ProcessPartners
from core.process_purchases import ProcessPurchases
from core.process_sales import ProcessSales
from core.resolve_missing_masters import resolve_missing_masters

# ============================================================
# CONFIGURACION
# ============================================================
CLIENT_ID = "pruebackt"
PREFIJO = "TEST-F4CK"

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
# Tito Pabon Connekta (idCompania=7936):
# La API retorna campos con nombres del ERP. El mapping los renombra
# a canonicos. Hardcodes inyectan fijos. Conditionals evaluan reglas
# (Maneja_lote -> tracking) y funciones del catalogo
# (route_compra_manufactura_prefijo).
#
# TODOS los queries de Tito Pabon requieren parametros de fecha.

_hoy = datetime.now()
_hace_30 = _hoy - timedelta(days=30)
_hace_365 = _hoy - timedelta(days=365)
PARAMS_FECHA = f"FechaInicio = {_hace_30.strftime('%Y%m%d')}|FechaFin = {_hoy.strftime('%Y%m%d')}"
PARAMS_FECHA_CLI = f"fecha_inicio = {_hace_30.strftime('%Y%m%d')}|fecha_fin = {_hoy.strftime('%Y%m%d')}"
PARAMS_FECHA_OC = f"fecha_inicio = 20260101|fecha_fin = {_hoy.strftime('%Y%m%d')}"
# Rango amplio para resolve (365 dias, para encontrar maestros antiguos)
PARAMS_FECHA_RESOLVE = f"FechaInicio = {_hace_365.strftime('%Y%m%d')}|FechaFin = {_hoy.strftime('%Y%m%d')}"
PARAMS_FECHA_CLI_RESOLVE = f"fecha_inicio = {_hace_365.strftime('%Y%m%d')}|fecha_fin = {_hoy.strftime('%Y%m%d')}"

# --- ITEMS ---
# API retorna: Referencia_Item, name, barcode, precio, costo, peso,
#   volumen, unidad_venta, descripcion_inv_serv, Maneja_lote, Caducidad,
#   vida_util, Compra, Venta, Manufactura
FLOW_ITEMS = {
    "flow_name": "items",
    "flow_type": "items",
    "query_desc": "pinturastitopabon_producto_wms",
    "parametros": PARAMS_FECHA,
    "paginacion": False,
    "mapping": {
        "Referencia_Item": "referencia",
        "name": "descripcion",
        "barcode": "codigo_barras",
        "unidad_venta": "unidad",
        "descripcion_inv_serv": "categoria",
        "vida_util": "vence",
    },
    "hardcodes": {
        "impuesto": 19.0,
    },
    "conditionals": [
        {
            "tipo": "reglas",
            "campo_destino": "tracking",
            "campo_origen": "Maneja_lote",
            "reglas": [{"si": "SI", "entonces": "lot"}],
            "default": "none",
        },
        {
            "tipo": "reglas",
            "campo_destino": "use_expiration_date",
            "campo_origen": "Caducidad",
            "reglas": [{"si": "SI", "entonces": 1}],
            "default": 0,
        },
        {
            "tipo": "funcion",
            "campo_destino": "ruta",
            "funcion": "route_compra_manufactura_prefijo",
            "params": {
                "campo_compra": "Compra",
                "campo_manufactura": "Manufactura",
                "campo_referencia": "Referencia_Item",
                "prefijo_manufactura": "PT",
            },
        },
    ],
    "uom_mapping": {
        "UND": "Unidades",
        "und": "Unidades",
        "UNID": "Unidades",
        "KG": "kg",
        "kgs": "kg",
        "LT": "lt",
        "GAL": "Galones",
    },
}

FLOW_ITEMS_QUERY_VACIO = {
    "flow_name": "items",
    "flow_type": "items",
    "query_desc": "",
    "paginacion": False,
    "mapping": {},
    "hardcodes": {},
    "conditionals": [],
}

FLOW_ITEMS_QUERY_ERROR = {
    "flow_name": "items",
    "flow_type": "items",
    "query_desc": "query_inexistente_xyz_999",
    "paginacion": False,
    "mapping": {},
    "hardcodes": {},
    "conditionals": [],
}

# --- CLIENTES ---
# API retorna: vat, sucursal, nombre_completo, correo, telefono,
#   celular, direccion, codigo_postal, ciudad, departamento, pais, zona
FLOW_CLIENTES = {
    "flow_name": "partners",
    "flow_type": "customer",
    "query_desc": "pinturastitopabon_Clientes",
    "parametros": PARAMS_FECHA_CLI,
    "paginacion": False,
    "mapping": {
        "vat": "identificacion",
        "nombre_completo": "nombre",
        "correo": "email",
    },
    "hardcodes": {},
    "conditionals": [],
    "sucursal_hierarchy": True,
    "sucursal_padre": "001",
    "country_id": 49,
    "identification_type_id": 5,
}

FLOW_CLIENTES_SIN_JERARQUIA = {
    **FLOW_CLIENTES,
    "sucursal_hierarchy": False,
}

# --- PROVEEDORES ---
FLOW_PROVEEDORES = {
    "flow_name": "partners",
    "flow_type": "supplier",
    "query_desc": "pinturastitopabon_Proveedores",
    "parametros": PARAMS_FECHA_CLI,
    "paginacion": False,
    "mapping": {
        "vat": "identificacion",
        "nombre_completo": "nombre",
        "correo": "email",
    },
    "hardcodes": {},
    "conditionals": [],
    "country_id": 49,
    "identification_type_id": 5,
}

# --- COMPRAS ---
# API retorna: documento, id_tercero, id_sucursal_prov, fechaDocto,
#   consec_docto, Bodega, Referencia, Cant_pendiente, Precio_unit,
#   id_tercero_comprador, Desc_bodega, Fecha_entrega
FLOW_COMPRAS = {
    "flow_name": "compras",
    "flow_type": "purchases",
    "query_desc": "pinturastitopabon_OrdenDeCompra",
    "parametros": PARAMS_FECHA_OC,
    "paginacion": False,
    "mapping": {
        "documento": "compra",
        "id_tercero": "proveedor",
        "id_sucursal_prov": "sucursal_proveedor",
        "consec_docto": "referencia_compra",
        "Referencia": "producto",
        "Cant_pendiente": "cantidad",
        "Precio_unit": "precio_unitario",
        "Desc_bodega": "bodega_siesa",
        "id_tercero_comprador": "comprador",
        "Fecha_entrega": "fecha_entrega",
    },
    "hardcodes": {
        "estado": "draft",
        "impuesto": 19.0,
        "almacen": 1,
    },
    "conditionals": [],
    "warehouse_mapping": {},
}

# --- VENTAS ---
# API retorna: documento, id_tercero, id_sucursal_cli, fecha,
#   referencia_item, cant_pedida, Precio_unit, notas, bodega, co,
#   unidad_medida, consec_docto, id_tipo_docto
FLOW_VENTAS = {
    "flow_name": "ventas",
    "flow_type": "sales",
    "query_desc": "pinturastitopabon_pedidospuntodeventa",
    "paginacion": False,
    "mapping": {
        "documento": "pedido",
        "id_tercero": "cliente",
        "id_sucursal_cli": "sucursal_cliente",
        "fecha": "fecha_pedido",
        "referencia_item": "producto",
        "cant_pedida": "cantidad_pedida",
        "Precio_unit": "precio_unitario",
        "notas": "observacion",
        "co": "zona",
    },
    "hardcodes": {
        "estado": "draft",
        "impuesto": 19.0,
        "almacen": 1,
        "precio_unitario": 0,
    },
    "conditionals": [],
    "warehouse_mapping": {},
}

# --- RESOLVE (rango amplio de fecha para encontrar maestros antiguos) ---
FLOW_ITEMS_RESOLVE = {**FLOW_ITEMS, "parametros": PARAMS_FECHA_RESOLVE}
FLOW_PROVEEDORES_RESOLVE = {**FLOW_PROVEEDORES, "parametros": PARAMS_FECHA_CLI_RESOLVE}
FLOW_CLIENTES_RESOLVE = {**FLOW_CLIENTES, "parametros": PARAMS_FECHA_CLI_RESOLVE}


# ============================================================
# SETUP
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
    print(f"  Compania:  {config['erp']['idcompania']}")

    odoo = JsonRPC(config)
    if odoo.authenticate():
        ok("SETUP", "Autenticacion Odoo OK")
    else:
        fail("SETUP", "Autenticacion Odoo FALLO")
        sys.exit(1)

    connector = SiesaConnekta(config)
    status, msg = connector.test_connection()
    if status:
        ok("SETUP", f"Conexion Connekta OK - {msg}")
    else:
        fail("SETUP", f"Conexion Connekta FALLO - {msg}")
        print("  Las pruebas E2E fallaran sin conexion al ERP")

    transform = TransformConnekta(config)
    ok("SETUP", "TransformConnekta instanciado")


# ============================================================
# ITEMS
# ============================================================
def test_items():
    header("FLOW: ITEMS (Tito Pabon)")

    # CI1: Feliz con mapping + hardcodes + conditionals
    info("CI1: Items feliz - mapping + hardcodes + conditionals (reglas + funcion)")
    data = transform.get_flow(connector, FLOW_ITEMS["flow_name"], FLOW_ITEMS)
    info(f"Transform retorno {len(data)} registros")
    if not data:
        fail("CI1", "Transform retorno 0 registros")
        return

    info(f"Muestra primer registro: {list(data[0].keys())}")
    info(f"  referencia={data[0].get('referencia')}, descripcion={str(data[0].get('descripcion', '?'))[:50]}")

    # CI2: Verificar mapping (Referencia_Item -> referencia)
    if "referencia" in data[0] and "Referencia_Item" not in data[0]:
        ok("CI2", f"Mapping funciono: Referencia_Item -> referencia = {data[0].get('referencia')}")
    elif "referencia" in data[0]:
        ok("CI2", f"Mapping funciono (campo original conservado): referencia = {data[0].get('referencia')}")
    else:
        fail("CI2", f"Mapping no funciono: keys = {list(data[0].keys())}")

    # CI3: Verificar hardcodes
    if data[0].get("impuesto") == 19.0:
        ok("CI3", f"Hardcodes funciono: impuesto = {data[0].get('impuesto')}")
    else:
        fail("CI3", f"Hardcodes no funciono: impuesto = {data[0].get('impuesto')}")

    # CI4: Verificar conditionals reglas (Maneja_lote -> tracking)
    if "tracking" in data[0]:
        ok("CI4", f"Conditional reglas funciono: tracking = {data[0].get('tracking')}")
    else:
        fail("CI4", f"Conditional reglas no funciono: keys = {list(data[0].keys())}")

    # CI5: Verificar conditional funcion (route_compra_manufactura_prefijo -> ruta)
    if "ruta" in data[0]:
        ok("CI5", f"Conditional funcion funciono: ruta = {data[0].get('ruta')}")
    else:
        fail("CI5", f"Conditional funcion no funciono: keys = {list(data[0].keys())}")

    # Procesar primeros 10
    data_limitada = data[:10]
    processor = ProcessItems(odoo, config, FLOW_ITEMS)
    result = processor.process(data_limitada)
    info(f"Resultado: {result}")

    if result["creados"] + result["actualizados"] > 0:
        ok("CI1", f"Items E2E: {result['creados']} creados, {result['actualizados']} actualizados")
    else:
        fail("CI1", f"No se creo ni actualizo nada: {result}")

    # CI6: Actualizacion
    info("CI6: Items actualizacion - segunda corrida")
    result2 = ProcessItems(odoo, config, FLOW_ITEMS).process(data_limitada)
    info(f"Resultado segunda corrida: {result2}")

    if result2["actualizados"] > 0 and result2["creados"] == 0:
        ok("CI6", f"Actualizacion correcta: {result2['actualizados']} actualizados, 0 creados")
    elif result2["actualizados"] > 0:
        ok("CI6", f"Parcial: {result2['actualizados']} actualizados, {result2['creados']} creados")
    else:
        fail("CI6", f"Esperaba actualizados > 0: {result2}")

    # CI7: query_desc vacio
    info("CI7: Items query_desc vacio")
    data_vacio = transform.get_flow(connector, FLOW_ITEMS_QUERY_VACIO["flow_name"], FLOW_ITEMS_QUERY_VACIO)
    if data_vacio == []:
        ok("CI7", "query_desc vacio -> transform retorno [] sin explotar")
    else:
        fail("CI7", f"Esperaba [], obtuvo {len(data_vacio)} registros")

    # CI8: query_desc inexistente
    info("CI8: Items query_desc inexistente")
    data_error = transform.get_flow(connector, FLOW_ITEMS_QUERY_ERROR["flow_name"], FLOW_ITEMS_QUERY_ERROR)
    if data_error == []:
        ok("CI8", "query_desc inexistente -> transform retorno [] sin explotar")
    else:
        fail("CI8", f"Esperaba [], obtuvo {len(data_error)} registros")


# ============================================================
# CLIENTES
# ============================================================
def test_clientes():
    header("FLOW: CLIENTES (Tito Pabon)")

    # CP1: Feliz sin jerarquia
    info("CP1: Clientes feliz - query_desc con mapping (sin jerarquia)")
    data = transform.get_flow(connector, FLOW_CLIENTES_SIN_JERARQUIA["flow_name"], FLOW_CLIENTES_SIN_JERARQUIA)
    info(f"Transform retorno {len(data)} registros")
    if not data:
        fail("CP1", "Transform retorno 0 registros")
        return

    info(f"Muestra: identificacion={data[0].get('identificacion')}, nombre={str(data[0].get('nombre', '?'))[:40]}")

    # Verificar mapping: vat -> identificacion
    if "identificacion" in data[0]:
        ok("CP1-map", f"Mapping vat->identificacion funciono")
    else:
        fail("CP1-map", f"Mapping no funciono: keys = {list(data[0].keys())}")

    data_limitada = data[:5]
    result = ProcessPartners(odoo, config, FLOW_CLIENTES_SIN_JERARQUIA).process(data_limitada)
    info(f"Resultado: {result}")

    if result["creados"] + result["actualizados"] > 0:
        ok("CP1", f"Clientes E2E: {result['creados']} creados, {result['actualizados']} actualizados")
    else:
        fail("CP1", f"No se creo ni actualizo nada: {result}")

    # CP2: Actualizacion
    info("CP2: Clientes actualizacion - segunda corrida")
    result2 = ProcessPartners(odoo, config, FLOW_CLIENTES_SIN_JERARQUIA).process(data_limitada)
    info(f"Resultado segunda corrida: {result2}")

    if result2["actualizados"] > 0 and result2["creados"] == 0:
        ok("CP2", f"Actualizacion correcta: {result2['actualizados']} actualizados")
    elif result2["actualizados"] > 0:
        ok("CP2", f"Parcial: {result2['actualizados']} actualizados, {result2['creados']} creados")
    else:
        fail("CP2", f"Esperaba actualizados > 0: {result2}")

    # CP3: Jerarquia (Tito Pabon usa jerarquia en produccion)
    info("CP3: Clientes con jerarquia (sucursal_hierarchy=true)")
    result3 = ProcessPartners(odoo, config, FLOW_CLIENTES).process(data_limitada)
    info(f"Resultado jerarquia: {result3}")
    ok("CP3", f"Jerarquia ejecutada: {result3['creados']} creados, {result3['actualizados']} actualizados")


# ============================================================
# PROVEEDORES
# ============================================================
def test_proveedores():
    header("FLOW: PROVEEDORES (Tito Pabon)")

    # CP4: Feliz
    info("CP4: Proveedores feliz - query_desc con mapping")
    data = transform.get_flow(connector, FLOW_PROVEEDORES["flow_name"], FLOW_PROVEEDORES)
    info(f"Transform retorno {len(data)} registros")
    if not data:
        fail("CP4", "Transform retorno 0 registros")
        return

    data_limitada = data[:5]
    result = ProcessPartners(odoo, config, FLOW_PROVEEDORES).process(data_limitada)
    info(f"Resultado: {result}")

    if result["creados"] + result["actualizados"] > 0:
        ok("CP4", f"Proveedores E2E: {result['creados']} creados, {result['actualizados']} actualizados")
    else:
        fail("CP4", f"No se creo ni actualizo nada: {result}")

    # Verificar supplier_rank
    if data_limitada:
        vat_check = data_limitada[0].get("identificacion", "")
        if vat_check:
            ok_v, parts = odoo.search_read(
                "res.partner", [["vat", "=", vat_check]], ["customer_rank", "supplier_rank"]
            )
            if ok_v and parts:
                if parts[0].get("supplier_rank", 0) >= 1:
                    ok("CP4b", f"supplier_rank >= 1 para {vat_check}")
                else:
                    fail("CP4b", f"supplier_rank = {parts[0].get('supplier_rank')} para {vat_check}")


# ============================================================
# COMPRAS
# ============================================================
def test_compras():
    header("FLOW: COMPRAS (Tito Pabon)")

    # CC1: Compras feliz con resolve
    info("CC1: Compras feliz - OC reales con mapping + resolve")
    data = transform.get_flow(connector, FLOW_COMPRAS["flow_name"], FLOW_COMPRAS)
    info(f"Transform retorno {len(data)} registros")
    if not data:
        fail("CC1", "Transform retorno 0 registros - sin OCs en el ERP")
        return

    data_limitada = data[:10]
    info(f"Muestra: compra={data_limitada[0].get('compra')}, producto={data_limitada[0].get('producto')}, proveedor={data_limitada[0].get('proveedor')}")

    # Resolve missing masters
    info("Resolviendo maestros faltantes antes de crear compras...")
    resolve_result = resolve_missing_masters(
        odoo, connector, transform,
        data_purchases=data_limitada,
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

    result = ProcessPurchases(odoo, config, FLOW_COMPRAS).process(data_limitada)
    info(f"Resultado: {result}")

    if result["creados"] > 0:
        ok("CC1", f"Compras E2E: {result['creados']} ordenes creadas")
    elif result["descartados"] > 0:
        ok("CC1", f"Compras: {result['descartados']} ya existian")
    elif result.get("fallidos"):
        fail("CC1", f"Fallidos: {result['fallidos'][:3]}")
    else:
        fail("CC1", f"Resultado inesperado: {result}")

    # CC4: Duplicadas
    info("CC4: Compras duplicadas - segunda corrida")
    result2 = ProcessPurchases(odoo, config, FLOW_COMPRAS).process(data_limitada)
    info(f"Resultado segunda corrida: {result2}")

    if result2["descartados"] > 0 and result2["creados"] == 0:
        ok("CC4", f"Duplicadas descartadas: {result2['descartados']} descartados, 0 creados")
    else:
        fail("CC4", f"Esperaba descartados > 0, creados = 0: {result2}")


# ============================================================
# VENTAS
# ============================================================
def test_ventas():
    header("FLOW: VENTAS (Tito Pabon)")

    # CV1: Ventas feliz con resolve
    info("CV1: Ventas feliz - pedidos reales con mapping + resolve")
    data = transform.get_flow(connector, FLOW_VENTAS["flow_name"], FLOW_VENTAS)
    info(f"Transform retorno {len(data)} registros")
    if not data:
        fail("CV1", "Transform retorno 0 registros - sin pedidos recientes")
        return

    data_limitada = data[:10]
    info(f"Muestra: pedido={data_limitada[0].get('pedido')}, producto={data_limitada[0].get('producto')}, cliente={data_limitada[0].get('cliente')}")

    # Resolve missing masters
    info("Resolviendo maestros faltantes antes de crear ventas...")
    resolve_result = resolve_missing_masters(
        odoo, connector, transform,
        data_purchases=[],
        data_sales=data_limitada,
        flow_configs={"items": FLOW_ITEMS_RESOLVE, "customer": FLOW_CLIENTES_RESOLVE},
        config=config, logger=logger
    )
    info(f"Resolve: {resolve_result['productos_faltantes']} productos faltantes, "
         f"{resolve_result['productos_resueltos']} resueltos, "
         f"{resolve_result['clientes_faltantes']} clientes faltantes, "
         f"{resolve_result['clientes_resueltos']} resueltos")
    if resolve_result.get("no_resueltos"):
        info(f"No resueltos: {len(resolve_result['no_resueltos'])}")

    result = ProcessSales(odoo, config, FLOW_VENTAS).process(data_limitada)
    info(f"Resultado: {result}")

    if result["creados"] > 0:
        ok("CV1", f"Ventas E2E: {result['creados']} pedidos creados")
    elif result["descartados"] > 0:
        ok("CV1", f"Ventas: {result['descartados']} ya existian")
    elif result.get("fallidos"):
        fail("CV1", f"Fallidos: {result['fallidos'][:3]}")
    else:
        fail("CV1", f"Resultado inesperado: {result}")

    # CV3: Duplicadas
    info("CV3: Ventas duplicadas - segunda corrida")
    result2 = ProcessSales(odoo, config, FLOW_VENTAS).process(data_limitada)
    if result2["descartados"] > 0 and result2["creados"] == 0:
        ok("CV3", f"Duplicadas: {result2['descartados']} descartados, 0 creados")
    else:
        fail("CV3", f"Esperaba descartados > 0: {result2}")


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
        "limpieza": limpieza,
    }

    if parte == "all":
        try:
            test_items()
            test_clientes()
            test_proveedores()
            test_compras()
            test_ventas()
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
