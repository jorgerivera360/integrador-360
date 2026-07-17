"""
test_connection.py — Pruebas de connection/
Casos de prueba:
  - Conexión exitosa por tipo de ERP
  - Error de autenticación manejado correctamente
  - Paginación trae todos los registros
  - _clean_string() elimina caracteres de control
Fase: 2 — Connection Layer
"""
import os
import json
import pytest
from unittest.mock import patch, MagicMock

# -- Configs ficticios 

SAP_CONFIG = {
    "client_id": "test_client",
    "erp": {
        "tipo":     "sap",
        "url":      "https://test-sap:50000",
        "compania": "TEST",
        "usuario":  "test",
        "clave":    "test"
    },
    "odoo": {"url": "https://test.odoo.com", "database": "test_db", "usuario": "test", "clave": "test"}
}
 
WS_CONFIG = {
    "client_id": "test_client",
    "erp": {
        "tipo":       "ws",
        "url":        "https://test-ws.asmx?wsdl",
        "compania":   "1",
        "usuario":    "test",
        "clave":      "test",
        "conexion":   "Test Conexion",
        "proveedor":  "BEXCONNECT",
        "proxy_host": None,
        "proxy_port": None
    },
    "odoo": {"url": "https://test.odoo.com", "database": "test_db", "usuario": "test", "clave": "test"}
}
 
WS_CONFIG_PROXY = {
    "client_id": "test_client",
    "erp": {
        "tipo":       "ws",
        "url":        "https://test-ws.asmx?wsdl",
        "compania":   "1",
        "usuario":    "test",
        "clave":      "test",
        "conexion":   "Test Conexion",
        "proveedor":  "BEXCONNECT",
        "proxy_host": "192.168.1.1",
        "proxy_port": "8080"
    },
    "odoo": {"url": "https://test.odoo.com", "database": "test_db", "usuario": "test", "clave": "test"}
}
 
CONNEKTA_CONFIG = {
    "client_id": "test_client",
    "erp": {
        "tipo":       "connekta",
        "url":        "https://servicios.siesacloud.com/api/connekta/v3/ejecutarconsulta",
        "url_qa":     "https://serviciosqa.siesacloud.com/api/connekta/v3/ejecutarconsulta",
        "idcompania": "7936",
        "connikey":   "test_key",
        "connitoken": "test_token"
    },
    "odoo": {"url": "https://test.odoo.com", "database": "test_db", "usuario": "test", "clave": "test"}
}
 
EXCEL_CONFIG = {
    "client_id": "test_client",
    "erp": {"tipo": "excel"},
    "odoo": {"url": "https://test.odoo.com", "database": "test_db", "usuario": "test", "clave": "test"}
}
 
JSONRPC_CONFIG = {
    "client_id": "test_client",
    "odoo": {
        "url":      "https://test.odoo.com",
        "database": "test_db",
        "usuario":  "test",
        "clave":    "test"
    }
}

# -- ERPConnector - base.py

class TestERPConnector:
    def test_erpconnector_no_se_puede_instanciar_directamente(self):
      from connection.base import ERPConnector
      with pytest.raises(TypeError):
          ERPConnector()

    def test_subclase_sin_get_no_se_puede_instanciar(self):
        with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
            from connection.base import ERPConnector

            class SinGet(ERPConnector):
                def test_connection(self):
                    return True, "ok"

            with pytest.raises(TypeError):
                SinGet()

    def test_subclase_sin_test_connection_no_se_puede_instanciar(self):
        with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
            from connection.base import ERPConnector

            class SinTestConnection(ERPConnector):
                def get(self, endpoint, params={}):
                    return True, []

            with pytest.raises(TypeError):
                SinTestConnection()

    def test_subclase_que_implementa_ambos_si_se_puede_instanciar(self):
        with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
            from connection.base import ERPConnector

            class Completa(ERPConnector):
                def get(self, endpoint, params={}):
                    return True, []
                def test_connection(self):
                    return True, "ok"

            conector = Completa()
            assert conector is not None

# -- SAP - sap.py

class TestSAP:
    
    def test_sap_constructor_extrae_url(self):
        with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
            from connection.sap import SAP
            sap = SAP(SAP_CONFIG)
            assert sap.url == "https://test-sap:50000"

    def test_sap_constructor_extrae_compania_usuario_clave(self):
        with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
            from connection.sap import SAP
            sap = SAP(SAP_CONFIG)
            assert sap.compania == "TEST"
            assert sap.usuario  == "test"
            assert sap.clave    == "test"

    def test_sap_constructor_inicializa_session_id_en_none(self):
        with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
            from connection.sap import SAP
            sap = SAP(SAP_CONFIG)
            assert sap.session_id is None

    def test_sap_login_api_exitoso_guarda_session_id(self):
        with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
            from connection.sap import SAP
            sap = SAP(SAP_CONFIG)
            mock_response = MagicMock()
            mock_response.json.return_value = {"SessionId": "abc123"}
            with patch("requests.post", return_value=mock_response):
                sap.login_api()
                assert sap.session_id == "abc123"
          
    def test_sap_login_api_exitoso_retorna_true(self):
        with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
            from connection.sap import SAP
            sap = SAP(SAP_CONFIG)
            mock_response = MagicMock()
            mock_response.json.return_value = {"SessionId": "abc123"}
            with patch("requests.post", return_value=mock_response):
                result = sap.login_api()
                assert result is True

    def test_sap_login_api_fallido_retorna_false(self):
        with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
            from connection.sap import SAP
            sap = SAP(SAP_CONFIG)
            with patch("requests.post", side_effect=Exception("timeout")):
                result = sap.login_api()
                assert result is False

    def test_sap_login_api_fallido_loggea_error(self):
        with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
            from connection.sap import SAP
            sap = SAP(SAP_CONFIG)
            with patch("requests.post", side_effect=Exception("timeout")):
                with patch.object(sap.logger, "error") as mock_error:
                    sap.login_api()
                    mock_error.assert_called_once()

    def test_sap_get_headers_retorna_session_id_y_cookie(self):
        with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
            from connection.sap import SAP
            sap = SAP(SAP_CONFIG)
            sap.session_id = "abc123"
            headers = sap._get_headers()
            assert headers["SessionId"] == "abc123"
            assert "B1SESSION=abc123" in headers["Cookie"]

    def test_sap_get_sin_session_id_retorna_false(self):
        with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
            from connection.sap import SAP
            sap = SAP(SAP_CONFIG)
            status, msg = sap.get("Items")
            assert status is False
            assert "No autenticado" in msg

    def test_sap_get_construye_url_con_skip_cero(self):
        with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
            from connection.sap import SAP
            sap = SAP(SAP_CONFIG)
            sap.session_id = "abc123"
            mock_response = MagicMock()
            mock_response.json.return_value = {"value": [{"id": 1}]}
            with patch("requests.get", return_value=mock_response) as mock_get:
                sap.get("Items")
                url_llamada = mock_get.call_args[0][0]
                assert "$skip=0" in url_llamada

    def test_sap_get_agrega_filter_cuando_params_tiene_filter(self):
        with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
            from connection.sap import SAP
            sap = SAP(SAP_CONFIG)
            sap.session_id = "abc123"
            mock_response = MagicMock()
            mock_response.json.return_value = {"value": [{"id": 1}]}
            with patch("requests.get", return_value=mock_response) as mock_get:
                sap.get("Items", params={"filter": "Valid eq 'tYES'"})
                url_llamada = mock_get.call_args[0][0]
                assert "$filter=Valid eq 'tYES'" in url_llamada

    def test_sap_get_agrega_select_cuando_params_tiene_select(self):
        with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
            from connection.sap import SAP
            sap = SAP(SAP_CONFIG)
            sap.session_id = "abc123"
            mock_response = MagicMock()
            mock_response.json.return_value = {"value": [{"id": 1}]}
            with patch("requests.get", return_value=mock_response) as mock_get:
                sap.get("Items", params={"select": "ItemCode,ItemName"})
                url_llamada = mock_get.call_args[0][0]
                assert "$select=ItemCode,ItemName" in url_llamada

    def test_sap_get_acumula_registros_de_multiples_paginas(self):
        with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
            from connection.sap import SAP
            sap = SAP(SAP_CONFIG)
            sap.session_id = "abc123"
            pagina1 = MagicMock()
            pagina1.json.return_value = {"value": [{"id": 1}, {"id": 2}], "odata.nextLink": "Items?$skip=20"}
            pagina2 = MagicMock()
            pagina2.json.return_value = {"value": [{"id": 3}]}
            with patch("requests.get", side_effect=[pagina1, pagina2]):
                status, data = sap.get("Items")
                assert status is True
                assert len(data) == 3

    def test_sap_get_para_cuando_no_hay_nextlink(self):
        with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
            from connection.sap import SAP
            sap = SAP(SAP_CONFIG)
            sap.session_id = "abc123"
            mock_response = MagicMock()
            mock_response.json.return_value = {"value": [{"id": 1}]}
            with patch("requests.get", return_value=mock_response) as mock_get:
                sap.get("Items")
                assert mock_get.call_count == 1

    def test_sap_get_para_cuando_items_esta_vacio(self):
        with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
            from connection.sap import SAP
            sap = SAP(SAP_CONFIG)
            sap.session_id = "abc123"
            mock_response = MagicMock()
            mock_response.json.return_value = {"value": []}
            with patch("requests.get", return_value=mock_response):
                status, data = sap.get("Items")
                assert status is True
                assert data == []

    def test_sap_get_retorna_false_cuando_hay_excepcion(self):
        with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
            from connection.sap import SAP
            sap = SAP(SAP_CONFIG)
            sap.session_id = "abc123"
            with patch("requests.get", side_effect=Exception("connection error")):
                status, msg = sap.get("Items")
                assert status is False
                assert "connection error" in msg

# -- Siesa Enterprise - siesa_enterprise.py

class TestSiesaEnterprise:
    
    def test_ws_constructor_extrae_todos_los_campos(self):
        with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
            from connection.siesa_enterprise import SiesaEnterprise
            ws = SiesaEnterprise(WS_CONFIG)
            assert ws.url        == "https://test-ws.asmx?wsdl"
            assert ws.conexion   == "Test Conexion"
            assert ws.compania   == "1"
            assert ws.usuario    == "test"
            assert ws.clave      == "test"
            assert ws.proveedor  == "BEXCONNECT"
            assert ws.proxy_host is None
            assert ws.proxy_port is None

    def test_ws_build_xml_retorna_string_con_sql(self):
        with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
            from connection.siesa_enterprise import SiesaEnterprise
            ws  = SiesaEnterprise(WS_CONFIG)
            xml = ws._build_xml("SELECT TOP 1 f430_id FROM t430")
            assert "SELECT TOP 1 f430_id FROM t430" in xml

    def test_ws_build_xml_incluye_conexion_y_compania(self):
        with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
            from connection.siesa_enterprise import SiesaEnterprise
            ws  = SiesaEnterprise(WS_CONFIG)
            xml = ws._build_xml("SELECT 1")
            assert "Test Conexion" in xml
            assert "BEXCONNECT"    in xml
    
    def test_ws_get_client_retorna_objeto_client(self):
        with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
            from connection.siesa_enterprise import SiesaEnterprise
            ws = SiesaEnterprise(WS_CONFIG)
            with patch("connection.siesa_enterprise.Client") as mock_client_class:
                mock_client_class.return_value = MagicMock()
                cliente = ws._get_client()
                mock_client_class.assert_called_once()
                assert cliente is not None
                
    def test_ws_get_client_configura_proxy_cuando_existe(self):
        with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
            from connection.siesa_enterprise import SiesaEnterprise
            ws = SiesaEnterprise(WS_CONFIG_PROXY)
            with patch("connection.siesa_enterprise.Client"):
                with patch("requests.Session") as mock_session_class:
                    mock_session = MagicMock()
                    mock_session_class.return_value = mock_session
                    ws._get_client()
                    mock_session.proxies.update.assert_called_once()

    def test_ws_get_client_no_configura_proxy_cuando_es_none(self):
        with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
            from connection.siesa_enterprise import SiesaEnterprise
            ws = SiesaEnterprise(WS_CONFIG)
            with patch("connection.siesa_enterprise.Client"):
                with patch("requests.Session") as mock_session_class:
                    mock_session = MagicMock()
                    mock_session_class.return_value = mock_session
                    ws._get_client()
                    mock_session.proxies.update.assert_not_called()

    def test_ws_clean_string_retorna_string_sin_cambios(self):
        with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
            from connection.siesa_enterprise import SiesaEnterprise
            ws     = SiesaEnterprise(WS_CONFIG)
            result = ws._clean_string("PRODUCTO A")
            assert result == "PRODUCTO A"

    def test_ws_clean_string_elimina_caracteres_no_imprimibles(self):
        with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
            from connection.siesa_enterprise import SiesaEnterprise
            ws     = SiesaEnterprise(WS_CONFIG)
            result = ws._clean_string("PRODUCTO\x00A\x01")
            assert result == "PRODUCTOA"

    def test_ws_clean_string_retorna_valor_sin_cambios_si_no_es_string(self):
        with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
            from connection.siesa_enterprise import SiesaEnterprise
            ws = SiesaEnterprise(WS_CONFIG)
            assert ws._clean_string(1234) == 1234
            assert ws._clean_string(None) is None
            assert ws._clean_string(12.5) == 12.5

    def test_ws_get_retorna_false_cuando_no_hay_sql(self):
        with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
            from connection.siesa_enterprise import SiesaEnterprise
            ws = SiesaEnterprise(WS_CONFIG)
            status, msg = ws.get("EjecutarConsultaXML", params={})
            assert status is False
            assert "Falta el SQL" in msg

    def test_ws_get_llama_ejecutarconsultaxml(self):
        with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
            from connection.siesa_enterprise import SiesaEnterprise
            ws = SiesaEnterprise(WS_CONFIG)
            mock_client = MagicMock()
            mock_client.service.EjecutarConsultaXML.return_value = {
                "_value_1": {"_value_1": None}
            }
            with patch.object(ws, "_get_client", return_value=mock_client):
                ws.get("EjecutarConsultaXML", params={"sql": "SELECT 1"})
                mock_client.service.EjecutarConsultaXML.assert_called_once()

    def test_ws_get_retorna_lista_vacia_cuando_datos_es_none(self):
        with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
            from connection.siesa_enterprise import SiesaEnterprise
            ws = SiesaEnterprise(WS_CONFIG)
            mock_client = MagicMock()
            mock_client.service.EjecutarConsultaXML.return_value = {
                "_value_1": {"_value_1": None}
            }
            with patch.object(ws, "_get_client", return_value=mock_client):
                status, data = ws.get("EjecutarConsultaXML", params={"sql": "SELECT 1"})
                assert status is True
                assert data == []

    def test_ws_get_retorna_lista_con_registros_limpios(self):
        with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
            from connection.siesa_enterprise import SiesaEnterprise
            ws = SiesaEnterprise(WS_CONFIG)
            mock_client = MagicMock()
            mock_client.service.EjecutarConsultaXML.return_value = {
                "_value_1": {"_value_1": [
                    {"Resultado": {"f430_id": "1000039", "f200_nombre": "PRODUCTO A"}}
                ]}
            }
            with patch.object(ws, "_get_client", return_value=mock_client):
                status, data = ws.get("EjecutarConsultaXML", params={"sql": "SELECT 1"})
                assert status is True
                assert len(data) == 1
                assert data[0]["f430_id"] == "1000039"

    def test_ws_get_aplica_clean_string_a_cada_campo(self):
        with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
            from connection.siesa_enterprise import SiesaEnterprise
            ws = SiesaEnterprise(WS_CONFIG)
            mock_client = MagicMock()
            mock_client.service.EjecutarConsultaXML.return_value = {
                "_value_1": {"_value_1": [
                    {"Resultado": {"f200_nombre": "PRODUCTO\x00A"}}
                ]}
            }
            with patch.object(ws, "_get_client", return_value=mock_client):
                status, data = ws.get("EjecutarConsultaXML", params={"sql": "SELECT 1"})
                assert status is True
                assert data[0]["f200_nombre"] == "PRODUCTOA"

    def test_ws_get_retorna_false_cuando_hay_excepcion_soap(self):
        with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
            from connection.siesa_enterprise import SiesaEnterprise
            ws = SiesaEnterprise(WS_CONFIG)
            with patch.object(ws, "_get_client", side_effect=Exception("SOAP error")):
                status, msg = ws.get("EjecutarConsultaXML", params={"sql": "SELECT 1"})
                assert status is False
                assert "SOAP error" in msg

    def test_ws_test_connection_ejecuta_select_top1(self):
        with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
            from connection.siesa_enterprise import SiesaEnterprise
            ws = SiesaEnterprise(WS_CONFIG)
            with patch.object(ws, "get", return_value=(True, [])) as mock_get:
                ws.test_connection()
                _, kwargs = mock_get.call_args
                assert "SELECT TOP 1 f430_id FROM t430" in kwargs["params"]["sql"]

    def test_ws_test_connection_retorna_true_cuando_get_es_exitoso(self):
        with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
            from connection.siesa_enterprise import SiesaEnterprise
            ws = SiesaEnterprise(WS_CONFIG)
            with patch.object(ws, "get", return_value=(True, [{"f430_id": "1"}])):
                status, msg = ws.test_connection()
                assert status is True
                assert "Conexión exitosa con SIESA WS" in msg

# -- SiesaConnekta — siesa_connekta.py

class TestSiesaConnekta:
    
    
    def test_connekta_constructor_extrae_url_y_url_qa(self):
        with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
            from connection.siesa_connekta import SiesaConnekta
            ck = SiesaConnekta(CONNEKTA_CONFIG)
            assert ck.url    == "https://servicios.siesacloud.com/api/connekta/v3/ejecutarconsulta"
            assert ck.url_qa == "https://serviciosqa.siesacloud.com/api/connekta/v3/ejecutarconsulta"

    def test_connekta_constructor_extrae_id_compania(self):
        with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
            from connection.siesa_connekta import SiesaConnekta
            ck = SiesaConnekta(CONNEKTA_CONFIG)
            assert ck.id_compania == "7936"