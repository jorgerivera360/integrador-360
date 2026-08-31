"""
TransformSAP — Transform SAP B1
Responsabilidades:
  - get_flow() — login SAP, llama al conector y normaliza los datos
  - _flatten_lines() — aplana arrays anidados (DocumentLines, StockTransferLines, BPAddresses)
  - _apply_mapping() — renombra keys del dict según mapping combinado (header + líneas)
  - _apply_hardcodes() — inyecta valores fijos según flow_config["hardcodes"]
  - _apply_conditionals() — evalúa reglas simples o funciones del catálogo
Hereda: Transform
Fase: 3 — Transform Layer
"""
from config.logger import IntegradorLogger
from transform.base import Transform
from transform.utils.determination_functions import get_determination_function
from transform.utils.helpers import (clean_row, validate_record, to_float, to_int, parse_fecha, resolve_parametros)


class TransformSAP(Transform):
    def __init__(self, config: dict):
        self.client_id = config["client_id"]
        self.logger = IntegradorLogger(client_id=self.client_id)
        self._categorias = {}

    def get_flow(self, connector, flow_name: str, flow_type: str, flow_config: dict) -> list:
        normalize_map = {
            "items": self._normalize_items,
            "customer": self._normalize_partners,
            "supplier": self._normalize_partners,
            "purchases": self._normalize_purchases,
            "sales": self._normalize_sales,
        }

        normalize_fn = normalize_map.get(flow_type)
        if not normalize_fn:
            self.logger.error(f"flow_type no soportado en TransformSAP: '{flow_type}'")
            return []

        try:
            if not connector.session_id:
                if not connector.login_api():
                    self.logger.error("No se pudo autenticar en SAP")
                    return []

            endpoint = flow_config.get("endpoint", "")
            if not endpoint:
                self.logger.error(f"No hay endpoint configurado para flow '{flow_name}'")
                return []

            filter_str = flow_config.get("filter", "")
            params = {}
            if filter_str:
                filter_str = resolve_parametros(filter_str, formato="%Y-%m-%d")
                params["filter"] = filter_str

            if flow_type == "items":
                if not self._prefetch_categories(connector):
                    return []

            status, raw = connector.get(endpoint=endpoint, params=params)
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

    def _prefetch_categories(self, connector):
        max_retries = 3
        for intento in range(1, max_retries + 1):
            status, categorias_raw = connector.get(endpoint="ItemGroups", params={})
            if status and categorias_raw:
                self._categorias = {
                    c.get("Number"): c.get("GroupName", "Sin categoría")
                    for c in categorias_raw
                }
                self.logger.info(f"Pre-fetch categorías: {len(self._categorias)} grupos")
                return True
            self.logger.warning(
              f"Pre-fetch categorías: intento {intento}/{max_retries} falló"
          )

        self.logger.error(
          "No se pudieron obtener las categorías de SAP después de "
          f"{max_retries} intentos — Service Layer posiblemente caído"
        ) 
        self._categorias = {}
        return False        

    def _flatten_lines(self, raw: list, mapping_lineas: dict) -> list:
        if not mapping_lineas:
            return raw

        origen = mapping_lineas.get("origen", "")
        if not origen:
            return raw

        flattened = []
        for doc in raw:
            header = {k: v for k, v in doc.items() if k != origen}
            lines = doc.get(origen, [])
            if not lines:
                doc_id = doc.get("DocNum", doc.get("DocEntry", "?"))
                self.logger.warning(
                    f"_flatten_lines: documento {doc_id} sin líneas en '{origen}' — descartado"
                )
                continue
            for line in lines:
                row = {**header}
                row.update(line)
                flattened.append(row)

        self.logger.info(
            f"_flatten_lines: {len(raw)} documentos → {len(flattened)} filas ({origen})"
        )
        return flattened

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
                # Resolver categoría antes del mapping
                group_code = row.get("ItemsGroupCode")
                if group_code is not None and self._categorias:
                    row["ItemsGroupCode_resolved"] = self._categorias.get(
                        group_code, "Sin categoría"
                    )

                row = self._apply_mapping(row, mapping)
                row = self._apply_hardcodes(row, hardcodes)
                row = self._apply_conditionals(row, conditionals)
                row = clean_row(row)

                valid, reason = validate_record(row, "items", logger=self.logger)
                if not valid:
                    fallidos.append({"ref": row.get("referencia", row.get("ItemCode", "?")), "desc": row.get("descripcion", row.get("ItemName", "?")), "razon": reason})
                    continue

                for campo in campos_float & row.keys():
                    row[campo] = to_float(row[campo], logger=self.logger, field_name=campo)

                for campo in campos_int & row.keys():
                    row[campo] = to_int(row[campo], logger=self.logger, field_name=campo)

                results.append(row)

            except Exception as e:
                fallidos.append({"ref": row.get("referencia", row.get("ItemCode", "?")), "desc": row.get("descripcion", row.get("ItemName", "?")), "razon": str(e)})
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
        mapping_lineas = flow_config.get("mapping_lineas", {})
        hardcodes = flow_config.get("hardcodes", {})
        conditionals = flow_config.get("conditionals", [])

        # Combinar mapping header + mapping líneas
        combined_mapping = {**mapping}
        if mapping_lineas:
            combined_mapping.update(mapping_lineas.get("campos", {}))

        # Aplanar si hay mapping_lineas (clientes con BPAddresses)
        rows = self._flatten_lines(raw, mapping_lineas)

        results = []
        fallidos = []

        for row in rows:
            try:
                row = self._apply_mapping(row, combined_mapping)
                row = self._apply_hardcodes(row, hardcodes)
                row = self._apply_conditionals(row, conditionals)
                row = clean_row(row)

                valid, reason = validate_record(row, "partners", logger=self.logger)
                if not valid:
                    fallidos.append({"nombre": row.get("nombre", row.get("CardName", "?")), "id": row.get("identificacion", row.get("CardCode", "?")), "razon": reason})
                    continue

                results.append(row)

            except Exception as e:
                fallidos.append({"nombre": row.get("nombre", row.get("CardName", "?")), "id": row.get("identificacion", row.get("CardCode", "?")), "razon": str(e)})
                continue

        self.logger.info(
            f"_normalize_partners: {len(results)}/{len(rows)} registros válidos"
        )
        if fallidos:
            self.logger.warning(f"_normalize_partners: {len(fallidos)} registros descartados:")
            for f in fallidos:
                self.logger.warning(f"  - {f['nombre']} ({f['id']}): {f['razon']}")
        return results

    def _normalize_purchases(self, raw: list, flow_config: dict) -> list:
        mapping = flow_config.get("mapping", {})
        mapping_lineas = flow_config.get("mapping_lineas", {})
        hardcodes = flow_config.get("hardcodes", {})
        conditionals = flow_config.get("conditionals", [])
        campos_float = {"cantidad", "precio_unitario", "impuesto"}
        campos_fecha = {"fecha_entrega"}

        combined_mapping = {**mapping}
        if mapping_lineas:
            combined_mapping.update(mapping_lineas.get("campos", {}))

        rows = self._flatten_lines(raw, mapping_lineas)

        results = []
        fallidos = []

        for row in rows:
            try:
                row = self._apply_mapping(row, combined_mapping)
                row = self._apply_hardcodes(row, hardcodes)
                row = self._apply_conditionals(row, conditionals)
                row = clean_row(row)

                valid, reason = validate_record(row, "purchases", logger=self.logger)
                if not valid:
                    fallidos.append({"compra": row.get("compra", row.get("DocNum", "?")), "producto": row.get("producto", row.get("ItemCode", "?")), "razon": reason})
                    continue

                for campo in campos_float & row.keys():
                    row[campo] = to_float(row[campo], logger=self.logger, field_name=campo)

                for campo in campos_fecha & row.keys():
                    row[campo] = parse_fecha(row[campo], logger=self.logger)

                results.append(row)

            except Exception as e:
                fallidos.append({"compra": row.get("compra", row.get("DocNum", "?")), "producto": row.get("producto", row.get("ItemCode", "?")), "razon": str(e)})
                continue

        self.logger.info(
            f"_normalize_purchases: {len(results)}/{len(rows)} registros válidos"
        )
        if fallidos:
            self.logger.warning(f"_normalize_purchases: {len(fallidos)} registros descartados:")
            for f in fallidos:
                self.logger.warning(f"  - Compra {f['compra']}, producto {f['producto']}: {f['razon']}")
        return results

    def _normalize_sales(self, raw: list, flow_config: dict) -> list:
        mapping = flow_config.get("mapping", {})
        mapping_lineas = flow_config.get("mapping_lineas", {})
        hardcodes = flow_config.get("hardcodes", {})
        conditionals = flow_config.get("conditionals", [])
        campos_float = {"cantidad_pedida", "precio_unitario", "impuesto"}
        campos_fecha = {"fecha_pedido"}

        combined_mapping = {**mapping}
        if mapping_lineas:
            combined_mapping.update(mapping_lineas.get("campos", {}))

        rows = self._flatten_lines(raw, mapping_lineas)

        results = []
        fallidos = []

        for row in rows:
            try:
                row = self._apply_mapping(row, combined_mapping)
                row = self._apply_hardcodes(row, hardcodes)
                row = self._apply_conditionals(row, conditionals)
                row = clean_row(row)

                valid, reason = validate_record(row, "sales", logger=self.logger)
                if not valid:
                    fallidos.append({"pedido": row.get("pedido", row.get("DocNum", "?")), "producto": row.get("producto", row.get("ItemCode", "?")), "razon": reason})
                    continue

                for campo in campos_float & row.keys():
                    row[campo] = to_float(row[campo], logger=self.logger, field_name=campo)

                for campo in campos_fecha & row.keys():
                    row[campo] = parse_fecha(row[campo], logger=self.logger)

                results.append(row)

            except Exception as e:
                fallidos.append({"pedido": row.get("pedido", row.get("DocNum", "?")), "producto": row.get("producto", row.get("ItemCode", "?")), "razon": str(e)})
                continue

        self.logger.info(
            f"_normalize_sales: {len(results)}/{len(rows)} registros válidos"
        )
        if fallidos:
            self.logger.warning(f"_normalize_sales: {len(fallidos)} registros descartados:")
            for f in fallidos:
                self.logger.warning(f"  - Pedido {f['pedido']}, producto {f['producto']}: {f['razon']}")
        return results