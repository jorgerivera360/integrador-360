"""
ProcessPartners — Carga partners en Odoo
Responsabilidades:
  - Bulk fetch de partners existentes (1 query)
  - Pre-resolver departamentos en lote
  - Crear/actualizar partners (vat nunca en write)
  - Jerarquía de sucursales configurable (si flow_config lo pide)
  - Rank solo sube 0→1, nunca baja
Hereda: CoreProcessor
Fase: 4 — Core Layer
"""
from config.logger import IntegradorLogger
from core.base import CoreProcessor
from core.utils.lookups import lookup_state


class ProcessPartners(CoreProcessor):

    def __init__(self, odoo, config, flow_config):
        self.odoo = odoo
        self.client_id = config["client_id"]
        self.logger = IntegradorLogger(client_id=self.client_id)
        self.flow_config = flow_config

    def process(self, data):
        if not data:
            return {"creados": 0, "actualizados": 0, "fallidos": [], "total": 0}

        try:
            # ---- Fase 1: Ordenar por jerarquía (si aplica) ----
            sucursal_hierarchy = self.flow_config.get("sucursal_hierarchy", False)
            sucursal_padre = self.flow_config.get("sucursal_padre", "001")
            if sucursal_hierarchy:
                data = sorted(data, key=lambda r: 0 if r.get("sucursal") == sucursal_padre else 1)
                self.logger.info(
                    f"Partners | Jerarquía: activada — sucursal '{sucursal_padre}' se procesa primero"
                )

            # ---- Fase 2: Bulk fetch existentes (con reintentos) ----
            vats = list({row["identificacion"] for row in data if row.get("identificacion")})
            existing = {}
            if vats:
                max_retries = 3
                fetch_ok = False
                for intento in range(1, max_retries + 1):
                    ok, result = self.odoo.search_read(
                        "res.partner",
                        [["vat", "in", vats]],
                        ["id", "vat", "sucursal", "customer_rank", "supplier_rank"]
                    )
                    if ok:
                        if result:
                            for p in result:
                                existing[(p["vat"], p.get("sucursal", ""))] = {
                                    "id": p["id"],
                                    "customer_rank": p.get("customer_rank", 0),
                                    "supplier_rank": p.get("supplier_rank", 0),
                                }
                        fetch_ok = True
                        break
                    self.logger.warning(
                        f"Partners | Búsqueda existentes: intento {intento}/{max_retries} falló: {result}"
                    )
                if not fetch_ok:
                    self.logger.error(
                        f"Partners | Búsqueda existentes: falló después de {max_retries} intentos"
                    )
                    return {
                        "creados": 0, "actualizados": 0, "fallidos": [],
                        "total": len(data), "error": str(result)
                    }
            self.logger.info(
                f"Partners | Búsqueda existentes: {len(vats)} identificaciones, "
                f"{len(existing)} ya existen en Odoo"
            )

            # ---- Fase 3: Pre-resolver departamentos en lote ----
            cache_state = {}
            country_id = self.flow_config.get("country_id", 49)
            identification_type_id = self.flow_config.get("identification_type_id", 5)

            states_resueltos = {}
            for depto in {row["departamento"] for row in data if row.get("departamento")}:
                states_resueltos[depto] = lookup_state(
                    self.odoo, depto, country_id=country_id,
                    cache=cache_state, logger=self.logger
                )

            self.logger.info(
                f"Partners | Pre-resolución: {len(states_resueltos)} departamentos resueltos"
            )

            # ---- Fase 4: Loop — create / write ----
            creados = 0
            actualizados = 0
            fallidos = []

            for row in data:
                vat = row.get("identificacion", "")
                sucursal = row.get("sucursal", "")
                nombre = row.get("nombre", "")
                try:
                    # Resolver departamento
                    state_id = states_resueltos.get(row.get("departamento"))

                    # Armar payload base
                    payload = {"name": nombre}

                    if row.get("direccion"):
                        payload["street"] = row["direccion"]
                    if row.get("codigo_postal"):
                        payload["zip"] = row["codigo_postal"]
                    if row.get("telefono"):
                        payload["phone"] = row["telefono"]
                    if row.get("email"):
                        payload["email"] = row["email"]
                    if row.get("ciudad"):
                        payload["city"] = row["ciudad"]

                    if state_id:
                        payload["state_id"] = state_id
                    payload["country_id"] = country_id

                    # Campos opcionales por presencia del dato
                    if row.get("lista_precio"):
                        payload["property_product_pricelist"] = row["lista_precio"]

                    partner = existing.get((vat, sucursal))

                    if partner:
                        # ---- WRITE (sin vat, rank solo sube) ----
                        payload["sucursal"] = sucursal
                        partner_id = partner["id"]

                        flow_type = self.flow_config.get("flow_type", "")
                        if flow_type in ("customer", "partners") and partner.get("customer_rank", 0) == 0:
                            payload["customer_rank"] = 1
                        if flow_type in ("supplier", "partners") and partner.get("supplier_rank", 0) == 0:
                            payload["supplier_rank"] = 1

                        ok, res = self.odoo.write("res.partner", [partner_id], payload)
                        if ok:
                            actualizados += 1
                        else:
                            fallidos.append({
                                "identificacion": vat, "sucursal": sucursal,
                                "razon": f"write falló: {res}"
                            })
                    else:
                        # ---- CREATE (con vat, sucursal, rank, tipo doc) ----
                        payload["vat"] = vat
                        payload["sucursal"] = sucursal
                        payload["l10n_latam_identification_type_id"] = identification_type_id

                        flow_type = self.flow_config.get("flow_type", "")
                        if flow_type in ("customer", "partners"):
                            payload["customer_rank"] = 1
                        if flow_type in ("supplier", "partners"):
                            payload["supplier_rank"] = 1

                        # Jerarquía: padre vs hijo
                        if sucursal_hierarchy:
                            if sucursal == sucursal_padre:
                                payload["is_company"] = True
                            else:
                                parent = existing.get((vat, sucursal_padre))
                                if parent:
                                    payload["parent_id"] = parent["id"]
                                    payload["type"] = "other"
                                    payload["is_company"] = False

                        ok, res = self.odoo.create("res.partner", payload)
                        if ok:
                            creados += 1
                            existing[(vat, sucursal)] = {
                                "id": res,
                                "customer_rank": payload.get("customer_rank", 0),
                                "supplier_rank": payload.get("supplier_rank", 0),
                            }
                        else:
                            fallidos.append({
                                "identificacion": vat, "sucursal": sucursal,
                                "razon": f"create falló: {res}"
                            })

                except Exception as e:
                    fallidos.append({
                        "identificacion": vat, "sucursal": sucursal,
                        "razon": f"excepción: {e}"
                    })
                    continue

            # ---- Fase 5: Resumen ----
            self.logger.info(
                f"Partners | Procesamiento: {creados} creados, {actualizados} actualizados, "
                f"{len(fallidos)} fallidos de {len(data)} total"
            )
            if fallidos:
                self.logger.warning("Partners | Registros fallidos:")
                for f in fallidos:
                    self.logger.warning(
                        f"  - {f['identificacion']} suc={f['sucursal']}: {f['razon']}"
                    )

            return {
                "creados": creados, "actualizados": actualizados,
                "fallidos": fallidos, "total": len(data)
            }

        except Exception as e:
            self.logger.error(f"Partners | Error fatal: {e}")
            return {
                "creados": 0, "actualizados": 0, "fallidos": [],
                "total": len(data), "error": str(e)
            }