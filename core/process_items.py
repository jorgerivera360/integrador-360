"""
ProcessItems — Carga productos en Odoo
Responsabilidades:
  - Bulk fetch de productos existentes (1 query)
  - Pre-resolver dependencias en lote (UOM, categoría, tax, route)
  - Crear productos nuevos (con retry barcode)
  - Actualizar productos existentes (sin default_code, tracking)
  - Barcode multi (codigos_extras, post-create)
Hereda: CoreProcessor
Fase: 4 — Core Layer
"""
from config.logger import IntegradorLogger
from core.base import CoreProcessor
from core.utils.lookups import lookup_uom, lookup_category, lookup_tax, lookup_route


class ProcessItems(CoreProcessor):

    def __init__(self, odoo, config, flow_config):
        self.odoo = odoo
        self.client_id = config["client_id"]
        self.logger = IntegradorLogger(client_id=self.client_id)
        self.flow_config = flow_config

    def process(self, data):
        if not data:
            return {"creados": 0, "actualizados": 0, "fallidos": [], "total": 0}

        try:
            # ---- Fase 1: Normalizar UOMs ----
            uom_mapping = self.flow_config.get("uom_mapping", {})
            if uom_mapping:
                for row in data:
                    raw = row.get("unidad", "")
                    if raw:
                        row["unidad"] = uom_mapping.get(raw, uom_mapping.get(raw.lower(), raw))

            # ---- Fase 2: Bulk fetch existentes (con reintentos) ----
            refs = list({row["referencia"] for row in data if row.get("referencia")})
            existing = {}
            if refs:
                max_retries = 3
                for intento in range(1, max_retries + 1):
                    ok, result = self.odoo.search_read(
                        "product.template",
                        [["default_code", "in", refs]],
                        ["id", "default_code"]
                    )
                    if ok:
                        if result:
                            existing = {p["default_code"]: p["id"] for p in result}
                        break
                    self.logger.warning(
                        f"Items | Búsqueda existentes: intento {intento}/{max_retries} falló: {result}"
                    )
                else:
                    self.logger.error(
                        f"Items | Búsqueda existentes: falló después de {max_retries} intentos"
                    )
                    return {
                        "creados": 0, "actualizados": 0, "fallidos": [],
                        "total": len(data), "error": str(result)
                    }
            self.logger.info(
                f"Items | Búsqueda existentes: {len(refs)} referencias, {len(existing)} ya existen en Odoo"
            )

            # ---- Fase 3: Pre-resolver dependencias en lote ----
            cache_uom = {}
            cache_categ = {}
            cache_tax = {}
            cache_route = {}

            # UOMs únicos
            uoms_resueltos = {}
            for name in {row["unidad"] for row in data if row.get("unidad")}:
                uoms_resueltos[name] = lookup_uom(self.odoo, name, cache=cache_uom, logger=self.logger)

            # Categorías únicas (1 o 2 niveles según presencia de marca)
            categorias_resueltas = {}
            tiene_marca = any(row.get("marca") for row in data)

            if tiene_marca:
                padres = {}
                for cat_name in {row["categoria"] for row in data if row.get("categoria")}:
                    padres[cat_name] = lookup_category(
                        self.odoo, cat_name, parent_id=False, cache=cache_categ, logger=self.logger
                    )
                for cat_name, marca_name in {(row["categoria"], row["marca"]) for row in data if row.get("marca") and row.get("categoria")}:
                    parent = padres.get(cat_name)
                    if parent:
                        categorias_resueltas[(cat_name, marca_name)] = lookup_category(
                            self.odoo, marca_name, parent_id=parent, cache=cache_categ, logger=self.logger
                        )
                for cat_name, cat_id in padres.items():
                    categorias_resueltas[(cat_name, None)] = cat_id
            else:
                for cat_name in {row["categoria"] for row in data if row.get("categoria")}:
                    categorias_resueltas[(cat_name, None)] = lookup_category(
                        self.odoo, cat_name, cache=cache_categ, logger=self.logger
                    )

            # Taxes únicos (solo si viene iva)
            taxes_resueltos = {}
            for iva in {row["iva"] for row in data if row.get("iva") is not None}:
                taxes_resueltos[iva] = {
                    "sale": lookup_tax(self.odoo, iva, "sale", cache=cache_tax, logger=self.logger),
                    "purchase": lookup_tax(self.odoo, iva, "purchase", cache=cache_tax, logger=self.logger),
                }

            # Routes únicos (solo si viene ruta, puede ser multi separado por coma)
            routes_resueltos = {}
            for row in data:
                if row.get("ruta"):
                    for r in str(row["ruta"]).split(","):
                        r = r.strip()
                        if r and r not in routes_resueltos:
                            routes_resueltos[r] = lookup_route(
                                self.odoo, r, cache=cache_route, logger=self.logger
                            )

            self.logger.info(
                f"Items | Pre-resolución: {len(uoms_resueltos)} UOMs, "
                f"{len(categorias_resueltas)} categorías, {len(taxes_resueltos)} taxes, "
                f"{len(routes_resueltos)} routes resueltos"
            )

            # ---- Fase 4: Loop — create / write ----
            creados = 0
            actualizados = 0
            fallidos = []

            for row in data:
                ref = row.get("referencia", "")
                try:
                    # Resolver UOM (obligatorio)
                    uom_id = uoms_resueltos.get(row.get("unidad"))
                    if not uom_id:
                        fallidos.append({"referencia": ref, "razon": f"UOM '{row.get('unidad')}' no resuelta"})
                        continue

                    # Resolver categoría
                    marca = row.get("marca") if tiene_marca else None
                    categ_id = categorias_resueltas.get((row.get("categoria"), marca))
                    if not categ_id and marca:
                        categ_id = categorias_resueltas.get((row.get("categoria"), None))

                    # Resolver taxes (opcional)
                    tax_data = taxes_resueltos.get(row.get("iva"), {})

                    # Resolver routes (opcional, multi)
                    route_ids = []
                    if row.get("ruta"):
                        for r in str(row["ruta"]).split(","):
                            r = r.strip()
                            rid = routes_resueltos.get(r)
                            if rid:
                                route_ids.append(rid)

                    # Armar payload
                    payload = {
                        "name": row.get("descripcion", ""),
                        "uom_id": uom_id,
                        "uom_po_id": uom_id,
                        "detailed_type": row.get("type", "product"),
                    }
                    if categ_id:
                        payload["categ_id"] = categ_id

                    if row.get("peso") is not None:
                        payload["weight"] = row["peso"]

                    if row.get("volumen") is not None:
                        payload["volume"] = row["volumen"]

                    if row.get("precio") is not None:
                        payload["list_price"] = row["precio"]

                    if row.get("costo") is not None:
                        payload["standard_price"] = row["costo"]

                    if row.get("use_expiration_date") is not None:
                        payload["use_expiration_date"] = bool(row["use_expiration_date"])

                    if row.get("expiration_time") is not None:
                        payload["expiration_time"] = row["expiration_time"]

                    if tax_data.get("sale"):
                        payload["taxes_id"] = [(6, 0, [tax_data["sale"]])]

                    if tax_data.get("purchase"):
                        payload["supplier_taxes_id"] = [(6, 0, [tax_data["purchase"]])]
                        
                    if route_ids:
                        payload["route_ids"] = [(6, 0, route_ids)]

                    product_id = existing.get(ref)

                    if product_id:
                        # ---- WRITE (sin default_code, tracking) ----
                        ok, res = self.odoo.write("product.template", [product_id], payload)
                        if ok:
                            actualizados += 1
                        else:
                            fallidos.append({"referencia": ref, "razon": f"write falló: {res}"})
                    else:
                        # ---- CREATE (con default_code, tracking, barcode) ----
                        payload["default_code"] = ref
                        payload["tracking"] = row.get("tracking", "none")
                        if row.get("codigo_barras"):
                            payload["barcode"] = row["codigo_barras"]

                        ok, res = self.odoo.create("product.template", payload)
                        if not ok and "barcode" in payload:
                            self.logger.warning(f"Items | '{ref}': create falló con barcode, reintentando sin él")
                            payload.pop("barcode")
                            ok, res = self.odoo.create("product.template", payload)

                        if ok:
                            creados += 1
                            existing[ref] = res
                            if row.get("codigos_extras"):
                                self._process_barcode_multi(res, ref, row["codigos_extras"])
                        else:
                            fallidos.append({"referencia": ref, "razon": f"create falló: {res}"})

                except Exception as e:
                    fallidos.append({"referencia": ref, "razon": f"excepción: {e}"})
                    continue

            # ---- Fase 5: Resumen ----
            self.logger.info(
                f"Items | Procesamiento: {creados} creados, {actualizados} actualizados, "
                f"{len(fallidos)} fallidos de {len(data)} total"
            )
            if fallidos:
                self.logger.warning("Items | Registros fallidos:")
                for f in fallidos:
                    self.logger.warning(f"  - {f['referencia']}: {f['razon']}")

            return {
                "creados": creados, "actualizados": actualizados,
                "fallidos": fallidos, "total": len(data)
            }

        except Exception as e:
            self.logger.error(f"Items | Error fatal: {e}")
            return {
                "creados": 0, "actualizados": 0, "fallidos": [],
                "total": len(data), "error": str(e)
            }

    def _process_barcode_multi(self, template_id, referencia, codigos_extras):
        """Crea barcodes adicionales en product.barcode.multi."""
        ok, variants = self.odoo.search_read(
            "product.product",
            [["product_tmpl_id", "=", template_id]],
            ["id"], limit=1
        )
        if not ok or not variants:
            self.logger.warning(f"barcode_multi '{referencia}': no se encontró variant")
            return

        variant_id = variants[0]["id"]
        codes = [c.strip() for c in str(codigos_extras).split(",") if c.strip()]

        for code in codes:
            ok_s, found = self.odoo.search_read(
                "product.barcode.multi",
                [["name", "=", code]],
                ["id", "product_id"], limit=1
            )
            if not ok_s:
                continue
            if found:
                if found[0]["product_id"][0] != variant_id:
                    self.logger.warning(
                        f"barcode_multi '{code}': ya existe en otro producto (id={found[0]['product_id'][0]})"
                    )
                continue

            ok_c, _ = self.odoo.create("product.barcode.multi", {"name": code, "product_id": variant_id})
            if ok_c:
                self.logger.info(f"barcode_multi '{referencia}': creado '{code}'")
            else:
                self.logger.warning(f"barcode_multi '{referencia}': no se pudo crear '{code}'")