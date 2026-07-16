"""
SiesaEnterprise — Conector SIESA WS
Responsabilidades:
  - Conecta con SIESA WS via SOAP usando zeep
  - Limpia caracteres de control del XML
  - Maneja paginación
  - Implementa get() y test_connection()
Hereda: ERPConnector
Fase: 2 — Connection Layer
"""
from zeep import Client
from zeep.transports import Transport
import requests
from config.logger import IntegradorLogger
from connection.base import ERPConnector

class SiesaEnterprise(ERPConnector):
    
    def __init__(self, config: dict):
        self.url         = config["erp"]["url"]
        self.conexion    = config["erp"]["conexion"]
        self.compania    = config["erp"]["compania"]
        self.usuario     = config["erp"]["usuario"]
        self.clave       = config["erp"]["clave"]
        self.proveedor   = config["erp"]["proveedor"]
        self.proxy_host  = config["erp"]["proxy_host"]
        self.proxy_port  = config["erp"]["proxy_port"]
        self.logger      = IntegradorLogger(client_id=config["client_id"])

    def _build_xml(self, sql: str) -> str:
        return f"""
        <Consulta>
            <NombreConexion>{self.conexion}</NombreConexion>
            <IdCia>{self.compania}</IdCia>
            <IdProveedor>{self.proveedor}</IdProveedor>
            <IdConsulta>SIESA</IdConsulta>
            <Usuario>{self.usuario}</Usuario>
            <Clave>{self.clave}</Clave>
            <Parametros>
                <Sql>
                    {sql}
                </Sql>
            </Parametros>
        </Consulta>
        """
    
    def _get_client(self) -> Client:
        session = requests.Session()
        if self.proxy_host and self.proxy_port:
            session.proxies.update({
                "http": f"http://{self.proxy_host}:{self.proxy_port}"
            })
        transport = Transport(session=session, timeout=600)
        return Client(self.url, transport=transport)
    
    def _clean_string(self, valor) -> str:
        if not isinstance(valor, str):
            return valor
        return "".join(c for c in valor if c.isprintable())
    
    def get(self, endpoint: str, params: dict = {}) -> tuple:
        sql = params.get("sql", "")
        if not sql:
            self.logger.error("No se proporcionó SQL en params")
            return False, "Falta el SQL en params"
        
        try:
            xml    = self._build_xml(sql)
            client = self._get_client()
            result = client.service.EjecutarConsultaXML(xml)
            datos  = result['_value_1']['_value_1']

            if not datos:
                self.logger.info("Consulta exitosa - sin registros")
                return True, []
            
            resultado = []
            for dato in datos:
                fila = dato['Resultado']
                fila_limpia = {}
                for k, v in fila.items():
                    fila_limpia[k] = self._clean_string(v)
                resultado.append(fila_limpia)
            
            self.logger.info(f"Consulta exitosa — {len(resultado)} registros traídos")
            return True, resultado
        
        except Exception as e:
            self.logger.error(f"Error SOAP SIESA WS: {e}")
            return False, str(e)
    
    def test_connection(self) -> tuple:
        sql = "SELECT TOP 1 f430_id FROM t430"
        status, data = self.get(
            endpoint="EjecutarConsultaXML",
            params={"sql": sql}
        )
        if status:
            return True, f"Conexión exitosa con SIESA WS — {self.conexion}"
        return False, f"No se pudo conectar con SIESA WS — {self.conexion}: {data}"
            