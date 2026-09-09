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
from zeep import Client, helpers
from zeep.transports import Transport
from zeep.plugins import HistoryPlugin
from lxml import etree
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
    
    def _get_client(self, plugins=None) -> Client:
      session = requests.Session()
      if self.proxy_host and self.proxy_port:
          session.proxies.update({
              "http": f"http://{self.proxy_host}:{self.proxy_port}"
          })
      transport = Transport(session=session, timeout=600)
      return Client(self.url, transport=transport, plugins=plugins or [])
    
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
            xml     = self._build_xml(sql)
            history = HistoryPlugin()
            client  = self._get_client(plugins=[history])
            result  = client.service.EjecutarConsultaXML(xml)

            try:
                result = helpers.serialize_object(result, target_cls=dict)
                datos  = result['_value_1']['_value_1']
            except TypeError:
                self.logger.info("serialize_object falló — usando fallback XML directo")
                datos = self._parse_raw_response(history)

            if not datos:
                self.logger.info("Consulta exitosa - sin registros")
                return True, []

            resultado = []
            for dato in datos:
                fila = dato.get('Resultado', dato) if isinstance(dato, dict) else dato
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
        sql = "SELECT 1"
        status, data = self.get(
            endpoint="EjecutarConsultaXML",
            params={"sql": sql}
        )
        if status:
            return True, f"Conexión exitosa con SIESA WS: {self.conexion}"
        return False, f"No se pudo conectar con SIESA WS: {self.conexion} ({data})"

    def _parse_raw_response(self, history) -> list | None:
      """Parsea respuesta SOAP cruda cuando serialize_object falla"""
      envelope = history.last_received['envelope']
      datos = []

      for resultado_elem in envelope.iter():
          if not isinstance(resultado_elem.tag, str):
              continue
          if etree.QName(resultado_elem.tag).localname != 'Resultado':
              continue

          fila = {}
          for child in resultado_elem:
              if not isinstance(child.tag, str):
                  continue
              child_tag = etree.QName(child.tag).localname
              fila[child_tag] = child.text.strip() if child.text else None

          if fila:
              datos.append({'Resultado': fila})

      return datos if datos else None
            