"""
TransformConnekta — Transform SIESA Connekta
Hereda: Transform
Fase: 3 — Transform Layer
"""
from config.logger import IntegradorLogger
from transform.base import Transform, TransformError
from transform.utils.helpers import resolve_parametros
from transform.utils.normalize import normalize


class TransformConnekta(Transform):
    def __init__(self, config: dict):
        self.client_id = config["client_id"]
        self.logger = IntegradorLogger(client_id=self.client_id)
        self.descartados = []

    def get_flow(self, connector, flow_name: str, flow_type: str, flow_config: dict) -> list:
        self.descartados = []

        try:
            query_desc = flow_config.get("query_desc", "")
            if not query_desc:
                raise TransformError(
                    f"Flow '{flow_name}': no hay query_desc configurado"
                )

            parametros = flow_config.get("parametros", "")
            paginacion = flow_config.get("paginacion", False)

            params = {
                "query_desc": query_desc,
                "no_paginar": not paginacion,
            }
            if parametros:
                parametros = resolve_parametros(parametros, logger=self.logger)
                params["parametros"] = parametros

            status, raw = connector.get(endpoint=query_desc, params=params)
            if not status:
                raise TransformError(
                    f"Flow '{flow_name}': error obteniendo datos del ERP — {raw}"
                )

            if not raw:
                self.logger.info(f"Flow '{flow_name}': sin registros del conector")
                return []

            return normalize(raw, flow_config, flow_type,
                             self.logger, self.descartados,
                             use_conditionals=True)

        except TransformError:
            raise
        except Exception as e:
            raise TransformError(
                f"Flow '{flow_name}': error inesperado en get_flow — {e}"
            ) from e
