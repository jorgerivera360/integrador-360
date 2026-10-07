"""
ProcessPickingDirect — Crea stock.picking directamente en Odoo
Responsabilidades:
  - Filtrar pickings existentes por origin (1 query)
  - Pre-resolver partners y productos en lote
  - Obtener locations desde el picking_type_id (operacion_id)
  - Agrupar líneas planas en documentos (cabecera + líneas)
  - Crear stock.picking con move_ids_without_package
  - Ejecutar acciones post-creación según estado (confirm, assign)
  - No actualiza — solo crea pickings nuevos
Hereda: CoreProcessor
Fase: 4 — Core Layer
"""
from collections import defaultdict
from config.logger import IntegradorLogger
from core.base import CoreProcessor
from core.utils.lookups import lookup_partner, lookup_product


class ProcessPickingDirect(CoreProcessor):

    def __init__(self, odoo, config, flow_config, cancel_check=None):
        self.odoo = odoo
        self.client_id = config["client_id"]
        self.logger = IntegradorLogger(client_id=self.client_id)
        self.flow_config = flow_config
        self.cancel_check = cancel_check

    def process(self, data):
        if not data:
            return {"creados": 0, "fallidos": [], "descartados": 0, "total": 0}

        try:
            # ---- Determinar dirección ----
            flow_type = self.flow_config.get("flow_type", "purchases")
            es_entrada = flow_type == "purchases"

            if es_entrada:
                doc_field = "compra"
                partner_field = "proveedor"
                sucursal_field = "sucursal_proveedor"
                fecha_field = "fecha_entrega"
            else:
                doc_field = "pedido"
                partner_field = "cliente"
                sucursal_field = "sucursal_cliente"
                fecha_field = "fecha_pedido"

            # ---- Fase 1: Filtrar pickings existentes (con reintentos) ----
            docs_unicos = list({str(row[doc_field]) for row in data if row.get(doc_field)})
            existentes = set()
            if docs_unicos:
                max_retries = 3
                fetch_ok = False
                for intento in range(1, max_retries + 1):
                    ok, result = self.odoo.search_read(
                        "stock.picking",
                        [["origin", "in", docs_unicos]],
                        ["id", "origin"]
                    )
                    if ok:
                        if result:
                            existentes = {p["origin"] for p in result}
                        fetch_ok = True
                        break
                    self.logger.warning(
                        f"PickingDirect | Filtrar existentes: intento {intento}/{max_retries} falló: {result}"
                    )
                if not fetch_ok:
                    self.logger.error(
                        "PickingDirect | Filtrar existentes: falló después de 3 intentos"
                    )
                    return {
                        "creados": 0, "fallidos": [], "descartados": 0,
                        "total": len(data), "error": str(result)
                    }

            data_nueva = [row for row in data if str(row.get(doc_field, "")) not in existentes]
            descartados = len(data) - len(data_nueva)
            self.logger.info(
                f"PickingDirect | Filtrar existentes: {len(docs_unicos)} documentos únicos, "
                f"{len(existentes)} ya existen, {descartados} líneas descartadas"
            )

            if not data_nueva:
                return {"creados": 0, "fallidos": [], "descartados": descartados, "total": len(data)}

            # ---- Fase 2: Pre-resolver partners ----
            cache_partner = {}
            partners_resueltos = {}
            for vat, suc in {
                (row[partner_field], row.get(sucursal_field, ""))
                for row in data_nueva if row.get(partner_field)
            }:
                partner = lookup_partner(self.odoo, vat, suc, cache=cache_partner, logger=self.logger)
                if partner:
                    partners_resueltos[(vat, suc)] = partner["id"]
                else:
                    self.logger.warning(
                        f"PickingDirect | Partner {vat} (suc={suc}) no existe en Odoo"
                    )

            # ---- Fase 3: Pre-resolver productos ----
            cache_product = {}
            productos_resueltos = {}
            for code in {str(row["producto"]) for row in data_nueva if row.get("producto")}:
                producto = lookup_product(self.odoo, code, cache=cache_product, logger=self.logger)
                if producto:
                    productos_resueltos[code] = producto
                else:
                    self.logger.warning(f"PickingDirect | Producto '{code}' no existe en Odoo")

            self.logger.info(
                f"PickingDirect | Pre-resolución: {len(partners_resueltos)} partners, "
                f"{len(productos_resueltos)} productos resueltos"
            )

            # ---- Fase 4: Cache de locations por picking_type_id ----
            cache_picking_type = {}

            def get_picking_type_locations(picking_type_id):
                if picking_type_id in cache_picking_type:
                    return cache_picking_type[picking_type_id]
                ok, result = self.odoo.search_read(
                    "stock.picking.type",
                    [["id", "=", picking_type_id]],
                    ["id", "default_location_src_id", "default_location_dest_id"],
                    limit=1
                )
                if ok and result:
                    loc_src = result[0]["default_location_src_id"]
                    loc_dest = result[0]["default_location_dest_id"]
                    locations = {
                        "location_id": loc_src[0] if isinstance(loc_src, list) else loc_src,
                        "location_dest_id": loc_dest[0] if isinstance(loc_dest, list) else loc_dest,
                    }
                    cache_picking_type[picking_type_id] = locations
                    return locations
                self.logger.warning(
                    f"PickingDirect | picking_type_id={picking_type_id} no encontrado en Odoo"
                )
                cache_picking_type[picking_type_id] = None
                return None

            # ---- Fase 5: Construir líneas válidas ----
            lineas_validas = []
            fallidos = []

            for row in data_nueva:
                doc_name = str(row.get(doc_field, ""))
                ref_producto = str(row.get("producto", ""))

                # Resolver partner
                partner_key = (row.get(partner_field, ""), row.get(sucursal_field, ""))
                partner_id = partners_resueltos.get(partner_key)
                if not partner_id:
                    fallidos.append({
                        doc_field: doc_name, "linea": ref_producto,
                        "razon": f"Partner {partner_key[0]} (suc={partner_key[1]}) no existe en Odoo"
                    })
                    continue

                # Resolver producto
                producto = productos_resueltos.get(ref_producto)
                if not producto:
                    fallidos.append({
                        doc_field: doc_name, "linea": ref_producto,
                        "razon": f"Producto '{ref_producto}' no existe en Odoo"
                    })
                    continue

                # Resolver picking_type locations
                operacion_id = row.get("operacion_id")
                if not operacion_id:
                    fallidos.append({
                        doc_field: doc_name, "linea": ref_producto,
                        "razon": "operacion_id no definido en la fila"
                    })
                    continue

                operacion_id = int(operacion_id)
                locations = get_picking_type_locations(operacion_id)
                if not locations:
                    fallidos.append({
                        doc_field: doc_name, "linea": ref_producto,
                        "razon": f"picking_type_id={operacion_id} no encontrado o sin locations"
                    })
                    continue

                lineas_validas.append({
                    **row,
                    "partner_id": partner_id,
                    "product_id": producto["id"],
                    "uom_id": producto["uom_id"],
                    "operacion_id": operacion_id,
                    "location_id": locations["location_id"],
                    "location_dest_id": locations["location_dest_id"],
                })

            # ---- Fase 6: Agrupar por cabecera ----
            ordenes = defaultdict(list)
            for linea in lineas_validas:
                header_key = (
                    str(linea[doc_field]),
                    linea["partner_id"],
                    linea.get(fecha_field, ""),
                    linea["operacion_id"],
                )
                ordenes[header_key].append(linea)

            self.logger.info(
                f"PickingDirect | Agrupación: {len(lineas_validas)} líneas válidas "
                f"→ {len(ordenes)} pickings a crear"
            )

            # ---- Fase 7: Crear pickings ----
            creados = 0
            creados_detalle = []

            for header_key, lineas in ordenes.items():
                if self.cancel_check and self.cancel_check():
                    self.logger.info("PickingDirect | Ejecución cancelada por el usuario")
                    break

                doc_name, partner_id, fecha, operacion_id = header_key
                try:
                    # Armar move lines
                    move_lines = []
                    for linea in lineas:
                        qty_field = "cantidad" if es_entrada else "cantidad_pedida"
                        line_vals = {
                            "name": linea.get("descripcion", linea.get("producto", "")),
                            "product_id": linea["product_id"],
                            "product_uom_qty": linea.get(qty_field, 0),
                            "product_uom": linea["uom_id"],
                            "location_id": linea["location_id"],
                            "location_dest_id": linea["location_dest_id"],
                        }
                        move_lines.append((0, 0, line_vals))

                    # Armar payload cabecera
                    payload = {
                        "origin": doc_name,
                        "partner_id": partner_id,
                        "picking_type_id": operacion_id,
                        "location_id": lineas[0]["location_id"],
                        "location_dest_id": lineas[0]["location_dest_id"],
                        "scheduled_date": fecha,
                        "move_ids_without_package": move_lines,
                    }

                    ok, res = self.odoo.create("stock.picking", payload)
                    if ok:
                        creados += 1
                        picking_id = res
                        self.logger.info(f"PickingDirect | Picking '{doc_name}' creado — odoo_id={picking_id}")

                        # Acciones post-creación según estado
                        estado = lineas[0].get("estado", "draft")
                        if estado in ("confirmed", "assigned"):
                            ok_confirm, res_confirm = self.odoo.action(
                                "stock.picking", "action_confirm", [picking_id]
                            )
                            if not ok_confirm:
                                self.logger.warning(
                                    f"PickingDirect | action_confirm falló para picking {picking_id}: {res_confirm}"
                                )
                            elif estado == "assigned":
                                ok_assign, res_assign = self.odoo.action(
                                    "stock.picking", "action_assign", [picking_id]
                                )
                                if not ok_assign:
                                    self.logger.warning(
                                        f"PickingDirect | action_assign falló para picking {picking_id}: {res_assign}"
                                    )

                        if len(creados_detalle) < self.MAX_DETALLE:
                            creados_detalle.append({doc_field: doc_name, "odoo_id": picking_id})
                    else:
                        fallidos.append({
                            doc_field: doc_name, "linea": "",
                            "razon": f"create falló: {res}"
                        })

                except Exception as e:
                    fallidos.append({
                        doc_field: doc_name, "linea": "",
                        "razon": f"excepción: {e}"
                    })
                    continue

            # ---- Fase 8: Resumen ----
            self.logger.info(
                f"PickingDirect | Procesamiento: {creados} pickings creados, "
                f"{len(fallidos)} fallidos, {descartados} líneas descartadas (ya existían), "
                f"de {len(data)} líneas totales"
            )
            if fallidos:
                self.logger.warning("PickingDirect | Registros fallidos:")
                for f in fallidos:
                    if f["linea"]:
                        self.logger.warning(
                            f"  - {f[doc_field]} [{f['linea']}]: {f['razon']}"
                        )
                    else:
                        self.logger.warning(
                            f"  - {f[doc_field]}: {f['razon']}"
                        )

            return {
                "creados": creados, "fallidos": fallidos,
                "descartados": descartados, "total": len(data),
                "total_ordenes": len(ordenes),
                "creados_detalle": creados_detalle,
                "creados_truncado": max(0, creados - len(creados_detalle))
            }

        except Exception as e:
            self.logger.error(f"PickingDirect | Error fatal: {e}")
            return {
                "creados": 0, "fallidos": [], "descartados": 0,
                "total": len(data), "error": str(e)
            }
