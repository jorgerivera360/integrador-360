"""
TransformWS — Transform SIESA WS
Hereda: Transform
Fase: 3 — Transform Layer
"""
from config.logger import IntegradorLogger
from transform.base import Transform, TransformError
from transform.utils.normalize import normalize


class TransformWS(Transform):
    def __init__(self, config: dict):
        self.client_id = config["client_id"]
        self.logger = IntegradorLogger(client_id=self.client_id)
        self.descartados = []

    def get_flow(self, connector, flow_name: str, flow_type: str, flow_config: dict) -> list:
        self.descartados = []

        try:
            sql = flow_config.get("sql", "")
            endpoint = flow_config.get("endpoint", "")

            if endpoint:
                status, raw = connector.get(endpoint=endpoint, params={})
            elif sql:
                status, raw = connector.get(
                    endpoint="EjecutarConsultaXML", params={"sql": sql}
                )
            else:
                raise TransformError(
                    f"Flow '{flow_name}': no hay SQL ni endpoint configurado"
                )

            if not status:
                raise TransformError(
                    f"Flow '{flow_name}': error obteniendo datos del ERP — {raw}"
                )

            if not raw:
                self.logger.info(f"Flow '{flow_name}': sin registros del conector")
                return []

            return normalize(raw, flow_config, flow_type,
                             self.logger, self.descartados)

        except TransformError:
            raise
        except Exception as e:
            raise TransformError(
                f"Flow '{flow_name}': error inesperado en get_flow — {e}"
            ) from e
