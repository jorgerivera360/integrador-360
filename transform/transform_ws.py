"""
TransformWS — Transform SIESA WS
Responsabilidades:
  - get_flow() — llama al conector y normaliza los datos
  - _apply_hardcodes() — inyecta valores fijos del flujo
  - _normalize_items() — limpieza + tipado + validación de productos
  - _normalize_partners() — limpieza + validación de clientes/proveedores
  - _normalize_purchases() — limpieza + tipado + validación de compras/entradas
  - _normalize_sales() — limpieza + tipado + validación de ventas/salidas
Hereda: Transform
Fase: 3 — Transform Layer
"""
from config.logger import IntegradorLogger
from transform.base import Transform
from transform.utils.helpers import (clean_row, validate_record, to_float, to_int, parse_fecha)
from transform.utils.documentos import preparar_documentos, procesar_fila

class TransformWS(Transform):
    def __init__(self, config: dict):
        self.client_id = config["client_id"]
        self.logger    = IntegradorLogger(client_id=self.client_id)

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
            self.logger.error(f"flow_type no soportado en TransformWS: '{flow_type}'")
            return []

        try:
            sql = flow_config.get("sql", "")
            endpoint = flow_config.get("endpoint", "")

            if endpoint:
                status, raw = connector.get(endpoint=endpoint, params={})
            elif sql:
                status, raw = connector.get(endpoint="EjecutarConsultaXML", params={"sql": sql})
            else:
                self.logger.error(f"No hay SQL ni endpoint configurado para flow '{flow_name}'")
                return []
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

    def _apply_hardcodes(self, row: dict, hardcodes: dict) -> dict:
        if not hardcodes:
            return row
        for campo, valor in hardcodes.items():
            row[campo] = valor
        return row

# Maestros

    def _normalize_items(self, raw: list, flow_config: dict) -> list:
        campos_float = {"peso", "volumen", "costo", "precio", "iva"}
        campos_int = {"vence", "use_expiration_date", "expiration_time",
                        "ind_compra", "ind_venta", "ind_manufactura"}
        hardcodes = flow_config.get("hardcodes", {})

        docs_activos, stats_docs = preparar_documentos(
            flow_config.get("documentos"), logger=self.logger
        )

        results = []
        fallidos = []

        for row in raw:
            try:
                row = self._apply_hardcodes(row, hardcodes)

                row = procesar_fila(row, docs_activos, stats_docs, logger=self.logger)
                if row is None:
                    continue

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
        if docs_activos:
            detalle = ", ".join(
                f"{cod}: {d['aceptados']} ok / {d['descartados']} descartados"
                for cod, d in stats_docs.items() if not cod.startswith("_")
            )
            self.logger.info(
                f"_normalize_items: documentos — {detalle}, "
                f"sin documento: {stats_docs['_sin_documento']}"
            )
        return results

    def _normalize_partners(self, raw: list, flow_config: dict) -> list:
        hardcodes = flow_config.get("hardcodes", {})

        docs_activos, stats_docs = preparar_documentos(
            flow_config.get("documentos"), logger=self.logger
        )

        results = []
        fallidos = []

        for row in raw:
            try:
                row = self._apply_hardcodes(row, hardcodes)

                row = procesar_fila(row, docs_activos, stats_docs, logger=self.logger)
                if row is None:
                    continue

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
        if docs_activos:
            detalle = ", ".join(
                f"{cod}: {d['aceptados']} ok / {d['descartados']} descartados"
                for cod, d in stats_docs.items() if not cod.startswith("_")
            )
            self.logger.info(
                f"_normalize_partners: documentos — {detalle}, "
                f"sin documento: {stats_docs['_sin_documento']}"
            )
        return results

# Transacciones

    def _normalize_purchases(self, raw: list, flow_config: dict) -> list:

        campos_float = {"cantidad", "precio_unitario", "impuesto"}
        campos_fecha = {"fecha_entrega"}
        hardcodes = flow_config.get("hardcodes", {})

        docs_activos, stats_docs = preparar_documentos(
            flow_config.get("documentos"), logger=self.logger
        )

        results = []
        fallidos = []

        for row in raw:
            try:
                row = self._apply_hardcodes(row, hardcodes)

                row = procesar_fila(row, docs_activos, stats_docs, logger=self.logger)
                if row is None:
                    continue

                row = clean_row(row)

                valid, reason = validate_record(row, "purchases", logger=self.logger)
                if not valid:
                    fallidos.append({"compra": row.get("compra", "?"), "producto": row.get("producto", "?"), "razon": reason})
                    continue

                for campo in campos_float & row.keys():
                    row[campo] = to_float(row[campo], logger = self.logger, field_name = campo)

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
        if docs_activos:
            detalle = ", ".join(
                f"{cod}: {d['aceptados']} ok / {d['descartados']} descartados"
                for cod, d in stats_docs.items() if not cod.startswith("_")
            )
            self.logger.info(
                f"_normalize_purchases: documentos — {detalle}, "
                f"sin documento: {stats_docs['_sin_documento']}"
            )
        return results

    def _normalize_sales(self, raw: list, flow_config: dict) -> list:
        campos_float = {"cantidad_pedida", "precio_unitario", "impuesto"}
        campos_fecha = {"fecha_pedido"}
        hardcodes = flow_config.get("hardcodes", {})

        docs_activos, stats_docs = preparar_documentos(
            flow_config.get("documentos"), logger=self.logger
        )

        results = []
        fallidos = []

        for row in raw:
            try:
                row = self._apply_hardcodes(row, hardcodes)

                row = procesar_fila(row, docs_activos, stats_docs, logger=self.logger)
                if row is None:
                    continue

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
        if docs_activos:
            detalle = ", ".join(
                f"{cod}: {d['aceptados']} ok / {d['descartados']} descartados"
                for cod, d in stats_docs.items() if not cod.startswith("_")
            )
            self.logger.info(
                f"_normalize_sales: documentos — {detalle}, "
                f"sin documento: {stats_docs['_sin_documento']}"
            )
        return results