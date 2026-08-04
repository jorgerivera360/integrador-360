"""
Lookups compartidos del core — funciones puras con cache opcional
Todas reciben odoo (JsonRPC) como primer parámetro.
El caller mantiene los dicts de cache durante el procesamiento.
Fase: 4 — Core Layer
"""


def lookup_uom(odoo, name, cache=None, logger=None):
    """Busca UOM por nombre, crea si no existe. Retorna id o None."""
    if not name:
        return None
    if cache is not None and name in cache:
        return cache[name]

    ok, result = odoo.search_read("uom.uom", [["name", "=", name]], ["id"], limit=1)
    if not ok:
        if logger:
            logger.error(f"lookup_uom: error buEsscando '{name}': {result}")
        return None

    if result:
        uom_id = result[0]["id"]
    else:
        ok_c, uom_id = odoo.create("uom.uom", {
            "name": name, "category_id": 1, "uom_type": "bigger"
        })
        if not ok_c:
            if logger:
                logger.warning(f"lookup_uom: no se pudo crear '{name}': {uom_id}")
            return None
        if logger:
            logger.info(f"lookup_uom: creada '{name}' → {uom_id}")

    if cache is not None:
        cache[name] = uom_id
    return uom_id

def lookup_category(odoo, name, parent_id=None, cache=None, logger=None):
    """
    Busca categoría por nombre, crea si no existe. Retorna id o None.
    parent_id=None  → sin filtro de padre (1 nivel)
    parent_id=False → solo raíz (2 niveles, buscar padre)
    parent_id=<int> → hijo de esa categoría (2 niveles, buscar marca)
    """
    if not name:
        return None
    key = (name, parent_id)
    if cache is not None and key in cache:
        return cache[key]

    domain = [["name", "=", name]]
    if parent_id is not None:
        domain.append(["parent_id", "=", parent_id])

    ok, result = odoo.search_read("product.category", domain, ["id"], limit=1)
    if not ok:
        if logger:
            logger.error(f"lookup_category: error buscando '{name}': {result}")
        return None

    if result:
        categ_id = result[0]["id"]
    else:
        fields = {"name": name}
        if isinstance(parent_id, int):
            fields["parent_id"] = parent_id
        ok_c, categ_id = odoo.create("product.category", fields)
        if not ok_c:
            if logger:
                logger.warning(f"lookup_category: no se pudo crear '{name}': {categ_id}")
            return None
        if logger:
            logger.info(f"lookup_category: creada '{name}' (parent={parent_id}) → {categ_id}")

    if cache is not None:
        cache[key] = categ_id
    return categ_id

def lookup_state(odoo, name, country_id=49, cache=None, logger=None):
    """Busca departamento por nombre, crea si no existe. Retorna id o None.
    country_id=49 → Colombia (default todos los clientes actuales)."""
    if not name:
        return None
    if cache is not None and name in cache:
        return cache[name]

    ok, result = odoo.search_read("res.country.state", [["name", "=", name]], ["id"], limit=1)
    if not ok:
        if logger:
            logger.error(f"lookup_state: error buscando '{name}': {result}")
        return None

    if result:
        state_id = result[0]["id"]
    else:
        code = "".join([p[0].upper() for p in str(name).split()[:3]])
        ok_c, state_id = odoo.create("res.country.state", {
            "name": name, "country_id": country_id, "code": code
        })
        if not ok_c:
            if logger:
                logger.warning(f"lookup_state: no se pudo crear '{name}': {state_id}")
            return None
        if logger:
            logger.info(f"lookup_state: creado '{name}' (code={code}) → {state_id}")

    if cache is not None:
        cache[name] = state_id
    return state_id

def lookup_zone(odoo, name, cache=None, logger=None):
    """Busca zona de entrega por nombre, crea si no existe. Retorna id o None."""
    if not name:
        return None
    if cache is not None and name in cache:
        return cache[name]

    ok, result = odoo.search_read("partner.delivery.zone", [["name", "=", name]], ["id"], limit=1)
    if not ok:
        if logger:
            logger.error(f"lookup_zone: error buscando '{name}': {result}")
        return None

    if result:
        zone_id = result[0]["id"]
    else:
        ok_c, zone_id = odoo.create("partner.delivery.zone", {"name": name})
        if not ok_c:
            if logger:
                logger.warning(f"lookup_zone: no se pudo crear '{name}': {zone_id}")
            return None
        if logger:
            logger.info(f"lookup_zone: creada '{name}' → {zone_id}")

    if cache is not None:
        cache[name] = zone_id
    return zone_id


def lookup_tax(odoo, amount, type_use, cache=None, logger=None):
    """Busca impuesto por amount + type_tax_use. No crea. Retorna id o None."""
    try:
        amount = float(amount)
    except (TypeError, ValueError):
        return None

    key = (amount, type_use)
    if cache is not None and key in cache:
        return cache[key]

    ok, result = odoo.search_read(
        "account.tax",
        [["amount", "=", amount], ["type_tax_use", "=", type_use]],
        ["id"], limit=1
    )
    if not ok or not result:
        if logger and not ok:
            logger.error(f"lookup_tax: error buscando amount={amount} type={type_use}: {result}")
        tax_id = None
    else:
        tax_id = result[0]["id"]

    if cache is not None:
        cache[key] = tax_id
    return tax_id

def lookup_route(odoo, name, cache=None, logger=None):
    """Busca ruta por nombre exacto. No crea. Retorna id o None."""
    if not name:
        return None
    if cache is not None and name in cache:
        return cache[name]

    ok, result = odoo.search_read("stock.route", [["name", "=", name]], ["id"], limit=1)
    if not ok:
        if logger:
            logger.error(f"lookup_route: error buscando '{name}': {result}")
        return None

    route_id = result[0]["id"] if result else None
    if route_id is None and logger:
        logger.warning(f"lookup_route: ruta '{name}' no existe en Odoo")

    if cache is not None:
        cache[name] = route_id
    return route_id


def lookup_product(odoo, default_code, cache=None, logger=None):
    """Busca producto por default_code. Retorna dict {id, uom_id} o None."""
    if not default_code:
        return None
    if cache is not None and default_code in cache:
        return cache[default_code]

    ok, result = odoo.search_read(
        "product.product",
        [["default_code", "=", default_code]],
        ["id", "uom_id"], limit=1
    )
    if not ok:
        if logger:
            logger.error(f"lookup_product: error buscando '{default_code}': {result}")
        return None

    if result:
        producto = {"id": result[0]["id"], "uom_id": result[0]["uom_id"][0]}
    else:
        producto = None

    if cache is not None:
        cache[default_code] = producto
    return producto


def lookup_partner(odoo, vat, sucursal, cache=None, logger=None):
    """Busca partner por vat + sucursal. Retorna dict {id, customer_rank, supplier_rank} o None."""
    if not vat:
        return None
    key = (vat, sucursal or "")
    if cache is not None and key in cache:
        return cache[key]

    ok, result = odoo.search_read(
        "res.partner",
        [["vat", "=", vat], ["sucursal", "=", sucursal or ""]],
        ["id", "customer_rank", "supplier_rank"], limit=1
    )
    if not ok:
        if logger:
            logger.error(f"lookup_partner: error buscando vat={vat} suc={sucursal}: {result}")
        return None

    partner = result[0] if result else None

    if cache is not None:
        cache[key] = partner
    return partner


def resolve_warehouse(bodega_erp, warehouse_mapping, logger=None):
    """Resuelve bodega ERP → ID almacén Odoo via dict de flow_config. Retorna id o None."""
    if not warehouse_mapping or not bodega_erp:
        return None

    almacen_id = warehouse_mapping.get(str(bodega_erp))
    if almacen_id is None and logger:
        logger.warning(f"resolve_warehouse: '{bodega_erp}' no encontrada en warehouse_mapping")
    return almacen_id