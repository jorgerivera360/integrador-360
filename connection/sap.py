"""
SAP — Conector SAP Business One
Responsabilidades:
  - Hereda ERPConnector
  - Constructor recibe config y extrae credenciales
  - login_api() obtiene SessionId — se guarda en self.session_id
  - get() construye la URL, hace el request con paginación
    y retorna (status, lista de dicts crudos)
  - test_connection() verifica que login_api() funciona
Patrones: Strategy · Singleton para session_id
Fase: 2 — Connection Layer
"""
import json
import requests
import urllib3
from config.logger import IntegradorLogger
from connection.base import ERPConnector

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class SAP(ERPConnector):
    
    def __init__(self, config:dict):
        self.url        = config["erp"]["url"]
        self.compania   = config["erp"]["compania"]
        self.usuario    = config["erp"]["usuario"]
        self.clave      = config["erp"]["clave"]
        self.session_id = None
        self.logger     = IntegradorLogger(client_id=config["client_id"])

    def login_api(self) -> bool:
        try:
            url     = f"{self.url}/b1s/v1/Login"
            payload = json.dumps({
                "CompanyDB": self.compania,
                "UserName":  self.usuario,
                "Password":  self.clave,
            })
            headers = {
                "Content-Type": "application/json",
                "Cookie":       "B1SESSION=; ROUTEID=.node3",
            }
            response = requests.post(url, headers=headers, data=payload, verify=False, timeout=30)
            response.raise_for_status()
            self.session_id = response.json().get("SessionId")
            self.logger.info(f"Login SAP exitoso para {self.compania}")
            return True
        except Exception as e:
            self.logger.error(f"Error en login SAP: {e}")
            return False
    
    def _get_headers(self) -> dict:
        return {
            "SessionId": self.session_id,
            "Cookie":    f"B1SESSION={self.session_id}; ROUTEID=.node7",
        }
    
    def get(self, endpoint: str, params: dict = {}) -> tuple:
        if not self.session_id:
            self.logger.error("No hay session_id")
            return False, "No autenticado en SAP"
        try:
            data_array = []
            count      = 0
            filter_str = params.get("filter", "")
            select_str = params.get("select", "")

            while True:
                url = f"{self.url}/b1s/v1/{endpoint}?$skip={count}"
                if filter_str:
                    url += f"&$filter={filter_str}"
                if select_str:
                  url += f"&$select={select_str}"

                response = requests.get(url, headers=self._get_headers(), verify=False)

                if response.status_code == 401 and count == 0:
                    self.logger.warning("Sesión SAP expirada, reintentando login")
                    if not self.login_api():
                        return False, "No se pudo re-autenticar en SAP"
                    response = requests.get(url, headers=self._get_headers(), verify=False)
                response.raise_for_status()
                data  = response.json()
                items = data.get("value", [])

                if not items:
                    break
                
                data_array.extend(items)
                self.logger.info(f"Página traída, {len(items)} registros - total: {len(data_array)}")

                if "odata.nextLink" not in data:
                    break
                
                count += 20

            return True, data_array
        
        except Exception as e:
            self.logger.error(f"Error al traer {endpoint} de SAP: {e}")
            return False, str(e)
        
    def test_connection(self) -> tuple:
        ok = self.login_api()
        if ok:
            return True, f"Conexión exitosa con SAP - empresa {self.compania}"
        return False, f"No se puedo conectar con SAP - empresa {self.compania}"