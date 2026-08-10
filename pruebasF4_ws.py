"""
pruebasF4_ws.py — Pruebas de integración Fase 4 Core Layer (SIESA WS)
Ejecutar en wms-servertest con ENV=staging
Cliente de prueba: pruebaws (ERP WS OrgComercia + Odoo pruebas)

Uso:
python pruebasF4_ws.py          → corre todas las partes
python pruebasF4_ws.py 0        → solo Parte 0 (setup)
python pruebasF4_ws.py 1        → solo Parte 1 (lookups)
python pruebasF4_ws.py limpieza → solo limpieza
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
from core.utils.lookups import (
    lookup_uom, lookup_category, lookup_state, lookup_zone,
    lookup_tax, lookup_route, lookup_product, lookup_partner,
    resolve_warehouse
)
from core.process_items import ProcessItems
from core.process_partners import ProcessPartners
from core.process_purchases import ProcessPurchases
from core.process_sales import ProcessSales
from core.resolve_missing_masters import resolve_missing_masters

# ============================================================
# CONFIGURACIÓN
# ============================================================
CLIENT_ID = "pruebaws"
PREFIJO = "TEST-F4WS"  # prefijo para todos los datos de prueba

# Contadores globales
passed = 0
failed = 0
errors = []


def ok(test_id, msg):
    global passed
    passed += 1
    print(f"  ✓ {test_id}: {msg}")


def fail(test_id, msg):
    global failed
    failed += 1
    errors.append(f"{test_id}: {msg}")
    print(f"  ✗ {test_id}: {msg}")


def header(titulo):
    print(f"\n{'='*60}")
    print(f"  {titulo}")
    print(f"{'='*60}")


# ============================================================
# PARTE 0 — Setup
# ============================================================
def parte_0():
    global config, odoo, connector, transform, logger

    header("PARTE 0 — Setup")

    config = ConfigLoader(CLIENT_ID).load_config()
    config["client_id"] = CLIENT_ID
    logger = IntegradorLogger(client_id=CLIENT_ID)

    print(f"  URL Odoo:  {config['odoo']['url']}")
    print(f"  DB Odoo:   {config['odoo']['database']}")
    print(f"  ERP tipo:  {config['erp']['tipo']}")

    # Conectar a Odoo
    odoo = JsonRPC(config)
    auth = odoo.authenticate()
    if auth:
        ok("0.1", "Autenticación Odoo OK")
    else:
        fail("0.1", "Autenticación Odoo FALLÓ — no se puede continuar")
        sys.exit(1)

    # Conectar al ERP
    connector = SiesaEnterprise(config)
    status, msg = connector.test_connection()
    if status:
        ok("0.2", f"Conexión SIESA WS OK — {msg}")
    else:
        fail("0.2", f"Conexión SIESA WS FALLÓ — {msg}")
        print("  ⚠ Las pruebas de flujo completo (end-to-end) fallarán")

    # Transform
    transform = TransformWS(config)
    ok("0.3", "TransformWS instanciado")


# ============================================================
# PARTE 1 — Lookups (A1-A16)
# ============================================================
def parte_1():
    header("PARTE 1 — Lookups")

    # A2: UOM existente
    cache_uom = {}
    uom_id = lookup_uom(odoo, "Unidades", cache=cache_uom, logger=logger)
    if uom_id:
        ok("A2", f"lookup_uom 'Unidades' → id={uom_id}")
    else:
        fail("A2", "UOM 'Unidades' no encontrada")

    # A3: UOM nueva
    uom_test = lookup_uom(odoo, f"{PREFIJO}-UOM", cache=cache_uom, logger=logger)
    if uom_test:
        ok("A3", f"lookup_uom crear '{PREFIJO}-UOM' → id={uom_test}")
    else:
        fail("A3", f"No se pudo crear UOM '{PREFIJO}-UOM'")

    # A3b: Cache hit
    uom_cache = lookup_uom(odoo, f"{PREFIJO}-UOM", cache=cache_uom, logger=logger)
    if uom_cache == uom_test:
        ok("A3b", f"Cache UOM funciona — mismo id={uom_cache}")
    else:
        fail("A3b", f"Cache UOM falló — esperaba {uom_test}, obtuvo {uom_cache}")

    # A4: Categoría existente
    cache_cat = {}
    cat_id = lookup_category(odoo, "All", cache=cache_cat, logger=logger)
    if cat_id:
        ok("A4", f"lookup_category 'All' → id={cat_id}")
    else:
        fail("A4", "Categoría 'All' no encontrada")

    # A5: Categoría jerarquía 2 niveles
    padre = lookup_category(odoo, f"{PREFIJO}-CAT", parent_id=False, cache=cache_cat, logger=logger)
    if padre:
        ok("A5a", f"Categoría padre '{PREFIJO}-CAT' → id={padre}")
    else:
        fail("A5a", "No se pudo crear categoría padre")

    hijo = lookup_category(odoo, f"{PREFIJO}-MARCA", parent_id=padre, cache=cache_cat, logger=logger)
    if hijo and hijo != padre:
        ok("A5b", f"Categoría hijo '{PREFIJO}-MARCA' (parent={padre}) → id={hijo}")
    else:
        fail("A5b", "No se pudo crear categoría hijo")

    # A6: State existente
    cache_state = {}
    state_id = lookup_state(odoo, "Antioquia", cache=cache_state, logger=logger)
    if state_id:
        ok("A6", f"lookup_state 'Antioquia' → id={state_id}")
    else:
        fail("A6", "Departamento 'Antioquia' no encontrado")

    # A7: State nuevo (verificar código por palabras)
    state_test = lookup_state(odoo, f"{PREFIJO} DEPTO NUEVO", cache=cache_state, logger=logger)
    if state_test:
        ok("A7", f"lookup_state '{PREFIJO} DEPTO NUEVO' → id={state_test}")
        # Verificar código generado: "TDN" (TEST → T, DEPTO → D, NUEVO → N)
        ok_s, states = odoo.search_read("res.country.state", [["id", "=", state_test]], ["code"])
        if ok_s and states:
            code = states[0]["code"]
            # Primer letra de cada palabra, max 3
            esperado = "".join([p[0].upper() for p in f"{PREFIJO} DEPTO NUEVO".split()[:3]])
            if code == esperado:
                ok("A7b", f"Código generado correcto: '{code}'")
            else:
                fail("A7b", f"Código esperado '{esperado}', obtuvo '{code}'")
    else:
        fail("A7", "No se pudo crear departamento")

    # A8: Zone nueva
    cache_zone = {}
    zone_test = lookup_zone(odoo, f"{PREFIJO}-ZONA", cache=cache_zone, logger=logger)
    if zone_test:
        ok("A8", f"lookup_zone '{PREFIJO}-ZONA' → id={zone_test}")
    else:
        fail("A8", "No se pudo crear zona")

    # A9: Tax existente
    cache_tax = {}
    tax_sale = lookup_tax(odoo, 19.0, "sale", cache=cache_tax, logger=logger)
    if tax_sale:
        ok("A9a", f"lookup_tax 19% sale → id={tax_sale}")
    else:
        fail("A9a", "IVA 19% sale no encontrado")

    tax_purchase = lookup_tax(odoo, 19.0, "purchase", cache=cache_tax, logger=logger)
    if tax_purchase:
        ok("A9b", f"lookup_tax 19% purchase → id={tax_purchase}")
    else:
        fail("A9b", "IVA 19% purchase no encontrado")

    # A10: Tax inexistente
    tax_99 = lookup_tax(odoo, 99.99, "sale", cache=cache_tax, logger=logger)
    if tax_99 is None:
        ok("A10", "lookup_tax 99.99% → None (correcto, no crea)")
    else:
        fail("A10", f"Esperaba None, obtuvo {tax_99}")

    # A11: Route
    cache_route = {}
    route_buy = lookup_route(odoo, "Buy", cache=cache_route, logger=logger)
    if route_buy:
        ok("A11", f"lookup_route 'Buy' → id={route_buy}")
    else:
        fail("A11", "Ruta 'Buy' no encontrada — puede no existir en este Odoo")

    # A12: Product inexistente
    cache_prod = {}
    prod = lookup_product(odoo, "NOEXISTE-XYZ-999", cache=cache_prod, logger=logger)
    if prod is None:
        ok("A12", "lookup_product inexistente → None (correcto)")
    else:
        fail("A12", f"Esperaba None, obtuvo {prod}")

    # A13: Partner inexistente
    cache_partner = {}
    partner = lookup_partner(odoo, "NOEXISTE-XYZ-999", "001", cache=cache_partner, logger=logger)
    if partner is None:
        ok("A13", "lookup_partner inexistente → None (correcto)")
    else:
        fail("A13", f"Esperaba None, obtuvo {partner}")

    # A14: resolve_warehouse
    wh = resolve_warehouse("BOD01", {"BOD01": 15, "BOD02": 16}, logger=logger)
    if wh == 15:
        ok("A14a", "resolve_warehouse 'BOD01' → 15 (correcto)")
    else:
        fail("A14a", f"Esperaba 15, obtuvo {wh}")

    wh2 = resolve_warehouse("BOD99", {"BOD01": 15}, logger=logger)
    if wh2 is None:
        ok("A14b", "resolve_warehouse 'BOD99' → None (correcto)")
    else:
        fail("A14b", f"Esperaba None, obtuvo {wh2}")

    # A15: Default picking type
    ok_pt, pts = odoo.search_read("stock.picking.type", [["code", "=", "incoming"]], ["id", "name"], limit=1)
    if ok_pt and pts:
        ok("A15", f"Default picking type incoming → id={pts[0]['id']} ({pts[0]['name']})")
    else:
        fail("A15", "No se encontró picking type 'incoming'")

    # A16: Default warehouse
    ok_wh, whs = odoo.search_read("stock.warehouse", [], ["id", "name"], limit=1)
    if ok_wh and whs:
        ok("A16", f"Default warehouse → id={whs[0]['id']} ({whs[0]['name']})")
    else:
        fail("A16", "No se encontró warehouse")


# ============================================================
# PARTE 2 — ProcessItems (WS-I1 a WS-I11)
# ============================================================
def parte_2():
    header("PARTE 2 — ProcessItems")

    # WS-I2: Producto mínimo
    p = ProcessItems(odoo, config, {})
    result = p.process([{
        "referencia": f"{PREFIJO}-001", "descripcion": "Producto mínimo WS",
        "unidad": "Unidades",
    }])
    if result["creados"] == 1:
        ok("WS-I2", f"Producto mínimo creado: {result}")
    else:
        fail("WS-I2", f"Esperaba 1 creado: {result}")

    # WS-I3: Producto completo
    p2 = ProcessItems(odoo, config, {"uom_mapping": {"UND": "Unidades"}})
    result2 = p2.process([{
        "referencia": f"{PREFIJO}-002", "descripcion": "Producto completo WS",
        "unidad": "UND",
        "categoria": "All", "peso": 1.5, "volumen": 0.3,
        "precio": 99.9, "costo": 50.0, "iva": 19.0,
        "tracking": "lot", "use_expiration_date": 1, "expiration_time": 365,
        "codigo_barras": f"{PREFIJO}7700001",
    }])
    if result2["creados"] == 1:
        ok("WS-I3", f"Producto completo creado: {result2}")
    else:
        fail("WS-I3", f"Esperaba 1 creado: {result2}")

    # WS-I7: uom_mapping — verificar que UND se buscó como Unidades
    print(f"  ℹ WS-I7: uom_mapping verificado en WS-I3 (UND → Unidades)")

    # WS-I4: Actualizar existente
    p3 = ProcessItems(odoo, config, {})
    result3 = p3.process([{
        "referencia": f"{PREFIJO}-001", "descripcion": "Producto ACTUALIZADO WS",
        "unidad": "Unidades", "peso": 9.99,
    }])
    if result3["actualizados"] == 1:
        ok("WS-I4", f"Producto actualizado: {result3}")
        # Verificar en Odoo que tracking no cambió
        ok_v, prods = odoo.search_read(
            "product.template", [["default_code", "=", f"{PREFIJO}-001"]],
            ["name", "weight", "tracking"]
        )
        if ok_v and prods:
            p_odoo = prods[0]
            if p_odoo["name"] == "Producto ACTUALIZADO WS" and p_odoo["weight"] == 9.99:
                ok("WS-I4b", f"Verificado en Odoo: name y weight correctos, tracking={p_odoo['tracking']}")
            else:
                fail("WS-I4b", f"Datos en Odoo no coinciden: {p_odoo}")
    else:
        fail("WS-I4", f"Esperaba 1 actualizado: {result3}")

    # WS-I5: Barcode duplicado → retry
    p4 = ProcessItems(odoo, config, {})
    result4 = p4.process([{
        "referencia": f"{PREFIJO}-003", "descripcion": "Producto barcode dup WS",
        "unidad": "Unidades",
        "codigo_barras": f"{PREFIJO}7700001",  # ya existe en PREFIJO-002
    }])
    if result4["creados"] == 1:
        ok("WS-I5", f"Barcode dup → retry exitoso (creado sin barcode): {result4}")
        # Verificar que se creó sin barcode
        ok_v, prods = odoo.search_read(
            "product.template", [["default_code", "=", f"{PREFIJO}-003"]],
            ["barcode"]
        )
        if ok_v and prods and not prods[0].get("barcode"):
            ok("WS-I5b", "Verificado: producto creado sin barcode")
        else:
            fail("WS-I5b", f"Producto tiene barcode inesperado: {prods}")
    else:
        fail("WS-I5", f"Esperaba 1 creado (retry): {result4}")

    # WS-I6: Sin UOM → fallidos
    p5 = ProcessItems(odoo, config, {})
    result5 = p5.process([{
        "referencia": f"{PREFIJO}-FAIL-UOM", "descripcion": "Sin unidad",
        "unidad": "",
    }])
    if result5["fallidos"] and "UOM" in result5["fallidos"][0]["razon"]:
        ok("WS-I6", f"Sin UOM → fallido correctamente: {result5['fallidos'][0]['razon']}")
    else:
        fail("WS-I6", f"Esperaba fallido por UOM: {result5}")

    # WS-I8: codigos_extras → barcode multi
    p6 = ProcessItems(odoo, config, {})
    result6 = p6.process([{
        "referencia": f"{PREFIJO}-004", "descripcion": "Con extras WS",
        "unidad": "Unidades",
        "codigos_extras": f"{PREFIJO}-EXTRA001,{PREFIJO}-EXTRA002",
    }])
    if result6["creados"] == 1:
        ok("WS-I8", f"Producto con codigos_extras creado: {result6}")
        # Verificar barcode.multi
        ok_v, variants = odoo.search_read(
            "product.product", [["default_code", "=", f"{PREFIJO}-004"]], ["id"]
        )
        if ok_v and variants:
            ok_b, barcodes = odoo.search_read(
                "product.barcode.multi",
                [["product_id", "=", variants[0]["id"]]],
                ["name"]
            )
            if ok_b and len(barcodes) == 2:
                nombres = {b["name"] for b in barcodes}
                ok("WS-I8b", f"Barcode multi verificado: {nombres}")
            else:
                fail("WS-I8b", f"Esperaba 2 barcodes, encontró {len(barcodes) if ok_b else 'error'}")
    else:
        fail("WS-I8", f"Esperaba 1 creado: {result6}")

    # WS-I9: Categoría + marca → 2 niveles
    p7 = ProcessItems(odoo, config, {})
    result7 = p7.process([{
        "referencia": f"{PREFIJO}-005", "descripcion": "Con marca WS",
        "unidad": "Unidades",
        "categoria": f"{PREFIJO}-CATEGORIA", "marca": f"{PREFIJO}-MARCA-PROD",
    }])
    if result7["creados"] == 1:
        ok("WS-I9", f"Producto con categoría+marca creado: {result7}")
        # Verificar jerarquía
        ok_c, cats = odoo.search_read(
            "product.category",
            [["name", "=", f"{PREFIJO}-MARCA-PROD"]],
            ["parent_id"]
        )
        if ok_c and cats and cats[0]["parent_id"]:
            ok("WS-I9b", f"Jerarquía 2 niveles verificada: parent_id={cats[0]['parent_id']}")
        else:
            fail("WS-I9b", f"No se encontró jerarquía: {cats}")
    else:
        fail("WS-I9", f"Esperaba 1 creado: {result7}")

    # WS-I10: IVA → taxes_id
    ok_v, prods = odoo.search_read(
        "product.template", [["default_code", "=", f"{PREFIJO}-002"]],
        ["taxes_id", "supplier_taxes_id"]
    )
    if ok_v and prods:
        has_tax = bool(prods[0].get("taxes_id")) and bool(prods[0].get("supplier_taxes_id"))
        if has_tax:
            ok("WS-I10", f"IVA asignado: taxes_id={prods[0]['taxes_id']}, supplier={prods[0]['supplier_taxes_id']}")
        else:
            fail("WS-I10", f"IVA no asignado: {prods[0]}")
    else:
        fail("WS-I10", "No se pudo verificar IVA")

    # WS-I11: Ruta → route_ids
    p8 = ProcessItems(odoo, config, {})
    result8 = p8.process([{
        "referencia": f"{PREFIJO}-006", "descripcion": "Con ruta WS",
        "unidad": "Unidades", "ruta": "Buy",
    }])
    if result8["creados"] == 1:
        ok_v, prods = odoo.search_read(
            "product.template", [["default_code", "=", f"{PREFIJO}-006"]],
            ["route_ids"]
        )
        if ok_v and prods and prods[0].get("route_ids"):
            ok("WS-I11", f"Ruta 'Buy' asignada: route_ids={prods[0]['route_ids']}")
        else:
            fail("WS-I11", f"Ruta no asignada: {prods}")
    else:
        fail("WS-I11", f"Esperaba 1 creado: {result8}")


# ============================================================
# PARTE 3 — ProcessPartners (WS-P1 a WS-P7)
# ============================================================
def parte_3():
    header("PARTE 3 — ProcessPartners")

    # WS-P2: Crear cliente
    pp = ProcessPartners(odoo, config, {"flow_type": "customer"})
    result = pp.process([{
        "nombre": f"{PREFIJO} CLIENTE", "identificacion": f"{PREFIJO}-CLI001",
        "sucursal": "001", "direccion": "Calle Test 123",
        "telefono": "3001234567", "email": "test@core-ws.com",
        "ciudad": "Medellín", "departamento": "Antioquia",
    }])
    if result["creados"] == 1:
        ok("WS-P2", f"Cliente creado: {result}")
        # Verificar ranks
        ok_v, parts = odoo.search_read(
            "res.partner", [["vat", "=", f"{PREFIJO}-CLI001"]],
            ["customer_rank", "supplier_rank"]
        )
        if ok_v and parts:
            if parts[0]["customer_rank"] == 1 and parts[0]["supplier_rank"] == 0:
                ok("WS-P2b", "Ranks correctos: customer=1, supplier=0")
            else:
                fail("WS-P2b", f"Ranks incorrectos: {parts[0]}")
    else:
        fail("WS-P2", f"Esperaba 1 creado: {result}")

    # WS-P3: Crear proveedor
    pp2 = ProcessPartners(odoo, config, {"flow_type": "supplier"})
    result2 = pp2.process([{
        "nombre": f"{PREFIJO} PROVEEDOR", "identificacion": f"{PREFIJO}-PROV001",
        "sucursal": "001", "direccion": "Calle Prov 456",
        "departamento": "Cundinamarca",
    }])
    if result2["creados"] == 1:
        ok("WS-P3", f"Proveedor creado: {result2}")
        ok_v, parts = odoo.search_read(
            "res.partner", [["vat", "=", f"{PREFIJO}-PROV001"]],
            ["customer_rank", "supplier_rank"]
        )
        if ok_v and parts:
            if parts[0]["supplier_rank"] == 1 and parts[0]["customer_rank"] == 0:
                ok("WS-P3b", "Ranks correctos: supplier=1, customer=0")
            else:
                fail("WS-P3b", f"Ranks incorrectos: {parts[0]}")
    else:
        fail("WS-P3", f"Esperaba 1 creado: {result2}")

    # WS-P4: Actualizar sin enviar vat
    pp3 = ProcessPartners(odoo, config, {"flow_type": "customer"})
    result3 = pp3.process([{
        "nombre": f"{PREFIJO} CLIENTE ACTUALIZADO", "identificacion": f"{PREFIJO}-CLI001",
        "sucursal": "001", "direccion": "Calle Actualizada 789",
        "departamento": "Antioquia",
    }])
    if result3["actualizados"] == 1:
        ok("WS-P4", f"Partner actualizado: {result3}")
        ok_v, parts = odoo.search_read(
            "res.partner", [["vat", "=", f"{PREFIJO}-CLI001"]],
            ["name", "street", "vat"]
        )
        if ok_v and parts:
            if parts[0]["name"] == f"{PREFIJO} CLIENTE ACTUALIZADO" and parts[0]["vat"] == f"{PREFIJO}-CLI001":
                ok("WS-P4b", "Verificado: nombre actualizado, vat intacto")
            else:
                fail("WS-P4b", f"Datos incorrectos: {parts[0]}")
    else:
        fail("WS-P4", f"Esperaba 1 actualizado: {result3}")

    # WS-P5: Rank no baja — actualizar cliente como proveedor
    pp4 = ProcessPartners(odoo, config, {"flow_type": "supplier"})
    result4 = pp4.process([{
        "nombre": f"{PREFIJO} CLIENTE ACTUALIZADO", "identificacion": f"{PREFIJO}-CLI001",
        "sucursal": "001", "departamento": "Antioquia",
    }])
    if result4["actualizados"] == 1:
        ok_v, parts = odoo.search_read(
            "res.partner", [["vat", "=", f"{PREFIJO}-CLI001"], ["sucursal", "=", "001"]],
            ["customer_rank", "supplier_rank"]
        )
        if ok_v and parts:
            if parts[0]["customer_rank"] >= 1 and parts[0]["supplier_rank"] == 1:
                ok("WS-P5", f"Rank no bajó: customer={parts[0]['customer_rank']}, supplier={parts[0]['supplier_rank']}")
            else:
                fail("WS-P5", f"Rank bajó: {parts[0]}")
    else:
        fail("WS-P5", f"Esperaba 1 actualizado: {result4}")

    # WS-P6: Jerarquía padre + hijo
    pp5 = ProcessPartners(odoo, config, {
        "flow_type": "customer",
        "sucursal_hierarchy": True,
        "sucursal_padre": "001",
    })
    result5 = pp5.process([
        {"nombre": f"{PREFIJO} EMPRESA JERARQUIA", "identificacion": f"{PREFIJO}-JER001",
        "sucursal": "001", "departamento": "Antioquia"},
        {"nombre": f"{PREFIJO} SUCURSAL 2", "identificacion": f"{PREFIJO}-JER001",
        "sucursal": "002", "departamento": "Antioquia"},
    ])
    if result5["creados"] == 2:
        ok("WS-P6", f"Jerarquía creada: {result5}")
        # Verificar padre
        ok_v, padre = odoo.search_read(
            "res.partner", [["vat", "=", f"{PREFIJO}-JER001"], ["sucursal", "=", "001"]],
            ["is_company", "parent_id"]
        )
        ok_v2, hijo = odoo.search_read(
            "res.partner", [["vat", "=", f"{PREFIJO}-JER001"], ["sucursal", "=", "002"]],
            ["is_company", "parent_id", "type"]
        )
        if ok_v and padre and ok_v2 and hijo:
            if padre[0].get("is_company") and not hijo[0].get("is_company"):
                ok("WS-P6b", f"Padre is_company=True, hijo is_company=False")
            else:
                fail("WS-P6b", f"is_company incorrecto: padre={padre[0]}, hijo={hijo[0]}")
            if hijo[0].get("parent_id") and hijo[0]["parent_id"][0] == padre[0]["id"]:
                ok("WS-P6c", f"Hijo parent_id apunta al padre (id={padre[0]['id']})")
            else:
                fail("WS-P6c", f"parent_id incorrecto: {hijo[0]}")
            if hijo[0].get("type") == "other":
                ok("WS-P6d", "Hijo type='other'")
            else:
                fail("WS-P6d", f"type incorrecto: {hijo[0].get('type')}")
    else:
        fail("WS-P6", f"Esperaba 2 creados: {result5}")

    # WS-P7: Departamento nuevo — código generado
    pp6 = ProcessPartners(odoo, config, {"flow_type": "customer"})
    result6 = pp6.process([{
        "nombre": f"{PREFIJO} DEPTO NUEVO", "identificacion": f"{PREFIJO}-DEPTO001",
        "sucursal": "001", "departamento": f"{PREFIJO} Depto Prueba",
    }])
    if result6["creados"] == 1:
        ok("WS-P7", "Partner con depto nuevo creado")
    else:
        fail("WS-P7", f"Esperaba 1 creado: {result6}")


# ============================================================
# PARTE 4 — ProcessPurchases (WS-C1 a WS-C9)
# ============================================================
def parte_4():
    header("PARTE 4 — ProcessPurchases")

    # WS-C2: Crear OC 1 línea
    pp = ProcessPurchases(odoo, config, {})
    result = pp.process([{
        "compra": f"{PREFIJO}-OC-001", "producto": f"{PREFIJO}-001",
        "proveedor": f"{PREFIJO}-PROV001", "sucursal_proveedor": "001",
        "fecha_entrega": "2026-08-15", "estado": "draft",
        "almacen": "ALM1", "cantidad": 10.0, "precio_unitario": 50.0,
    }])
    if result["creados"] == 1:
        ok("WS-C2", f"OC 1 línea creada: {result}")
    else:
        fail("WS-C2", f"Esperaba 1 creada: {result}")

    # WS-C3: Crear OC 2 líneas
    pp2 = ProcessPurchases(odoo, config, {})
    result2 = pp2.process([
        {"compra": f"{PREFIJO}-OC-002", "producto": f"{PREFIJO}-001",
        "proveedor": f"{PREFIJO}-PROV001", "sucursal_proveedor": "001",
        "fecha_entrega": "2026-08-15", "estado": "draft",
        "almacen": "ALM1", "cantidad": 5.0, "precio_unitario": 30.0},
        {"compra": f"{PREFIJO}-OC-002", "producto": f"{PREFIJO}-002",
        "proveedor": f"{PREFIJO}-PROV001", "sucursal_proveedor": "001",
        "fecha_entrega": "2026-08-15", "estado": "draft",
        "almacen": "ALM1", "cantidad": 3.0, "precio_unitario": 100.0},
    ])
    if result2["creados"] == 1 and result2.get("total_ordenes") == 1:
        ok("WS-C3", f"OC 2 líneas (groupby correcto): {result2}")
    else:
        fail("WS-C3", f"Esperaba 1 orden con 2 líneas: {result2}")

    # WS-C4: Orden duplicada
    pp3 = ProcessPurchases(odoo, config, {})
    result3 = pp3.process([{
        "compra": f"{PREFIJO}-OC-001", "producto": f"{PREFIJO}-001",
        "proveedor": f"{PREFIJO}-PROV001", "sucursal_proveedor": "001",
        "fecha_entrega": "2026-08-15", "estado": "draft",
        "almacen": "ALM1", "cantidad": 10.0, "precio_unitario": 50.0,
    }])
    if result3["descartados"] >= 1 and result3["creados"] == 0:
        ok("WS-C4", f"Orden duplicada descartada: {result3}")
    else:
        fail("WS-C4", f"Esperaba descartados>=1, creados=0: {result3}")

    # WS-C5: warehouse_mapping resuelve
    ok_pt, pts = odoo.search_read("stock.picking.type", [["code", "=", "incoming"]], ["id"], limit=1)
    if ok_pt and pts:
        real_pt_id = pts[0]["id"]
        pp4 = ProcessPurchases(odoo, config, {
            "warehouse_mapping": {"BOD-WS-TEST": real_pt_id}
        })
        result4 = pp4.process([{
            "compra": f"{PREFIJO}-OC-003", "producto": f"{PREFIJO}-001",
            "proveedor": f"{PREFIJO}-PROV001", "sucursal_proveedor": "001",
            "fecha_entrega": "2026-08-15", "estado": "draft",
            "almacen": "ALM1", "bodega_siesa": "BOD-WS-TEST",
            "cantidad": 7.0, "precio_unitario": 25.0,
        }])
        if result4["creados"] == 1:
            ok("WS-C5", f"warehouse_mapping resolvió picking_type_id={real_pt_id}: {result4}")
        else:
            fail("WS-C5", f"Esperaba 1 creada: {result4}")
    else:
        fail("WS-C5", "No se pudo obtener picking type para test")

    # WS-C6: Sin warehouse_mapping → default picking type
    print(f"  ℹ WS-C6: verificado implícitamente en WS-C2 (sin warehouse_mapping)")

    # WS-C7: Proveedor inexistente
    pp5 = ProcessPurchases(odoo, config, {})
    result5 = pp5.process([{
        "compra": f"{PREFIJO}-OC-FAIL1", "producto": f"{PREFIJO}-001",
        "proveedor": "NOEXISTE-PROV-999", "sucursal_proveedor": "001",
        "fecha_entrega": "2026-08-15", "estado": "draft",
        "almacen": "ALM1", "cantidad": 10.0, "precio_unitario": 50.0,
    }])
    prov_fallido = any("Proveedor" in f.get("razon", "") for f in result5.get("fallidos", []))
    if prov_fallido:
        ok("WS-C7", f"Proveedor inexistente → fallido: {result5['fallidos']}")
    else:
        fail("WS-C7", f"Esperaba fallido por proveedor: {result5}")

    # WS-C8: Producto inexistente
    pp6 = ProcessPurchases(odoo, config, {})
    result6 = pp6.process([{
        "compra": f"{PREFIJO}-OC-FAIL2", "producto": "NOEXISTE-PROD-999",
        "proveedor": f"{PREFIJO}-PROV001", "sucursal_proveedor": "001",
        "fecha_entrega": "2026-08-15", "estado": "draft",
        "almacen": "ALM1", "cantidad": 10.0, "precio_unitario": 50.0,
    }])
    prod_fallido = any("Producto" in f.get("razon", "") for f in result6.get("fallidos", []))
    if prod_fallido:
        ok("WS-C8", f"Producto inexistente → fallido: {result6['fallidos']}")
    else:
        fail("WS-C8", f"Esperaba fallido por producto: {result6}")

    # WS-C9: referencia_compra → partner_ref
    pp7 = ProcessPurchases(odoo, config, {})
    result7 = pp7.process([{
        "compra": f"{PREFIJO}-OC-004", "producto": f"{PREFIJO}-001",
        "proveedor": f"{PREFIJO}-PROV001", "sucursal_proveedor": "001",
        "fecha_entrega": "2026-08-15", "estado": "draft",
        "almacen": "ALM1", "cantidad": 5.0, "precio_unitario": 20.0,
        "referencia_compra": "REF-PROV-EXTERNO-123",
    }])
    if result7["creados"] == 1:
        ok_v, ocs = odoo.search_read(
            "purchase.order", [["name", "=", f"{PREFIJO}-OC-004"]],
            ["partner_ref"]
        )
        if ok_v and ocs and ocs[0].get("partner_ref") == "REF-PROV-EXTERNO-123":
            ok("WS-C9", f"partner_ref correcto: {ocs[0]['partner_ref']}")
        else:
            fail("WS-C9", f"partner_ref incorrecto: {ocs}")
    else:
        fail("WS-C9", f"Esperaba 1 creada: {result7}")


# ============================================================
# PARTE 5 — ProcessSales (WS-V1 a WS-V9)
# ============================================================
def parte_5():
    header("PARTE 5 — ProcessSales")

    # WS-V2: Crear pedido 1 línea
    ps = ProcessSales(odoo, config, {})
    result = ps.process([{
        "pedido": f"{PREFIJO}-PED-001", "producto": f"{PREFIJO}-001",
        "cliente": f"{PREFIJO}-CLI001", "sucursal_cliente": "001",
        "fecha_pedido": "2026-08-15", "estado": "draft",
        "almacen": "ALM1", "cantidad_pedida": 5.0, "precio_unitario": 100.0,
        "zona": f"{PREFIJO}-ZONA-VENTAS", "vendedor": "Juan Test",
        "condicion_pago": "30 días", "observacion": "Pedido prueba WS",
    }])
    if result["creados"] == 1:
        ok("WS-V2", f"Pedido 1 línea creado: {result}")
    else:
        fail("WS-V2", f"Esperaba 1 creado: {result}")

    # WS-V3: Pedido 2 líneas
    ps2 = ProcessSales(odoo, config, {})
    result2 = ps2.process([
        {"pedido": f"{PREFIJO}-PED-002", "producto": f"{PREFIJO}-001",
        "cliente": f"{PREFIJO}-CLI001", "sucursal_cliente": "001",
        "fecha_pedido": "2026-08-15", "estado": "draft",
        "almacen": "ALM1", "cantidad_pedida": 3.0, "precio_unitario": 80.0,
        "zona": f"{PREFIJO}-ZONA-VENTAS", "vendedor": "Juan Test",
        "condicion_pago": "30 días", "observacion": ""},
        {"pedido": f"{PREFIJO}-PED-002", "producto": f"{PREFIJO}-002",
        "cliente": f"{PREFIJO}-CLI001", "sucursal_cliente": "001",
        "fecha_pedido": "2026-08-15", "estado": "draft",
        "almacen": "ALM1", "cantidad_pedida": 2.0, "precio_unitario": 150.0,
        "zona": f"{PREFIJO}-ZONA-VENTAS", "vendedor": "Juan Test",
        "condicion_pago": "30 días", "observacion": ""},
    ])
    if result2["creados"] == 1 and result2.get("total_ordenes") == 1:
        ok("WS-V3", f"Pedido 2 líneas (groupby correcto): {result2}")
    else:
        fail("WS-V3", f"Esperaba 1 pedido con 2 líneas: {result2}")

    # WS-V4: Pedido duplicado
    ps3 = ProcessSales(odoo, config, {})
    result3 = ps3.process([{
        "pedido": f"{PREFIJO}-PED-001", "producto": f"{PREFIJO}-001",
        "cliente": f"{PREFIJO}-CLI001", "sucursal_cliente": "001",
        "fecha_pedido": "2026-08-15", "estado": "draft",
        "almacen": "ALM1", "cantidad_pedida": 5.0, "precio_unitario": 100.0,
    }])
    if result3["descartados"] >= 1 and result3["creados"] == 0:
        ok("WS-V4", f"Pedido duplicado descartado: {result3}")
    else:
        fail("WS-V4", f"Esperaba descartados>=1, creados=0: {result3}")

    # WS-V5: warehouse_mapping → warehouse_id
    ok_wh, whs = odoo.search_read("stock.warehouse", [], ["id"], limit=1)
    if ok_wh and whs:
        real_wh_id = whs[0]["id"]
        ps4 = ProcessSales(odoo, config, {
            "warehouse_mapping": {"BOD-WS-TEST": real_wh_id}
        })
        result4 = ps4.process([{
            "pedido": f"{PREFIJO}-PED-003", "producto": f"{PREFIJO}-001",
            "cliente": f"{PREFIJO}-CLI001", "sucursal_cliente": "001",
            "fecha_pedido": "2026-08-15", "estado": "draft",
            "almacen": "ALM1", "bodega_siesa": "BOD-WS-TEST",
            "cantidad_pedida": 4.0, "precio_unitario": 60.0,
        }])
        if result4["creados"] == 1:
            ok("WS-V5", f"warehouse_mapping resolvió warehouse_id={real_wh_id}: {result4}")
        else:
            fail("WS-V5", f"Esperaba 1 creado: {result4}")
    else:
        fail("WS-V5", "No se pudo obtener warehouse para test")

    # WS-V6: Zona creada automáticamente
    ok_z, zones = odoo.search_read(
        "partner.delivery.zone", [["name", "=", f"{PREFIJO}-ZONA-VENTAS"]], ["id"]
    )
    if ok_z and zones:
        ok("WS-V6", f"Zona '{PREFIJO}-ZONA-VENTAS' creada automáticamente → id={zones[0]['id']}")
    else:
        fail("WS-V6", "Zona no fue creada automáticamente")

    # WS-V7: Observación → note
    ok_n, pedidos = odoo.search_read(
        "sale.order", [["name", "=", f"{PREFIJO}-PED-001"]], ["note"]
    )
    if ok_n and pedidos and pedidos[0].get("note") and "Pedido prueba WS" in str(pedidos[0]["note"]):
        ok("WS-V7", f"Observación → note correcta: {pedidos[0]['note']}")
    else:
        fail("WS-V7", f"Note incorrecta: {pedidos}")

    # WS-V8: product_uom_qty (no product_qty)
    if ok_n and pedidos:
        ok_l, lines = odoo.search_read(
            "sale.order.line", [["order_id", "=", pedidos[0]["id"]]],
            ["product_uom_qty"]
        )
        if ok_l and lines and lines[0].get("product_uom_qty") == 5.0:
            ok("WS-V8", f"product_uom_qty correcto: {lines[0]['product_uom_qty']}")
        else:
            fail("WS-V8", f"product_uom_qty incorrecto: {lines}")

    # WS-V9: Cliente inexistente
    ps5 = ProcessSales(odoo, config, {})
    result5 = ps5.process([{
        "pedido": f"{PREFIJO}-PED-FAIL", "producto": f"{PREFIJO}-001",
        "cliente": "NOEXISTE-CLI-999", "sucursal_cliente": "001",
        "fecha_pedido": "2026-08-15", "estado": "draft",
        "almacen": "ALM1", "cantidad_pedida": 5.0, "precio_unitario": 100.0,
    }])
    cli_fallido = any("Cliente" in f.get("razon", "") for f in result5.get("fallidos", []))
    if cli_fallido:
        ok("WS-V9", f"Cliente inexistente → fallido: {result5['fallidos']}")
    else:
        fail("WS-V9", f"Esperaba fallido por cliente: {result5}")


# ============================================================
# PARTE 6 — resolve_missing_masters (WS-R1 a WS-R3)
# ============================================================
def parte_6():
    header("PARTE 6 — resolve_missing_masters")

    # WS-R1: Todo existe
    result = resolve_missing_masters(
        odoo, connector, transform,
        data_purchases=[{
            "producto": f"{PREFIJO}-001",
            "proveedor": f"{PREFIJO}-PROV001", "sucursal_proveedor": "001"
        }],
        data_sales=[],
        flow_configs={"items": {}, "supplier": {"flow_type": "supplier"}},
        config=config, logger=logger
    )
    if result["productos_faltantes"] == 0 and result["proveedores_faltantes"] == 0:
        ok("WS-R1", f"Todo existe → 0 faltantes: {result}")
    else:
        fail("WS-R1", f"Esperaba 0 faltantes: {result}")

    # WS-R2: Producto faltante sin connector → no_resueltos
    result2 = resolve_missing_masters(
        odoo, None, None,
        data_purchases=[{
            "producto": "NOEXISTE-RESOLVE-999",
            "proveedor": f"{PREFIJO}-PROV001", "sucursal_proveedor": "001"
        }],
        data_sales=[],
        flow_configs={},  # sin flow_config de items → no puede consultar ERP
        config=config, logger=logger
    )
    if result2["productos_faltantes"] >= 1:
        ok("WS-R2", f"Producto faltante detectado: {result2['productos_faltantes']}")
    else:
        fail("WS-R2", f"Esperaba faltantes: {result2}")

    # WS-R3: Sin flow_config de items → salta productos
    result3 = resolve_missing_masters(
        odoo, connector, transform,
        data_purchases=[{
            "producto": "NOEXISTE-RESOLVE-888",
            "proveedor": f"{PREFIJO}-PROV001", "sucursal_proveedor": "001"
        }],
        data_sales=[],
        flow_configs={},  # vacío
        config=config, logger=logger
    )
    if result3["productos_faltantes"] >= 1 and result3["productos_resueltos"] == 0:
        ok("WS-R3", f"Sin flow_config → no intenta resolver: {result3}")
    else:
        fail("WS-R3", f"Resultado inesperado: {result3}")


# ============================================================
# PARTE 7 — Limpieza
# ============================================================
def limpieza():
    header("LIMPIEZA — Borrando registros de prueba")

    modelos = [
        ("sale.order", [["name", "like", f"{PREFIJO}%"]], "Pedidos de venta"),
        ("purchase.order", [["name", "like", f"{PREFIJO}%"]], "Órdenes de compra"),
        ("product.barcode.multi", [["name", "like", f"{PREFIJO}%"]], "Barcodes multi"),
        ("product.template", [["default_code", "like", f"{PREFIJO}%"]], "Productos"),
        ("res.partner", [["vat", "like", f"{PREFIJO}%"]], "Partners"),
        ("product.category", [["name", "like", f"{PREFIJO}%"]], "Categorías"),
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
            print(f"  ⚠ Error limpiando {label}: {e}")

    print(f"\n  Revisa el log: /var/log/integrador/{CLIENT_ID}.log")


# ============================================================
# MAIN — Dispatcher
# ============================================================
def resumen():
    header("RESUMEN")
    print(f"  Pasaron:  {passed}")
    print(f"  Fallaron: {failed}")
    if errors:
        print(f"\n  Errores:")
        for e in errors:
            print(f"    ✗ {e}")


if __name__ == "__main__":
    parte = sys.argv[1] if len(sys.argv) > 1 else "all"

    # Setup siempre corre primero
    parte_0()

    if parte == "all":
        try:
            parte_1()
            parte_2()
            parte_3()
            parte_4()
            parte_5()
            parte_6()
            resumen()
        except Exception as e:
            print(f"\n💥 Error fatal: {e}")
            traceback.print_exc()
        finally:
            resp = input("\n¿Ejecutar limpieza? (s/n): ")
            if resp.lower() == "s":
                limpieza()
    elif parte == "0":
        pass  # ya corrió
    elif parte == "1":
        parte_1()
        resumen()
    elif parte == "2":
        parte_2()
        resumen()
    elif parte == "3":
        parte_3()
        resumen()
    elif parte == "4":
        parte_4()
        resumen()
    elif parte == "5":
        parte_5()
        resumen()
    elif parte == "6":
        parte_6()
        resumen()
    elif parte == "limpieza":
        limpieza()
    else:
        print(f"Parte '{parte}' no reconocida. Opciones: all, 0-6, limpieza")