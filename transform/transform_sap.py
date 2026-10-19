"""
TransformSAP — Transform SAP B1
Hereda: Transform
Fase: 3 — Transform Layer
"""
from config.logger import IntegradorLogger
from transform.base import Transform, TransformError
from transform.utils.helpers import resolve_parametros
from transform.utils.normalize import normalize


class TransformSAP(Transform):
    def __init__(self, config: dict):
        self.client_id = config["client_id"]
        self.logger = IntegradorLogger(client_id=self.client_id)
        self.descartados = []
        self._categorias = {}

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
            f"No se pudieron obtener las categorías de SAP después de "
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

    def _resolve_categories(self, raw: list):
        if not self._categorias:
            return
        for row in raw:
            group_code = row.get("ItemsGroupCode")
            if group_code is not None:
                row["ItemsGroupCode_resolved"] = self._categorias.get(
                    group_code, "Sin categoría"
                )

    def get_flow(self, connector, flow_name: str, flow_type: str, flow_config: dict) -> list:
        self.descartados = []

        try:
            if not connector.session_id:
                if not connector.login_api():
                    raise TransformError(
                        f"Flow '{flow_name}': no se pudo autenticar en SAP"
                    )

            endpoint = flow_config.get("endpoint", "")
            if not endpoint:
                raise TransformError(
                    f"Flow '{flow_name}': no hay endpoint configurado"
                )

            filter_str = flow_config.get("filter", "")
            params = {}
            if filter_str:
                filter_str = resolve_parametros(filter_str, formato="%Y-%m-%d")
                params["filter"] = filter_str

            if flow_type == "items":
                if not self._prefetch_categories(connector):
                    raise TransformError(
                        f"Flow '{flow_name}': no se pudieron obtener las categorias "
                        f"de SAP tras 3 intentos"
                    )

            status, raw = connector.get(endpoint=endpoint, params=params)
            if not status:
                raise TransformError(
                    f"Flow '{flow_name}': error obteniendo datos del ERP — {raw}"
                )

            if not raw:
                self.logger.info(f"Flow '{flow_name}': sin registros del conector")
                return []

            # Pasos SAP-específicos antes del normalize genérico
            mapping_lineas = flow_config.get("mapping_lineas", {})
            raw = self._flatten_lines(raw, mapping_lineas)

            if flow_type == "items":
                self._resolve_categories(raw)

            # Combinar mapping header + mapping líneas
            if mapping_lineas:
                combined = {**flow_config.get("mapping", {})}
                combined.update(mapping_lineas.get("campos", {}))
                flow_config = {**flow_config, "mapping": combined}

            return normalize(raw, flow_config, flow_type,
                             self.logger, self.descartados,
                             use_conditionals=True)

        except TransformError:
            raise
        except Exception as e:
            raise TransformError(
                f"Flow '{flow_name}': error inesperado en get_flow — {e}"
            ) from e
