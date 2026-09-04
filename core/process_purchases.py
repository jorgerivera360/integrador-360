"""
ProcessPurchases — Carga órdenes de compra en Odoo
Responsabilidades:
  - Filtrar órdenes existentes (1 query)
  - Pre-resolver proveedores y productos en lote
  - Resolver almacenes via warehouse_mapping
  - Agrupar líneas planas en documentos (cabecera + líneas)
  - Crear purchase.order con order_line
  - No actualiza — solo crea órdenes nuevas
Hereda: CoreProcessor
Fase: 4 — Core Layer
"""
from collections import defaultdict
from config.logger import IntegradorLogger
from core.base import CoreProcessor
from core.utils.lookups import lookup_partner, lookup_product, resolve_warehouse


class ProcessPurchases(CoreProcessor):

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
            # ---- Fase 1: Filtrar órdenes existentes (con reintentos) ----
            compras_unicas = list({str(row["compra"]) for row in data if row.get("compra")})
            existentes = set()
            if compras_unicas:
                max_retries = 3
                fetch_ok = False
                for intento in range(1, max_retries + 1):
                    ok, result = self.odoo.search_read(
                        "purchase.order",
                        [["name", "in", compras_unicas]],
                        ["id", "name"]
                    )
                    if ok:
                        if result:
                            existentes = {p["name"] for p in result}
                        fetch_ok = True
                        break
                    self.logger.warning(
                        f"Purchases | Filtrar existentes: intento {intento}/{max_retries} falló: {result}"
                    )
                if not fetch_ok:
                    self.logger.error(
                        "Purchases | Filtrar existentes: falló después de 3 intentos"
                    )
                    return {
                        "creados": 0, "fallidos": [], "descartados": 0,
                        "total": len(data), "error": str(result)
                    }

            data_nueva = [row for row in data if row.get("compra") not in existentes]
            descartados = len(data) - len(data_nueva)
            self.logger.info(
                f"Purchases | Filtrar existentes: {len(compras_unicas)} órdenes únicas, "
                f"{len(existentes)} ya existen, {descartados} líneas descartadas"
            )

            if not data_nueva:
                return {"creados": 0, "fallidos": [], "descartados": descartados, "total": len(data)}

            # ---- Default picking type (fallback) ----
            default_picking_type_id = None
            ok_pt, pts = self.odoo.search_read(
                "stock.picking.type",
                [["code", "=", "incoming"]],
                ["id"], limit=1
            )
            if ok_pt and pts:
                default_picking_type_id = pts[0]["id"]
                self.logger.info(f"Purchases | Default picking type: {default_picking_type_id}")
            else:
                self.logger.warning("Purchases | No se encontró picking type 'incoming' por defecto")

            # ---- Fase 2: Pre-resolver proveedores ----
            cache_partner = {}
            proveedores_resueltos = {}
            for vat, suc in {(row["proveedor"], row.get("sucursal_proveedor", "")) for row in data_nueva if row.get("proveedor")}:
                partner = lookup_partner(self.odoo, vat, suc, cache=cache_partner, logger=self.logger)
                if partner:
                    proveedores_resueltos[(vat, suc)] = partner["id"]
                else:
                    self.logger.warning(
                        f"Purchases | Proveedor {vat} (suc={suc}) no existe en Odoo"
                    )

            # ---- Fase 3: Pre-resolver productos ----
            cache_product = {}
            productos_resueltos = {}
            for code in {str(row["producto"]) for row in data_nueva if row.get("producto")}:
                producto = lookup_product(self.odoo, code, cache=cache_product, logger=self.logger)
                if producto:
                    productos_resueltos[code] = producto
                else:
                    self.logger.warning(f"Purchases | Producto '{code}' no existe en Odoo")

            self.logger.info(
                f"Purchases | Pre-resolución: {len(proveedores_resueltos)} proveedores, "
                f"{len(productos_resueltos)} productos resueltos"
            )

            # ---- Fase 4: Resolver almacenes + enriquecer filas ----
            warehouse_mapping = self.flow_config.get("warehouse_mapping", {})
            lineas_validas = []
            fallidos = []

            for row in data_nueva:
                compra = row.get("compra", "")
                ref_producto = str(row.get("producto", ""))

                # Resolver proveedor
                supplier_key = (row.get("proveedor", ""), row.get("sucursal_proveedor", ""))
                supplier_id = proveedores_resueltos.get(supplier_key)
                if not supplier_id:
                    fallidos.append({
                        "compra": compra, "linea": ref_producto,
                        "razon": f"Proveedor {supplier_key[0]} (suc={supplier_key[1]}) no existe en Odoo"
                    })
                    continue

                # Resolver producto
                producto = productos_resueltos.get(ref_producto)
                if not producto:
                    fallidos.append({
                        "compra": compra, "linea": ref_producto,
                        "razon": f"Producto '{ref_producto}' no existe en Odoo"
                    })
                    continue

                # Resolver almacén
                picking_type_id = default_picking_type_id
                bodega_erp = row.get("bodega_siesa") or row.get("bodega_sap")
                if bodega_erp and warehouse_mapping:
                    almacen_resuelto = resolve_warehouse(
                        bodega_erp, warehouse_mapping, logger=self.logger
                    )
                    if almacen_resuelto:
                        picking_type_id = almacen_resuelto

                lineas_validas.append({
                    **row,
                    "supplier_id": supplier_id,
                    "product_id": producto["id"],
                    "uom_id": producto["uom_id"],
                    "picking_type_id": picking_type_id,
                })

            # ---- Fase 5: Agrupar por cabecera ----
            ordenes = defaultdict(list)
            for linea in lineas_validas:
                header_key = (
                    linea["compra"],
                    linea["supplier_id"],
                    linea.get("referencia_compra", ""),
                    linea.get("fecha_entrega", ""),
                    linea.get("estado", "draft"),
                    linea.get("picking_type_id", ""),
                )
                ordenes[header_key].append(linea)

            self.logger.info(
                f"Purchases | Agrupación: {len(lineas_validas)} líneas válidas "
                f"→ {len(ordenes)} órdenes a crear"
            )

            # ---- Fase 6: Crear órdenes ----
            creados = 0
            creados_detalle = []

            for header_key, lineas in ordenes.items():
                if self.cancel_check and self.cancel_check():
                    self.logger.info("Purchases | Ejecución cancelada por el usuario")
                    break
                try:
                    # Armar order_lines
                    order_lines = []
                    for linea in lineas:
                        line_vals = {
                            "product_id": linea["product_id"],
                            "product_qty": linea.get("cantidad", 0),
                            "product_uom": linea["uom_id"],
                            "price_unit": linea.get("precio_unitario", 0),
                            "name": linea.get("descripcion", linea.get("producto", "")),
                        }
                        order_lines.append((0, 0, line_vals))

                    # Armar payload cabecera
                    payload = {
                        "name": compra,
                        "partner_id": supplier_id,
                        "date_planned": fecha,
                        "state": estado,
                        "partner_ref": referencia or lineas[0].get("comprador", ""),
                        "order_line": order_lines,
                    }
                    if picking_type_id:
                          payload["picking_type_id"] = picking_type_id

                    ok, res = self.odoo.create("purchase.order", payload)
                    if ok:
                        creados += 1
                        self.logger.info(f"Purchases | Compra '{compra}' creada — odoo_id={res}")
                        if len(creados_detalle) < self.MAX_DETALLE:
                            creados_detalle.append({"compra": compra, "odoo_id": res})
                    else:
                        fallidos.append({
                            "compra": compra, "linea": "",
                            "razon": f"create falló: {res}"
                        })

                except Exception as e:
                    fallidos.append({
                        "compra": compra, "linea": "",
                        "razon": f"excepción: {e}"
                    })
                    continue

            # ---- Fase 7: Resumen ----
            self.logger.info(
                f"Purchases | Procesamiento: {creados} órdenes creadas, "
                f"{len(fallidos)} fallidos, {descartados} líneas descartadas (ya existían), "
                f"de {len(data)} líneas totales"
            )
            if fallidos:
                self.logger.warning("Purchases | Registros fallidos:")
                for f in fallidos:
                    if f["linea"]:
                        self.logger.warning(
                            f"  - {f['compra']} [{f['linea']}]: {f['razon']}"
                        )
                    else:
                        self.logger.warning(
                            f"  - {f['compra']}: {f['razon']}"
                        )

            return {
                "creados": creados, "fallidos": fallidos,
                "descartados": descartados, "total": len(data),
                "total_ordenes": len(ordenes),
                "creados_detalle": creados_detalle,
                "creados_truncado": max(0, creados - len(creados_detalle))
            }

        except Exception as e:
            self.logger.error(f"Purchases | Error fatal: {e}")
            return {
                "creados": 0, "fallidos": [], "descartados": 0,
                "total": len(data), "error": str(e)
            }