"""
TransformWS — Transform SIESA WS
Responsabilidades:
  - get_flow() — llama al conector y normaliza los datos
  - _normalize_items() — limpieza + tipado + validación de productos
  - _normalize_partners() — limpieza + validación de clientes/proveedores
  - _normalize_purchases() — limpieza + tipado + validación de compras/entradas
Hereda: Transform
Fase: 3 — Transform Layer
"""
from config.logger import IntegradorLogger
from transform.base import Transform
from transform.utils.helpers import (clean_row, validate_record, to_float, to_int, parse_fecha)

class TransformWS(Transform):
    def __init__(self, config: dict):  
        self.client_id = config["client_id"]
        self.logger    = IntegradorLogger(client_id=self.client_id)

    def get_flow(self, connector, flow_name: str, flow_config: dict) -> list:
        normalize_map = {
            # Maestros
            "items": self._normalize_items,
            "partners": self._normalize_partners,
            # Transacciones entrada
            "compras": self._normalize_purchases,
            "compras_importacion": self._normalize_purchases,
            "transferencia_entrada": self._normalize_purchases,
            "traslados_entrada": self._normalize_purchases,
            "entrada_mercancia": self._normalize_purchases,
            "entrada_directa": self._normalize_purchases,
            "devolucion_in": self._normalize_purchases,
            "nota_credito": self._normalize_purchases,
            # Transacciones salida
            "ventas": self._normalize_sales,
            "facturas": self._normalize_sales,
            "transferencia_salida": self._normalize_sales,
            "transferencia_interna": self._normalize_sales,
            "salida_mercancia": self._normalize_sales,
            "salida_directa": self._normalize_sales,
            "devolucion_out": self._normalize_sales,
            "requisiciones": self._normalize_sales,
        }

        normalize_fn = normalize_map.get(flow_name)
        if not normalize_fn:
            self.logger.error(f"Flujo no soportado en TransformWS: '{flow_name}'")
            return []

        try:
            sql = flow_config.get("sql", "")
            if not sql:
                self.logger.error(f"No hay SQL configurado para flow '{flow_name}'")
                return []
            status, raw = connector.get(endpoint="EjecutarConsultaXML", params={"sql": sql})
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

# Maestros

    def _normalize_items(self, raw: list, flow_config: dict) -> list:
        campos_float = {"peso", "volumen", "costo", "precio", "iva"}
        campos_int = {"vence", "use_expiration_date", "expiration_time",
                        "ind_compra", "ind_venta", "ind_manufactura"}

        results = []

        for row in raw:
            try:
                row = clean_row(row)

                valid, reason = validate_record(row, "items", logger=self.logger)
                if not valid:
                    continue

                for campo in campos_float & row.keys():
                    row[campo] = to_float(row[campo], logger=self.logger, field_name=campo)

                for campo in campos_int & row.keys():
                    row[campo] = to_int(row[campo], logger=self.logger, field_name=campo)

                results.append(row)

            except Exception as e:
                ref = row.get("referencia", "?")
                self.logger.error(f"_normalize_items: error procesando registro '{ref}': {e}")
                continue

        self.logger.info(
            f"_normalize_items: {len(results)}/{len(raw)} registros válidos"
        )
        return results

    def _normalize_partners(self, raw: list, flow_config: dict) -> list:
        results = []

        for row in raw:
            try:
                row = clean_row(row)

                valid, reason = validate_record(row, "partners", logger=self.logger)
                if not valid:
                    continue

                results.append(row)

            except Exception as e:
                nombre = row.get("nombre", "?")
                self.logger.error(f"_normalize_partners: error procesando '{nombre}': {e}")
                continue

        self.logger.info(
            f"_normalize_partners: {len(results)}/{len(raw)} registros válidos"
        )
        return results

# Transacciones

    def _normalize_purchases(self, raw: list, flow_config: dict) -> list:

        campos_float = {"cantidad", "precio_unitario", "impuesto"}
        campos_fecha = {"fecha_entrega"}

        results = []

        for row in raw:
            try:
                row = clean_row(row)

                valid, reason = validate_record(row, "purchases", logger=self.logger)
                if not valid:
                    continue

                for campo in campos_float & row.keys():
                    row[campo] = to_float(row[campo], logger = self.logger, field_name = campo)

                for campo in campos_fecha & row.keys():
                    row[campo] = parse_fecha(row[campo], logger=self.logger)

                results.append(row)

            except Exception as e:
                compra = row.get("compra", "?")
                self.logger.error(f"_normalize_purchases: error procesando '{compra}': {e}")
                continue

        self.logger.info(
            f"_normalize_purchases: {len(results)}/{len(raw)} registros válidos"
        )
        return results

    def _normalize_sales(self, raw: list, flow_config: dict) -> list:
        campos_float = {"cantidad_pedida", "precio_unitario", "impuesto"}
        campos_fecha = {"fecha_pedido"}

        results = []

        for row in raw:
            try:
                row = clean_row(row)

                valid, reason = validate_record(row, "sales", logger=self.logger)
                if not valid:
                    continue

                for campo in campos_float & row.keys():
                    row[campo] = to_float(row[campo], logger=self.logger, field_name=campo)

                for campo in campos_fecha & row.keys():
                    row[campo] = parse_fecha(row[campo], logger=self.logger)

                results.append(row)

            except Exception as e:
                pedido = row.get("pedido", "?")
                self.logger.error(f"_normalize_sales: error procesando '{pedido}': {e}")
                continue

        self.logger.info(
            f"_normalize_sales: {len(results)}/{len(raw)} registros válidos"
        )
        return results