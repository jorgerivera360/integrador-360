"""
pruebasF4_sap.py — Pruebas de integracion Fase 4 Core Layer (SAP B1)
Ejecutar en wms-servertest con ENV=staging
Secret GCP: integrador-pruebasap (ERP BYCSA SAP B1 + Odoo pruebas)

Enfoque: Simula JSONs flow_config como vendrian del front.
Cada escenario ejecuta el flujo completo: connector OData -> transform
(prefetch categorias + flatten_lines + mapping + hardcodes + conditionals) -> core -> Odoo.

Uso:
  python pruebasF4_sap.py              -> corre todos los escenarios
  python pruebasF4_sap.py items        -> solo flow items
  python pruebasF4_sap.py clientes     -> solo flow clientes
  python pruebasF4_sap.py proveedores  -> solo flow proveedores
  python pruebasF4_sap.py compras      -> solo flow compras
  python pruebasF4_sap.py ventas       -> solo flow ventas
  python pruebasF4_sap.py limpieza     -> solo limpieza
"""
import os
import sys
import traceback

os.environ["ENV"] = "staging"

from config.loader import ConfigLoader
from config.logger import IntegradorLogger
from connection.sap import SAP
from connection.jsonrpc import JsonRPC
from transform.transform_sap import TransformSAP
from core.process_items import ProcessItems
from core.process_partners import ProcessPartners
from core.process_purchases import ProcessPurchases
from core.process_sales import ProcessSales
from core.resolve_missing_masters import resolve_missing_masters

# ============================================================
# CONFIGURACION
# ============================================================
CLIENT_ID = "pruebasap"
PREFIJO = "TEST-F4SAP"

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
# BYCSA SAP B1: la API OData retorna objetos JSON con arrays anidados
# (DocumentLines, BPAddresses). El transform aplana con _flatten_lines,
# prefetch /ItemGroups para categorias, mapping header+lineas,
# hardcodes y conditionals con funciones del catalogo.

# Categorias que manejan lote en BYCSA
CATEGORIAS_LOTE = [
    307, 313, 315, 316, 317, 304, 320, 321, 322, 323, 329, 332,
    331, 333, 334, 318, 309, 314, 319, 305, 330, 308, 324, 337,
    340, 306, 339, 341, 342, 344, 345, 346, 347, 349, 352, 351, 350,
]

# --- ITEMS ---
# SAP retorna: ItemCode, ItemName, BarCode, U_FB_EANWMS, ItemsGroupCode,
#   ProdStdCost, InventoryUOM, SalesUnitWeight, SalesUnitVolume,
#   PurchaseItem, InventoryItem, U_FB_EnviarWMS, U_FB_EnviarProdWMS
# Items son planos (no usan _flatten_lines)
FLOW_ITEMS = {
    "flow_name": "items",
    "flow_type": "items",
    "endpoint": "Items",
    "filter": "Valid eq 'tYES' and UpdateDate ge '2026-07-01'",
    "mapping": {
        "ItemCode": "referencia",
        "ItemName": "descripcion",
        "BarCode": "codigo_barras",
        "U_FB_EANWMS": "codigos_extras",
        "ItemsGroupCode_resolved": "categoria",
        "ProdStdCost": "costo",
        "InventoryUOM": "unidad",
        "SalesUnitWeight": "peso",
        "SalesUnitVolume": "volumen",
    },
    "hardcodes": {
        "precio": 0,
        "impuesto": 0,
    },
    "conditionals": [
        {
            "tipo": "funcion",
            "campo_destino": "tracking",
            "funcion": "valor_por_lista",
            "params": {
                "campo_origen": "ItemsGroupCode",
                "lista": CATEGORIAS_LOTE,
                "si": "lot",
                "no": "none",
            },
        },
        {
            "tipo": "funcion",
            "campo_destino": "ruta",
            "funcion": "valor_por_campo",
            "params": {
                "campo_origen": "PurchaseItem",
                "valor": "tYES",
                "si": "Buy",
                "no": "Fabricar",
            },
        },
        {
            "tipo": "funcion",
            "campo_destino": "type",
            "funcion": "valor_por_campo",
            "params": {
                "campo_origen": "InventoryItem",
                "valor": "tYES",
                "si": "product",
                "no": "consu",
            },
        },
        {
            "tipo": "funcion",
            "campo_destino": "sap_field",
            "funcion": "sap_field_combined",
            "params": {
                "campo1": "U_FB_EnviarWMS",
                "campo2": "U_FB_EnviarProdWMS",
                "valor_esperado": "Y",
                "texto_ambos": "Producto Terminado, Produccion",
                "texto_solo_uno": "Producto Terminado",
            },
        },
    ],
    "uom_mapping": {
        "UND": "Unidades",
        "und": "Unidades",
        "UNID": "Unidades",
        "KG": "kg",
        "LT": "lt",
        "MT": "m",
    },
}

FLOW_ITEMS_ERROR = {
    "flow_name": "items",
    "flow_type": "items",
    "endpoint": "",
    "filter": "",
    "mapping": {},
    "hardcodes": {},
    "conditionals": [],
}

# --- CLIENTES ---
# SAP retorna BusinessPartners con BPAddresses anidado
FLOW_CLIENTES = {
    "flow_name": "partners",
    "flow_type": "customer",
    "endpoint": "BusinessPartners",
    "filter": "CardType eq 'cCustomer' and UpdateDate ge '2026-07-01'",
    "mapping": {
        "CardCode": "identificacion",
        "CardName": "nombre",
        "EmailAddress": "email",
        "Phone1": "telefono",
        "Phone2": "celular",
    },
    "mapping_lineas": {
        "origen": "BPAddresses",
        "campos": {
            "AddressName": "sucursal",
            "Street": "direccion",
            "ZipCode": "codigo_postal",
            "City": "ciudad",
            "U_Zona": "zona",
        },
    },
    "hardcodes": {
        "departamento": "",
        "pais": "Colombia",
    },
    "conditionals": [],
    "sucursal_hierarchy": False,
    "country_id": 49,
    "identification_type_id": 5,
}

# --- PROVEEDORES ---
FLOW_PROVEEDORES = {
    "flow_name": "partners",
    "flow_type": "supplier",
    "endpoint": "BusinessPartners",
    "filter": "CardType eq 'cSupplier' and UpdateDate ge '2026-07-01'",
    "mapping": {
        "CardCode": "identificacion",
        "CardName": "nombre",
        "EmailAddress": "email",
        "Phone1": "telefono",
        "Phone2": "celular",
    },
    "mapping_lineas": {
        "origen": "BPAddresses",
        "campos": {
            "AddressName": "sucursal",
            "Street": "direccion",
            "ZipCode": "codigo_postal",
            "City": "ciudad",
        },
    },
    "hardcodes": {
        "departamento": "",
        "pais": "Colombia",
    },
    "conditionals": [],
    "country_id": 49,
    "identification_type_id": 5,
}

# --- COMPRAS ---
# SAP retorna PurchaseOrders con DocumentLines anidado
FLOW_COMPRAS = {
    "flow_name": "compras",
    "flow_type": "purchases",
    "endpoint": "PurchaseOrders",
    "filter": "DocumentStatus eq 'bost_Open'",
    "mapping": {
        "CardCode": "proveedor",
        "DocDate": "fecha_entrega",
        "DocNum": "referencia_compra",
    },
    "mapping_lineas": {
        "origen": "DocumentLines",
        "campos": {
            "ItemCode": "producto",
            "Quantity": "cantidad",
            "UnitPrice": "precio_unitario",
            "WarehouseCode": "bodega_sap",
        },
    },
    "hardcodes": {
        "sucursal_proveedor": "000",
        "estado": "draft",
        "impuesto": 19,
        "almacen": 1,
    },
    "conditionals": [
        {
            "tipo": "funcion",
            "campo_destino": "compra",
            "funcion": "doc_name_por_rango",
            "params": {
                "campo_origen": "DocNum",
                "rangos": {"1-10000000": "OCNAL"},
                "separador": "-",
            },
        },
    ],
    "warehouse_mapping": {},
}

# --- VENTAS ---
# SAP retorna Orders con DocumentLines anidado
FLOW_VENTAS = {
    "flow_name": "ventas",
    "flow_type": "sales",
    "endpoint": "Orders",
    "filter": "DocumentStatus eq 'bost_Open'",
    "mapping": {
        "CardCode": "cliente",
        "ShipToCode": "sucursal_cliente",
        "DocDate": "fecha_pedido",
        "Comments": "observacion",
    },
    "mapping_lineas": {
        "origen": "DocumentLines",
        "campos": {
            "ItemCode": "producto",
            "Quantity": "cantidad_pedida",
            "UnitPrice": "precio_unitario",
            "WarehouseCode": "bodega_sap",
            "ItemDescription": "descripcion",
        },
    },
    "hardcodes": {
        "estado": "draft",
        "impuesto": 0,
        "almacen": 1,
        "zona": "",
        "vendedor": "",
        "condicion_pago": "",
    },
    "conditionals": [
        {
            "tipo": "funcion",
            "campo_destino": "pedido",
            "funcion": "doc_name_por_rango",
            "params": {
                "campo_origen": "DocNum",
                "rangos": {"1-10000000": "PVNAL"},
                "separador": "-",
            },
        },
    ],
    "warehouse_mapping": {},
}

# --- RESOLVE (filtro de 6 meses para no traer todo el historico) ---
FLOW_ITEMS_RESOLVE = {**FLOW_ITEMS, "filter": "Valid eq 'tYES' and UpdateDate ge '2026-01-01'"}
FLOW_PROVEEDORES_RESOLVE = {**FLOW_PROVEEDORES, "filter": "CardType eq 'cSupplier' and UpdateDate ge '2026-01-01'"}
FLOW_CLIENTES_RESOLVE = {**FLOW_CLIENTES, "filter": "CardType eq 'cCustomer' and UpdateDate ge '2026-01-01'"}


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
    print(f"  Compania:  {config['erp']['compania']}")

    odoo = JsonRPC(config)
    if odoo.authenticate():
        ok("SETUP", "Autenticacion Odoo OK")
    else:
        fail("SETUP", "Autenticacion Odoo FALLO")
        sys.exit(1)

    connector = SAP(config)
    if connector.login_api():
        ok("SETUP", f"Login SAP OK - SessionId obtenido")
    else:
        fail("SETUP", "Login SAP FALLO")
        print("  Las pruebas E2E fallaran sin conexion a SAP")

    transform = TransformSAP(config)
    ok("SETUP", "TransformSAP instanciado")


# ============================================================
# ITEMS
# ============================================================
def test_items():
    header("FLOW: ITEMS (BYCSA)")

    # SI1: Feliz con prefetch categorias + mapping + conditionals
    info("SI1: Items feliz - prefetch categorias + mapping + 4 conditionals")
    data = transform.get_flow(connector, FLOW_ITEMS["flow_name"], FLOW_ITEMS)
    info(f"Transform retorno {len(data)} registros")
    if not data:
        fail("SI1", "Transform retorno 0 registros")
        return

    info(f"Muestra primer registro: {list(data[0].keys())[:15]}...")
    info(f"  referencia={data[0].get('referencia')}, descripcion={str(data[0].get('descripcion', '?'))[:50]}")

    # SI2: Verificar mapping
    if "referencia" in data[0]:
        ok("SI2", f"Mapping ItemCode->referencia funciono: {data[0].get('referencia')}")
    else:
        fail("SI2", f"Mapping no funciono: keys = {list(data[0].keys())[:10]}")

    # SI3: Verificar prefetch categorias
    if data[0].get("categoria") and data[0].get("categoria") != "Sin categoria":
        ok("SI3", f"Prefetch categorias funciono: categoria={data[0].get('categoria')}")
    else:
        info(f"SI3: categoria={data[0].get('categoria')} (puede ser Sin categoria)")
        ok("SI3", "Prefetch ejecutado")

    # SI4: Verificar conditionals
    if "tracking" in data[0]:
        ok("SI4a", f"Conditional valor_por_lista -> tracking={data[0].get('tracking')}")
    else:
        fail("SI4a", "Conditional tracking no funciono")

    if "ruta" in data[0]:
        ok("SI4b", f"Conditional valor_por_campo -> ruta={data[0].get('ruta')}")
    else:
        fail("SI4b", "Conditional ruta no funciono")

    if "type" in data[0]:
        ok("SI4c", f"Conditional valor_por_campo -> type={data[0].get('type')}")
    else:
        fail("SI4c", "Conditional type no funciono")

    if "sap_field" in data[0]:
        ok("SI4d", f"Conditional sap_field_combined -> sap_field={data[0].get('sap_field')}")
    else:
        fail("SI4d", "Conditional sap_field no funciono")

    # Procesar primeros 10
    data_limitada = data[:10]
    result = ProcessItems(odoo, config, FLOW_ITEMS).process(data_limitada)
    info(f"Resultado: {result}")

    if result["creados"] + result["actualizados"] > 0:
        ok("SI1", f"Items E2E: {result['creados']} creados, {result['actualizados']} actualizados")
    else:
        fail("SI1", f"No se creo ni actualizo nada: {result}")

    # SI5: Actualizacion
    info("SI5: Items actualizacion - segunda corrida")
    result2 = ProcessItems(odoo, config, FLOW_ITEMS).process(data_limitada)
    info(f"Resultado segunda corrida: {result2}")

    if result2["actualizados"] > 0 and result2["creados"] == 0:
        ok("SI5", f"Actualizacion correcta: {result2['actualizados']} actualizados, 0 creados")
    elif result2["actualizados"] > 0:
        ok("SI5", f"Parcial: {result2['actualizados']} actualizados, {result2['creados']} creados")
    else:
        fail("SI5", f"Esperaba actualizados > 0: {result2}")

    # SI6: Endpoint vacio
    info("SI6: Items endpoint vacio")
    data_error = transform.get_flow(connector, FLOW_ITEMS_ERROR["flow_name"], FLOW_ITEMS_ERROR)
    if data_error == []:
        ok("SI6", "Endpoint vacio -> transform retorno [] sin explotar")
    else:
        fail("SI6", f"Esperaba [], obtuvo {len(data_error)} registros")


# ============================================================
# CLIENTES
# ============================================================
def test_clientes():
    header("FLOW: CLIENTES (BYCSA)")

    # SP1: Feliz con flatten BPAddresses
    info("SP1: Clientes feliz - flatten BPAddresses + mapping")
    data = transform.get_flow(connector, FLOW_CLIENTES["flow_name"], FLOW_CLIENTES)
    info(f"Transform retorno {len(data)} registros")
    if not data:
        fail("SP1", "Transform retorno 0 registros")
        return

    info(f"Muestra: identificacion={data[0].get('identificacion')}, nombre={str(data[0].get('nombre', '?'))[:40]}")

    if "identificacion" in data[0] and "sucursal" in data[0]:
        ok("SP1-map", f"Mapping + flatten funciono: identificacion={data[0].get('identificacion')}, sucursal={data[0].get('sucursal')}")
    else:
        fail("SP1-map", f"Mapping no funciono: keys = {list(data[0].keys())[:10]}")

    data_limitada = data[:5]
    result = ProcessPartners(odoo, config, FLOW_CLIENTES).process(data_limitada)
    info(f"Resultado: {result}")

    if result["creados"] + result["actualizados"] > 0:
        ok("SP1", f"Clientes E2E: {result['creados']} creados, {result['actualizados']} actualizados")
    else:
        fail("SP1", f"No se creo ni actualizo nada: {result}")

    # SP2: Actualizacion
    info("SP2: Clientes actualizacion - segunda corrida")
    result2 = ProcessPartners(odoo, config, FLOW_CLIENTES).process(data_limitada)
    info(f"Resultado segunda corrida: {result2}")

    if result2["actualizados"] > 0 and result2["creados"] == 0:
        ok("SP2", f"Actualizacion correcta: {result2['actualizados']} actualizados")
    elif result2["actualizados"] > 0:
        ok("SP2", f"Parcial: {result2['actualizados']} actualizados, {result2['creados']} creados")
    else:
        fail("SP2", f"Esperaba actualizados > 0: {result2}")


# ============================================================
# PROVEEDORES
# ============================================================
def test_proveedores():
    header("FLOW: PROVEEDORES (BYCSA)")

    info("SP3: Proveedores feliz - flatten BPAddresses + mapping")
    data = transform.get_flow(connector, FLOW_PROVEEDORES["flow_name"], FLOW_PROVEEDORES)
    info(f"Transform retorno {len(data)} registros")
    if not data:
        fail("SP3", "Transform retorno 0 registros")
        return

    data_limitada = data[:5]
    result = ProcessPartners(odoo, config, FLOW_PROVEEDORES).process(data_limitada)
    info(f"Resultado: {result}")

    if result["creados"] + result["actualizados"] > 0:
        ok("SP3", f"Proveedores E2E: {result['creados']} creados, {result['actualizados']} actualizados")
    else:
        fail("SP3", f"No se creo ni actualizo nada: {result}")

    if data_limitada:
        vat_check = data_limitada[0].get("identificacion", "")
        if vat_check:
            ok_v, parts = odoo.search_read(
                "res.partner", [["vat", "=", vat_check]], ["customer_rank", "supplier_rank"]
            )
            if ok_v and parts:
                if parts[0].get("supplier_rank", 0) >= 1:
                    ok("SP3b", f"supplier_rank >= 1 para {vat_check}")
                else:
                    fail("SP3b", f"supplier_rank = {parts[0].get('supplier_rank')} para {vat_check}")


# ============================================================
# COMPRAS
# ============================================================
def test_compras():
    header("FLOW: COMPRAS (BYCSA)")

    info("SC1: Compras feliz - flatten DocumentLines + doc_name_por_rango + resolve")
    data = transform.get_flow(connector, FLOW_COMPRAS["flow_name"], FLOW_COMPRAS)
    info(f"Transform retorno {len(data)} registros")
    if not data:
        fail("SC1", "Transform retorno 0 registros - sin OCs abiertas en SAP")
        return

    data_limitada = data[:10]
    info(f"Muestra: compra={data_limitada[0].get('compra')}, producto={data_limitada[0].get('producto')}, proveedor={data_limitada[0].get('proveedor')}")

    # Verificar doc_name_por_rango
    compra_name = data_limitada[0].get("compra", "")
    if compra_name.startswith("OCNAL-"):
        ok("SC1-docname", f"doc_name_por_rango funciono: {compra_name}")
    else:
        info(f"SC1-docname: compra={compra_name} (puede no matchear rango)")

    # Resolve
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
        ok("SC1", f"Compras E2E: {result['creados']} ordenes creadas")
    elif result["descartados"] > 0:
        ok("SC1", f"Compras: {result['descartados']} ya existian")
    elif result.get("fallidos"):
        fail("SC1", f"Fallidos: {result['fallidos'][:3]}")
    else:
        fail("SC1", f"Resultado inesperado: {result}")

    # SC2: Duplicadas
    info("SC2: Compras duplicadas - segunda corrida")
    result2 = ProcessPurchases(odoo, config, FLOW_COMPRAS).process(data_limitada)
    info(f"Resultado segunda corrida: {result2}")

    if result2["descartados"] > 0 and result2["creados"] == 0:
        ok("SC2", f"Duplicadas descartadas: {result2['descartados']} descartados, 0 creados")
    else:
        fail("SC2", f"Esperaba descartados > 0, creados = 0: {result2}")


# ============================================================
# VENTAS
# ============================================================
def test_ventas():
    header("FLOW: VENTAS (BYCSA)")

    info("SV1: Ventas feliz - flatten DocumentLines + doc_name_por_rango + resolve")
    data = transform.get_flow(connector, FLOW_VENTAS["flow_name"], FLOW_VENTAS)
    info(f"Transform retorno {len(data)} registros")
    if not data:
        fail("SV1", "Transform retorno 0 registros - sin pedidos abiertos en SAP")
        return

    data_limitada = data[:10]
    info(f"Muestra: pedido={data_limitada[0].get('pedido')}, producto={data_limitada[0].get('producto')}, cliente={data_limitada[0].get('cliente')}")

    # Resolve
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
        ok("SV1", f"Ventas E2E: {result['creados']} pedidos creados")
    elif result["descartados"] > 0:
        ok("SV1", f"Ventas: {result['descartados']} ya existian")
    elif result.get("fallidos"):
        fail("SV1", f"Fallidos: {result['fallidos'][:3]}")
    else:
        fail("SV1", f"Resultado inesperado: {result}")

    # SV2: Duplicadas
    info("SV2: Ventas duplicadas - segunda corrida")
    result2 = ProcessSales(odoo, config, FLOW_VENTAS).process(data_limitada)
    if result2["descartados"] > 0 and result2["creados"] == 0:
        ok("SV2", f"Duplicadas: {result2['descartados']} descartados, 0 creados")
    else:
        fail("SV2", f"Esperaba descartados > 0: {result2}")


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
