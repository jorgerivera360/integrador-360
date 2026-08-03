"""
TransformConnekta — Transform SIESA Connekta
Responsabilidades:
  - get_flow() — llama al conector y normaliza los datos
  - _apply_mapping() — renombra keys del dict según flow_config["mapping"]
  - _apply_hardcodes() — inyecta valores fijos según flow_config["hardcodes"]
  - _apply_conditionals() — evalúa reglas simples o funciones del catálogo
Hereda: Transform
Fase: 3 — Transform Layer
"""
from config.logger import IntegradorLogger
from transform.base import Transform
from transform.utils.determination_functions import get_determination_function
from transform.utils.helpers import (clean_row, validate_record, to_float, to_int, parse_fecha)


class TransformConnekta(Transform):
    def __init__(self, config: dict):
        self.client_id = config["client_id"]
        self.logger = IntegradorLogger(client_id=self.client_id)

    def get_flow(self, connector, flow_name: str, flow_config: dict) -> list:
        normalize_map = {
          # Maestros
          "items": self._normalize_items,
          "partners": self._normalize_partners,
          #Transacciones entrada
          "compras": self._normalize_purchases,
          "devoluciones_cliente": self._normalize_purchases,
          "entrada_calidad_recepcion": self._normalize_purchases,
          "traslados_entradas": self._normalize_purchases,
          "entrada_inventario_oc": self._normalize_purchases,
          "entrada_ensamble": self._normalize_purchases,
          "entrada_desensamble": self._normalize_purchases,
          "traslados_transito_entrada": self._normalize_purchases,
          # Transacciones salidas
          "ventas": self._normalize_sales,
          "devoluciones_proveedores": self._normalize_sales,
          "traslados_salidas": self._normalize_sales,
          "traslados_preproduccion": self._normalize_sales,
          "salidas_ensamble": self._normalize_sales,
          "salida_desensamble": self._normalize_sales,
          "salidas_consumo_interno": self._normalize_sales,
          "salida_requisiciones": self._normalize_sales,
          "traslados_transito_salida": self._normalize_sales,
          "facturas": self._normalize_sales,
        }

        normalize_fn = normalize_map.get(flow_name)
        if not normalize_fn:
            self.logger.error(f"Flujo no soportado en TransformConnekta: '{flow_name}' ")
            return []

        try:
            query_desc = flow_config.get("query_desc", "")
            if not query_desc:
                self.logger.error(f"No hay query_desc configurado para flow '{flow_name}'")
                return []

            parametros = flow_config.get("parametros", "")
            paginacion = flow_config.get("paginacion", False)

            params = {
                "query_desc": query_desc,
                "no_paginar": not paginacion,
            }
            if parametros:
                params["parametros"] = parametros

            status, raw = connector.get(endpoint=query_desc, params=params)
            if not status:
                self.logger.error(f"Error obteniendo datos para '{flow_name}': {raw}")
                return []

            if not raw:
                self.logger.info(f"Flow '{flow_name}': sin registros del conector")
                return []

            return normalize_fn(raw, flow_config)

        except Exception as e:
            self.logger.error(f"get_flow: error inesperado en '{flow_name}': {e}")
            return []

    def _apply_mapping(self, row: dict, mapping: dict) -> dict:
          if not mapping:
              return row
          mapped = {}
          mapped_keys = set()
          for key_api, key_canon in mapping.items():
              if key_api in row:
                  mapped[key_canon] = row[key_api]
                  mapped_keys.add(key_api)
          for key, value in row.items():
              if key not in mapped_keys:
                  mapped[key] = value
          return mapped

    def _apply_hardcodes(self, row: dict, hardcodes: dict) -> dict:
        if not hardcodes:
            return row
        for campo, valor in hardcodes.items():
            row[campo] = valor
        return row

    def _apply_conditionals(self, row: dict, conditionals: list) -> dict:
        if not conditionals:
            return row

        for cond in conditionals:
            tipo = cond.get("tipo", "")
            campo_destino = cond.get("campo_destino", "")

            if tipo == "reglas":
                campo_origen = cond.get("campo_origen", "")
                reglas = cond.get("reglas", [])
                default = cond.get("default")
                valor_origen = str(row.get(campo_origen, "")).strip()

                resultado = default
                for regla in reglas:
                    if str(regla.get("si", "")).strip() == valor_origen:
                        if "entonces" not in regla:
                            self.logger.error(
                                f"_apply_conditionals: regla sin 'entonces' para "
                                f"campo_destino '{campo_destino}' — regla: {regla}"
                            )
                            break
                        resultado = regla["entonces"]
                        break

                if resultado is not None:
                    row[campo_destino] = resultado
                else:
                    self.logger.warning(
                        f"_apply_conditionals: ninguna regla matcheó para "
                        f"campo_destino '{campo_destino}' y no hay default configurado"
                    )

            elif tipo == "funcion":
                nombre_fn = cond.get("funcion", "")
                params = cond.get("params", {})
                fn = get_determination_function(nombre_fn, logger=self.logger)
                if fn:
                    row[campo_destino] = fn(row, params, logger=self.logger)

        return row

    def _normalize_items(self, raw: list, flow_config: dict) -> list:
        mapping = flow_config.get("mapping", {})
        hardcodes = flow_config.get("hardcodes", {})
        conditionals = flow_config.get("conditionals", [])
        campos_float = {"peso", "volumen", "costo", "precio", "iva"}
        campos_int = {"vence", "use_expiration_date", "expiration_time",
                      "ind_compra", "ind_venta", "ind_manufactura"}

        results = []
        fallidos = []

        for row in raw:
            try:
                row = self._apply_mapping(row, mapping)
                row = self._apply_hardcodes(row, hardcodes)
                row = self._apply_conditionals(row, conditionals)
                row = clean_row(row)

                valid, reason = validate_record(row, "items", logger=self.logger)
                if not valid:
                    fallidos.append({"ref": row.get("referencia", "?"), "desc": row.get("descripcion", "?"), "razon": reason})
                    continue

                for campo in campos_float & row.keys():
                    row[campo] = to_float(row[campo], logger=self.logger, field_name=campo)

                for campo in campos_int & row.keys():
                    row[campo] = to_int(row[campo], logger=self.logger, field_name=campo)

                results.append(row)

            except Exception as e:
                fallidos.append({"ref": row.get("referencia", "?"), "desc": row.get("descripcion", "?"), "razon": str(e)})
                continue

        self.logger.info(
            f"_normalize_items: {len(results)}/{len(raw)} registros válidos"
        )
        if fallidos:
            self.logger.warning(f"_normalize_items: {len(fallidos)} registros descartados:")
            for f in fallidos:
                self.logger.warning(f"  - {f['ref']} ({f['desc']}): {f['razon']}")
        return results

    def _normalize_partners(self, raw: list, flow_config: dict) -> list:
        mapping = flow_config.get("mapping", {})
        hardcodes = flow_config.get("hardcodes", {})
        conditionals = flow_config.get("conditionals", [])

        results = []
        fallidos = []

        for row in raw:
            try:
                row = self._apply_mapping(row, mapping)
                row = self._apply_hardcodes(row, hardcodes)
                row = self._apply_conditionals(row, conditionals)
                row = clean_row(row)

                valid, reason = validate_record(row, "partners", logger=self.logger)
                if not valid:
                    fallidos.append({"nombre": row.get("nombre", "?"), "id": row.get("identificacion", "?"), "razon": reason})
                    continue

                results.append(row)

            except Exception as e:
                fallidos.append({"nombre": row.get("nombre", "?"), "id": row.get("identificacion", "?"), "razon": str(e)})
                continue

        self.logger.info(
            f"_normalize_partners: {len(results)}/{len(raw)} registros válidos"
        )
        if fallidos:
            self.logger.warning(f"_normalize_partners: {len(fallidos)} registros descartados:")
            for f in fallidos:
                self.logger.warning(f"  - {f['nombre']} ({f['id']}): {f['razon']}")
        return results

    def _normalize_purchases(self, raw: list, flow_config: dict) -> list:
        mapping = flow_config.get("mapping", {})
        hardcodes = flow_config.get("hardcodes", {})
        conditionals = flow_config.get("conditionals", [])
        campos_float = {"cantidad", "precio_unitario", "impuesto"}
        campos_fecha = {"fecha_entrega", "fecha_compra"}

        results = []
        fallidos = []

        for row in raw:
            try:
                row = self._apply_mapping(row, mapping)
                row = self._apply_hardcodes(row, hardcodes)
                row = self._apply_conditionals(row, conditionals)
                row = clean_row(row)

                valid, reason = validate_record(row, "purchases", logger=self.logger)
                if not valid:
                    fallidos.append({"compra": row.get("compra", "?"), "producto": row.get("producto", "?"), "razon": reason})
                    continue

                for campo in campos_float & row.keys():
                    row[campo] = to_float(row[campo], logger=self.logger, field_name=campo)

                for campo in campos_fecha & row.keys():
                    row[campo] = parse_fecha(row[campo], logger=self.logger)

                results.append(row)

            except Exception as e:
                fallidos.append({"compra": row.get("compra", "?"), "producto": row.get("producto", "?"), "razon": str(e)})
                continue

        self.logger.info(
            f"_normalize_purchases: {len(results)}/{len(raw)} registros válidos"
        )
        if fallidos:
            self.logger.warning(f"_normalize_purchases: {len(fallidos)} registros descartados:")
            for f in fallidos:
                self.logger.warning(f"  - Compra {f['compra']}, producto {f['producto']}: {f['razon']}")
        return results

    def _normalize_sales(self, raw: list, flow_config: dict) -> list:
        mapping = flow_config.get("mapping", {})
        hardcodes = flow_config.get("hardcodes", {})
        conditionals = flow_config.get("conditionals", [])
        campos_float = {"cantidad_pedida", "precio_unitario", "impuesto"}
        campos_fecha = {"fecha_pedido", "fecha_entrega"}

        results = []
        fallidos = []

        for row in raw:
            try:
                row = self._apply_mapping(row, mapping)
                row = self._apply_hardcodes(row, hardcodes)
                row = self._apply_conditionals(row, conditionals)
                row = clean_row(row)

                valid, reason = validate_record(row, "sales", logger=self.logger)
                if not valid:
                    fallidos.append({"pedido": row.get("pedido", "?"), "producto": row.get("producto", "?"), "razon": reason})
                    continue

                for campo in campos_float & row.keys():
                    row[campo] = to_float(row[campo], logger=self.logger, field_name=campo)

                for campo in campos_fecha & row.keys():
                    row[campo] = parse_fecha(row[campo], logger=self.logger)

                results.append(row)

            except Exception as e:
                fallidos.append({"pedido": row.get("pedido", "?"), "producto": row.get("producto", "?"), "razon": str(e)})
                continue

        self.logger.info(
            f"_normalize_sales: {len(results)}/{len(raw)} registros válidos"
        )
        if fallidos:
            self.logger.warning(f"_normalize_sales: {len(fallidos)} registros descartados:")
            for f in fallidos:
                self.logger.warning(f"  - Pedido {f['pedido']}, producto {f['producto']}: {f['razon']}")
        return results