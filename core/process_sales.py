"""
ProcessSales — Carga órdenes de venta en Odoo
Responsabilidades:
  - Filtrar órdenes existentes (1 query)
  - Pre-resolver clientes, productos y zonas en lote
  - Resolver almacenes via warehouse_mapping
  - Agrupar líneas planas en documentos (cabecera + líneas)
  - Crear sale.order con order_line
  - No actualiza — solo crea órdenes nuevas
Hereda: CoreProcessor
Fase: 4 — Core Layer
"""
from collections import defaultdict
from config.logger import IntegradorLogger
from core.base import CoreProcessor
from core.utils.lookups import lookup_partner, lookup_product, lookup_zone, resolve_warehouse


class ProcessSales(CoreProcessor):

    def __init__(self, odoo, config, flow_config):
        self.odoo = odoo
        self.client_id = config["client_id"]
        self.logger = IntegradorLogger(client_id=self.client_id)
        self.flow_config = flow_config

    def process(self, data):
        if not data:
            return {"creados": 0, "fallidos": [], "descartados": 0, "total": 0}

        try:
            # ---- Fase 1: Filtrar órdenes existentes (con reintentos) ----
            pedidos_unicos = list({str(row["pedido"]) for row in data if row.get("pedido")})
            existentes = set()
            if pedidos_unicos:
                max_retries = 3
                fetch_ok = False
                for intento in range(1, max_retries + 1):
                    ok, result = self.odoo.search_read(
                        "sale.order",
                        [["name", "in", pedidos_unicos]],
                        ["id", "name"]
                    )
                    if ok:
                        if result:
                            existentes = {p["name"] for p in result}
                        fetch_ok = True
                        break
                    self.logger.warning(
                        f"Sales | Filtrar existentes: intento {intento}/{max_retries} falló: {result}"
                    )
                if not fetch_ok:
                    self.logger.error(
                        "Sales | Filtrar existentes: falló después de 3 intentos"
                    )
                    return {
                        "creados": 0, "fallidos": [], "descartados": 0,
                        "total": len(data), "error": str(result)
                    }

            data_nueva = [row for row in data if row.get("pedido") not in existentes]
            descartados = len(data) - len(data_nueva)
            self.logger.info(
                f"Sales | Filtrar existentes: {len(pedidos_unicos)} pedidos únicos, "
                f"{len(existentes)} ya existen, {descartados} líneas descartadas"
            )

            if not data_nueva:
                return {"creados": 0, "fallidos": [], "descartados": descartados, "total": len(data)}

            # ---- Default warehouse (fallback) ----
            default_warehouse_id = None
            ok_wh, whs = self.odoo.search_read(
                "stock.warehouse",
                [],
                ["id"], limit=1
            )
            if ok_wh and whs:
                default_warehouse_id = whs[0]["id"]
                self.logger.info(f"Sales | Default warehouse: {default_warehouse_id}")
            else:
                self.logger.warning("Sales | No se encontró warehouse por defecto")

            # ---- Fase 2: Pre-resolver clientes ----
            cache_partner = {}
            clientes_resueltos = {}
            for vat, suc in {
                (row["cliente"], row.get("sucursal_cliente", ""))
                for row in data_nueva if row.get("cliente")
            }:
                partner = lookup_partner(self.odoo, vat, suc, cache=cache_partner, logger=self.logger)
                if partner:
                    clientes_resueltos[(vat, suc)] = partner["id"]
                else:
                    self.logger.warning(
                        f"Sales | Cliente {vat} (suc={suc}) no existe en Odoo"
                    )

            # ---- Fase 3: Pre-resolver productos ----
            cache_product = {}
            productos_resueltos = {}
            for code in {str(row["producto"]) for row in data_nueva if row.get("producto")}:
                producto = lookup_product(self.odoo, code, cache=cache_product, logger=self.logger)
                if producto:
                    productos_resueltos[code] = producto
                else:
                    self.logger.warning(f"Sales | Producto '{code}' no existe en Odoo")

            # ---- Fase 4: Pre-resolver zonas (buscar/crear) ----
            cache_zone = {}
            zonas_resueltas = {}
            for zona in {row["zona"] for row in data_nueva if row.get("zona")}:
                zone_id = lookup_zone(self.odoo, zona, cache=cache_zone, logger=self.logger)
                if zone_id:
                    zonas_resueltas[zona] = zone_id

            self.logger.info(
                f"Sales | Pre-resolución: {len(clientes_resueltos)} clientes, "
                f"{len(productos_resueltos)} productos, {len(zonas_resueltas)} zonas resueltas"
            )

            # ---- Fase 5: Resolver almacenes + enriquecer filas ----
            warehouse_mapping = self.flow_config.get("warehouse_mapping", {})
            lineas_validas = []
            fallidos = []

            for row in data_nueva:
                pedido = row.get("pedido", "")
                ref_producto = str(row.get("producto", ""))

                # Resolver cliente
                customer_key = (row.get("cliente", ""), row.get("sucursal_cliente", ""))
                customer_id = clientes_resueltos.get(customer_key)
                if not customer_id:
                    fallidos.append({
                        "pedido": pedido, "linea": ref_producto,
                        "razon": f"Cliente {customer_key[0]} (suc={customer_key[1]}) no existe en Odoo"
                    })
                    continue

                # Resolver producto
                producto = productos_resueltos.get(ref_producto)
                if not producto:
                    fallidos.append({
                        "pedido": pedido, "linea": ref_producto,
                        "razon": f"Producto '{ref_producto}' no existe en Odoo"
                    })
                    continue

                # Resolver almacén
                warehouse_id = default_warehouse_id
                bodega_erp = row.get("bodega_siesa") or row.get("bodega_sap")
                if bodega_erp and warehouse_mapping:
                    almacen_resuelto = resolve_warehouse(
                        bodega_erp, warehouse_mapping, logger=self.logger
                    )
                    if almacen_resuelto:
                        warehouse_id = almacen_resuelto

                # Resolver zona
                zone_id = zonas_resueltas.get(row.get("zona"))

                lineas_validas.append({
                    **row,
                    "customer_id": customer_id,
                    "product_id": producto["id"],
                    "uom_id": producto["uom_id"],
                    "warehouse_id": warehouse_id,
                    "zone_id": zone_id,
                })

            # ---- Fase 6: Agrupar por cabecera ----
            ordenes = defaultdict(list)
            for linea in lineas_validas:
                header_key = (
                    linea["pedido"],
                    linea["customer_id"],
                    linea.get("zone_id") or 0,
                    linea.get("vendedor", ""),
                    linea.get("condicion_pago", ""),
                    linea.get("warehouse_id"),
                    linea.get("observacion", ""),
                    linea.get("fecha_pedido", ""),
                )
                ordenes[header_key].append(linea)

            self.logger.info(
                f"Sales | Agrupación: {len(lineas_validas)} líneas válidas "
                f"→ {len(ordenes)} pedidos a crear"
            )

            # ---- Fase 7: Crear órdenes ----
            creados = 0
            creados_detalle = []

            for header_key, lineas in ordenes.items():
                pedido, customer_id, zone_id, vendedor, condicion, warehouse_id, observacion, fecha = header_key
                try:
                    # Armar order_lines
                    order_lines = []
                    for linea in lineas:
                        line_vals = {
                            "product_id": linea["product_id"],
                            "product_uom_qty": linea.get("cantidad_pedida", 0),
                            "product_uom": linea["uom_id"],
                            "price_unit": linea.get("precio_unitario", 0),
                        }
                        order_lines.append((0, 0, line_vals))

                    # Armar payload cabecera
                    payload = {
                        "name": pedido,
                        "partner_id": customer_id,
                        "date_order": fecha,
                        "state": lineas[0].get("estado", "draft"),
                        "order_line": order_lines,
                    }
                    if warehouse_id:
                        payload["warehouse_id"] = warehouse_id
                    if zone_id:
                        payload["delivery_zone_id"] = zone_id
                    if observacion:
                        payload["note"] = observacion

                    ok, res = self.odoo.create("sale.order", payload)
                    if ok:
                        creados += 1
                        self.logger.info(f"Sales | Pedido '{pedido}' creado — odoo_id={res}")
                        if len(creados_detalle) < self.MAX_DETALLE:
                            creados_detalle.append({"pedido": pedido, "odoo_id": res})
                    else:
                        fallidos.append({
                            "pedido": pedido, "linea": "",
                            "razon": f"create falló: {res}"
                        })

                except Exception as e:
                    fallidos.append({
                        "pedido": pedido, "linea": "",
                        "razon": f"excepción: {e}"
                    })
                    continue

            # ---- Fase 8: Resumen ----
            self.logger.info(
                f"Sales | Procesamiento: {creados} pedidos creados, "
                f"{len(fallidos)} fallidos, {descartados} líneas descartadas (ya existían), "
                f"de {len(data)} líneas totales"
            )
            if fallidos:
                self.logger.warning("Sales | Registros fallidos:")
                for f in fallidos:
                    if f["linea"]:
                        self.logger.warning(
                            f"  - {f['pedido']} [{f['linea']}]: {f['razon']}"
                        )
                    else:
                        self.logger.warning(
                            f"  - {f['pedido']}: {f['razon']}"
                        )

            return {
                "creados": creados, "fallidos": fallidos,
                "descartados": descartados, "total": len(data),
                "total_ordenes": len(ordenes)
                "creados_detalle": creados_detalle,
                "creados_truncado": max(0, creados - len(creados_detalle))
            }

        except Exception as e:
            self.logger.error(f"Sales | Error fatal: {e}")
            return {
                "creados": 0, "fallidos": [], "descartados": 0,
                "total": len(data), "error": str(e)
            }