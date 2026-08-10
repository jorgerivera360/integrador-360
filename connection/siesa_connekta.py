"""
SiesaConnekta — Conector SIESA Connekta
Responsabilidades:
  - Conecta con SIESA Connekta via REST/JSON
  - Detecta automáticamente formato Datos vs Table
  - Maneja paginación automática
  - Implementa get() y test_connection()
Hereda: ERPConnector
Fase: 2 — Connection Layer
"""
import requests
from config.logger import IntegradorLogger
from connection.base import ERPConnector

class SiesaConnekta(ERPConnector):

    def __init__(self, config: dict):
        self.url         = config["erp"]["url"]
        self.url_qa      = config["erp"].get("url_qa", "")
        self.id_compania = config["erp"]["idcompania"]
        self.conni_key   = config["erp"]["connikey"]
        self.conni_token = config["erp"]["connitoken"]
        self.client_id   = config["client_id"]
        self.logger      = IntegradorLogger(client_id=self.client_id)

    def _get_headers(self) -> dict:
        return {
            "ConniKey": self.conni_key,
            "ConniToken": self.conni_token,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    def get(self, endpoint: str, params: dict = {}) -> tuple:
        # Se obtiene el query del parámetro o directamente del endpoint
        query_desc = params.get("query_desc", endpoint)
        if not query_desc:
            self.logger.error("No se proporcionó la descripción del query")
            return False, "Falta la consulta de Siesa"

        single_page = params.get("single_page", False)
        tam_pag = params.get("tam_pag", 100)
        no_paginar = params.get("no_paginar", False)

        array_items = []
        num_pag = 1

        try:
            while True:
                # Construcción dinámica de la URL con query params
                url = f"{self.url}?idCompania={self.id_compania}&descripcion={query_desc}"
                if not no_paginar:
                    url += f"&paginacion=numPag={num_pag}|tamPag={tam_pag}"

                parametros = params.get("parametros", "")
                if parametros:
                    url += f"&parametros={parametros}"

                self.logger.info(f"Consumiendo consulta Siesa Connekta: {query_desc} - Página: {num_pag}")
                response = requests.get(url, headers=self._get_headers(), verify=True)
                response.raise_for_status()

                json_response = response.json()

                if json_response.get("codigo") == 0:
                    detalle = json_response.get("detalle", {})
                    
                    # Detección automática formato Datos vs Table
                    items = detalle.get("Datos")
                    if items is None:
                        items = detalle.get("Table")
                    if items is None:
                        items = []

                    if not items:
                        break

                    array_items.extend(items)

                    total_paginas = detalle.get("total_páginas", 1)
                    if no_paginar or single_page or num_pag >= total_paginas or len(items) < tam_pag:
                        break

                    num_pag += 1
                else:
                    msg = json_response.get('mensaje', 'Sin mensaje')
                    self.logger.error(f"Error devuelto por Siesa Connekta: {msg}")
                    return False, f"Siesa error: {msg}"

            self.logger.info(f"Consulta a {query_desc} exitosa — {len(array_items)} registros crudos traídos")
            return True, array_items

        except Exception as e:
            self.logger.error(f"Error al traer {query_desc} de Siesa Connekta: {e}")
            return False, str(e)
    
    def test_connection(self) -> tuple:
        try:
            response = requests.get(
                self.url,
                headers=self._get_headers(),
                verify=True,
                timeout=10
            )
            if response.status_code in (200, 400, 404):
                return True, f"Conexión exitosa con SIESA Connekta — compañía {self.id_compania}"
            return False, f"No se pudo conectar — status {response.status_code}"
        except Exception as e:
            self.logger.error(f"Error al probar conexión Connekta: {e}")
            return False, str(e)