"""
TransformWS — Transform SIESA WS
Responsabilidades:
  - _build_sql() — construye SQL con sql_params y siesa_mapping
  - get_flow() — llama al conector y normaliza los datos
Hereda: TransformBase
Fase: 3 — Transform Layer
"""
from config.logger import IntegradorLogger
from transform.base import Transform
from transform.utils.helpers import (clean_row, validate_record, to_float, to_int)

class TransformWS(Transform):
    def __init__(self, config: dict):
        self.client_id = config["client_id"]
        self.logger    = IntegradorLogger(client_id=self.client_id)

    def get_flow(self, connector, flow_name: str, flow_config: dict) -> list:
        normalize_map = {
            "productos": self._normalize_productos,
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

    def _normalize_productos(self, raw: list, flow_config: dict) -> list:
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
                self.logger.error(f"_normalize_productos: error procesando registro '{ref}': {e}")
                continue

        self.logger.info(
            f"_normalize_productos: {len(results)}/{len(raw)} registros válidos"
        )
        return results