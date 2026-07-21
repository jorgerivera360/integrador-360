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

    def test_connekta_constructor_extrae_conni_key_y_token(self):
        with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
            from connection.siesa_connekta import SiesaConnekta
            ck = SiesaConnekta(CONNEKTA_CONFIG)
            assert ck.conni_key   == "test_key"
            assert ck.conni_token == "test_token"

    def test_connekta_get_headers_retorna_los_cuatro_headers(self):
        with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
            from connection.siesa_connekta import SiesaConnekta
            ck      = SiesaConnekta(CONNEKTA_CONFIG)
            headers = ck._get_headers()
            assert "ConniKey"     in headers
            assert "ConniToken"   in headers
            assert "Content-Type" in headers
            assert "Accept"       in headers

    def test_connekta_get_sin_query_desc_retorna_false(self):
        with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
            from connection.siesa_connekta import SiesaConnekta
            ck = SiesaConnekta(CONNEKTA_CONFIG)
            status, msg = ck.get("", params={})
            assert status is False

    def test_connekta_get_construye_url_con_id_compania(self):
        with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
            from connection.siesa_connekta import SiesaConnekta
            ck = SiesaConnekta(CONNEKTA_CONFIG)
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "codigo": 0,
                "detalle": {"Datos": [], "total_páginas": 1}
            }
            with patch("requests.get", return_value=mock_response) as mock_get:
                ck.get("items_wms", params={"no_paginar": True})
                url_llamada = mock_get.call_args[0][0]
                assert "idCompania=7936" in url_llamada

    def test_connekta_get_agrega_paginacion_cuando_no_paginar_es_false(self):
        with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
            from connection.siesa_connekta import SiesaConnekta
            ck = SiesaConnekta(CONNEKTA_CONFIG)
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "codigo": 0,
                "detalle": {"Datos": [], "total_páginas": 1}
            }
            with patch("requests.get", return_value=mock_response) as mock_get:
                ck.get("items_wms", params={"no_paginar": False})
                url_llamada = mock_get.call_args[0][0]
                assert "paginacion" in url_llamada

    def test_connekta_get_no_agrega_paginacion_cuando_no_paginar_es_true(self):
        with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
            from connection.siesa_connekta import SiesaConnekta
            ck = SiesaConnekta(CONNEKTA_CONFIG)
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "codigo": 0,
                "detalle": {"Datos": [], "total_páginas": 1}
            }
            with patch("requests.get", return_value=mock_response) as mock_get:
                ck.get("items_wms", params={"no_paginar": True})
                url_llamada = mock_get.call_args[0][0]
                assert "paginacion" not in url_llamada

    def test_connekta_get_detecta_formato_datos(self):
        with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
            from connection.siesa_connekta import SiesaConnekta
            ck = SiesaConnekta(CONNEKTA_CONFIG)
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "codigo": 0,
                "detalle": {"Datos": [{"id": 1}, {"id": 2}], "total_páginas": 1}
            }
            with patch("requests.get", return_value=mock_response):
                status, data = ck.get("items_wms", params={"no_paginar": True})
                assert status is True
                assert len(data) == 2

    def test_connekta_get_detecta_formato_table_cuando_datos_no_existe(self):
        with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
            from connection.siesa_connekta import SiesaConnekta
            ck = SiesaConnekta(CONNEKTA_CONFIG)
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "codigo": 0,
                "detalle": {"Table": [{"id": 1}], "total_páginas": 1}
            }
            with patch("requests.get", return_value=mock_response):
                status, data = ck.get("items_wms", params={"no_paginar": True})
                assert status is True
                assert len(data) == 1

    def test_connekta_get_retorna_lista_vacia_cuando_items_esta_vacio(self):
        with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
            from connection.siesa_connekta import SiesaConnekta
            ck = SiesaConnekta(CONNEKTA_CONFIG)
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "codigo": 0,
                "detalle": {"Datos": [], "total_páginas": 1}
            }
            with patch("requests.get", return_value=mock_response):
                status, data = ck.get("items_wms", params={"no_paginar": True})
                assert status is True
                assert data == []

    def test_connekta_get_para_con_single_page_true(self):
        with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
            from connection.siesa_connekta import SiesaConnekta
            ck = SiesaConnekta(CONNEKTA_CONFIG)
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "codigo": 0,
                "detalle": {"Datos": [{"id": 1}], "total_páginas": 5}
            }
            with patch("requests.get", return_value=mock_response) as mock_get:
                ck.get("items_wms", params={"single_page": True})
                assert mock_get.call_count == 1

    def test_connekta_get_retorna_false_cuando_codigo_no_es_cero(self):
        with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
            from connection.siesa_connekta import SiesaConnekta
            ck = SiesaConnekta(CONNEKTA_CONFIG)
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "codigo": 1,
                "mensaje": "Token inválido"
            }
            with patch("requests.get", return_value=mock_response):
                status, msg = ck.get("items_wms", params={"no_paginar": True})
                assert status is False
                assert "Token inválido" in msg

    def test_connekta_get_retorna_false_cuando_hay_excepcion(self):
        with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
            from connection.siesa_connekta import SiesaConnekta
            ck = SiesaConnekta(CONNEKTA_CONFIG)
            with patch("requests.get", side_effect=Exception("network error")):
                status, msg = ck.get("items_wms")
                assert status is False
                assert "network error" in msg

    def test_connekta_test_connection_retorna_true_con_status_200_400_404(self):
        with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
            from connection.siesa_connekta import SiesaConnekta
            ck = SiesaConnekta(CONNEKTA_CONFIG)
            for status_code in [200, 400, 404]:
                mock_response = MagicMock()
                mock_response.status_code = status_code
                with patch("requests.get", return_value=mock_response):
                    status, msg = ck.test_connection()
                    assert status is True

# -- ExcelConnector — excel_connector.py

class TestExcelConnector:

    def test_excel_constructor_asigna_client_id(self):
        with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
            from connection.excel_connector import ExcelConnector
            ec = ExcelConnector(EXCEL_CONFIG)
            assert ec.client_id == "test_client"

    def test_excel_constructor_construye_ruta_base_correcta(self):
        with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
            from connection.excel_connector import ExcelConnector
            ec = ExcelConnector(EXCEL_CONFIG)
            assert ec.ruta_base == "/etc/integrador/excel/test_client/"

    def test_excel_get_ruta_archivo_retorna_ruta_correcta(self):
        with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
            from connection.excel_connector import ExcelConnector
            ec   = ExcelConnector(EXCEL_CONFIG)
            ruta = ec._get_ruta_archivo("productos")
            assert "test_client-productos.xlsx" in ruta
            assert "/etc/integrador/excel/test_client/" in ruta

    def test_excel_get_endpoint_invalido_retorna_false(self):
        with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
            from connection.excel_connector import ExcelConnector
            ec = ExcelConnector(EXCEL_CONFIG)
            status, msg = ec.get("clientes")
            assert status is False
            assert "no válido" in msg

    def test_excel_get_archivo_no_existe_retorna_lista_vacia(self):
        with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
            from connection.excel_connector import ExcelConnector
            ec = ExcelConnector(EXCEL_CONFIG)
            with patch("os.path.exists", return_value=False):
                status, data = ec.get("productos")
                assert status is True
                assert data == []

    def test_excel_get_lee_archivo_y_retorna_lista_de_dicts(self, tmp_path):
        import pandas as pd
        with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
            from connection.excel_connector import ExcelConnector
            config = {"client_id": "test", "erp": {"tipo": "excel"}, "odoo": {}}
            ec = ExcelConnector(config)
            archivo = tmp_path / "test-productos.xlsx"
            df = pd.DataFrame([{"referencia": "1000039", "descripcion": "PRODUCTO A"}])
            df.to_excel(archivo, index=False)
            ec.ruta_base = str(tmp_path) + "/"
            status, data = ec.get("productos")
            assert status is True
            assert len(data) == 1
            assert data[0]["referencia"] == "1000039"

    def test_excel_get_convierte_nan_a_none(self, tmp_path):
        import pandas as pd
        with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
            from connection.excel_connector import ExcelConnector
            config = {"client_id": "test", "erp": {"tipo": "excel"}, "odoo": {}}
            ec = ExcelConnector(config)
            archivo = tmp_path / "test-productos.xlsx"
            df = pd.DataFrame([{"referencia": "1000039", "barras": None}])
            df.to_excel(archivo, index=False)
            ec.ruta_base = str(tmp_path) + "/"
            status, data = ec.get("productos")
            assert status is True
            assert data[0]["barras"] is None

    def test_excel_test_connection_retorna_false_sin_archivos(self):
        with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
            from connection.excel_connector import ExcelConnector
            ec = ExcelConnector(EXCEL_CONFIG)
            with patch("os.path.exists", return_value=False):
                status, msg = ec.test_connection()
                assert status is False

    def test_excel_constructor_asigna_client_id(self):
        with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
            from connection.excel_connector import ExcelConnector
            ec = ExcelConnector(EXCEL_CONFIG)
            assert ec.client_id == "test_client"

    def test_excel_constructor_construye_ruta_base_correcta(self):
        """self.ruta_base sigue el estándar /etc/integrador/excel/{client_id}/."""
        with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
            from connection.excel_connector import ExcelConnector
            ec = ExcelConnector(EXCEL_CONFIG)
            assert ec.ruta_base == "/etc/integrador/excel/test_client/"

    def test_excel_get_ruta_archivo_retorna_ruta_correcta(self):
        """_get_ruta_archivo() retorna ruta completa con nombre {client_id}-{proceso}.xlsx."""
        with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
            from connection.excel_connector import ExcelConnector
            ec   = ExcelConnector(EXCEL_CONFIG)
            ruta = ec._get_ruta_archivo("productos")
            assert "test_client-productos.xlsx" in ruta
            assert "/etc/integrador/excel/test_client/" in ruta

    def test_excel_get_endpoint_invalido_retorna_false(self):
        """get() retorna (False, error) cuando endpoint no está en ARCHIVOS_VALIDOS."""
        with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
            from connection.excel_connector import ExcelConnector
            ec = ExcelConnector(EXCEL_CONFIG)
            status, msg = ec.get("clientes")
            assert status is False
            assert "no válido" in msg

    def test_excel_get_archivo_no_existe_retorna_lista_vacia(self):
        """get() retorna (True, []) con WARNING cuando el archivo no existe."""
        with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
            from connection.excel_connector import ExcelConnector
            ec = ExcelConnector(EXCEL_CONFIG)
            with patch("os.path.exists", return_value=False):
                status, data = ec.get("productos")
                assert status is True
                assert data == []

    def test_excel_get_lee_archivo_y_retorna_lista_de_dicts(self, tmp_path):
        """get() lee el archivo xlsx y retorna lista de dicts."""
        import pandas as pd
        with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
            from connection.excel_connector import ExcelConnector
            config = {"client_id": "test", "erp": {"tipo": "excel"}, "odoo": {}}
            ec = ExcelConnector(config)
            archivo = tmp_path / "test-productos.xlsx"
            df = pd.DataFrame([{"referencia": "1000039", "descripcion": "PRODUCTO A"}])
            df.to_excel(archivo, index=False)
            ec.ruta_base = str(tmp_path) + "/"
            status, data = ec.get("productos")
            assert status is True
            assert len(data) == 1
            assert data[0]["referencia"] == "1000039"

    def test_excel_get_convierte_nan_a_none(self, tmp_path):
        """get() convierte celdas vacías del Excel a None."""
        import pandas as pd
        with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
            from connection.excel_connector import ExcelConnector
            config = {"client_id": "test", "erp": {"tipo": "excel"}, "odoo": {}}
            ec = ExcelConnector(config)
            archivo = tmp_path / "test-productos.xlsx"
            df = pd.DataFrame([{"referencia": "1000039", "barras": None}])
            df.to_excel(archivo, index=False)
            ec.ruta_base = str(tmp_path) + "/"
            status, data = ec.get("productos")
            assert status is True
            assert data[0]["barras"] is None

    def test_excel_test_connection_retorna_false_sin_archivos(self):
        """test_connection() retorna (False, error) cuando no existe ningún archivo."""
        with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
            from connection.excel_connector import ExcelConnector
            ec = ExcelConnector(EXCEL_CONFIG)
            with patch("os.path.exists", return_value=False):
                status, msg = ec.test_connection()
                assert status is False


# -- JsonRPC — jsonrpc.py

class TestJsonRPC:

    def test_jsonrpc_constructor_extrae_url_sin_barra_final(self):
        with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
            from connection.jsonrpc import JsonRPC
            config = {**JSONRPC_CONFIG, "odoo": {**JSONRPC_CONFIG["odoo"], "url": "https://test.odoo.com/"}}
            rpc = JsonRPC(config)
            assert not rpc.url.endswith("/")
            assert rpc.url == "https://test.odoo.com"

    def test_jsonrpc_constructor_extrae_db_usuario_clave(self):
        with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
            from connection.jsonrpc import JsonRPC
            rpc = JsonRPC(JSONRPC_CONFIG)
            assert rpc.db       == "test_db"
            assert rpc.username == "test"
            assert rpc.password == "test"

    def test_jsonrpc_constructor_inicializa_authenticated_en_false(self):
        with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
            from connection.jsonrpc import JsonRPC
            rpc = JsonRPC(JSONRPC_CONFIG)
            assert rpc._authenticated is False

    def test_jsonrpc_authenticate_exitoso_pone_authenticated_en_true(self):
        with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
            from connection.jsonrpc import JsonRPC
            rpc = JsonRPC(JSONRPC_CONFIG)
            mock_response = MagicMock()
            mock_response.json.return_value = {"result": {"session_id": "xyz789"}}
            with patch.object(rpc._session, "post", return_value=mock_response):
                rpc.authenticate()
                assert rpc._authenticated is True

    def test_jsonrpc_authenticate_exitoso_guarda_session_id(self):
        with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
            from connection.jsonrpc import JsonRPC
            rpc = JsonRPC(JSONRPC_CONFIG)
            mock_response = MagicMock()
            mock_response.json.return_value = {"result": {"session_id": "xyz789"}}
            with patch.object(rpc._session, "post", return_value=mock_response):
                rpc.authenticate()
                assert rpc._session_id == "xyz789"

    def test_jsonrpc_authenticate_fallido_retorna_false(self):
        with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
            from connection.jsonrpc import JsonRPC
            rpc = JsonRPC(JSONRPC_CONFIG)
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "error": {"data": {"message": "Credenciales incorrectas", "arguments": []}}
            }
            with patch.object(rpc._session, "post", return_value=mock_response):
                status, msg = rpc.authenticate()
                assert status is False

    def test_jsonrpc_authenticate_loggea_info_cuando_exitoso(self):
        with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
            from connection.jsonrpc import JsonRPC
            rpc = JsonRPC(JSONRPC_CONFIG)
            mock_response = MagicMock()
            mock_response.json.return_value = {"result": {"session_id": "xyz789"}}
            with patch.object(rpc._session, "post", return_value=mock_response):
                with patch.object(rpc.logger, "info") as mock_info:
                    rpc.authenticate()
                    mock_info.assert_called()

    def test_jsonrpc_authenticate_loggea_error_cuando_falla(self):
        with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
            from connection.jsonrpc import JsonRPC
            rpc = JsonRPC(JSONRPC_CONFIG)
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "error": {"data": {"message": "Error", "arguments": []}}
            }
            with patch.object(rpc._session, "post", return_value=mock_response):
                with patch.object(rpc.logger, "error") as mock_error:
                    rpc.authenticate()
                    mock_error.assert_called()

    def test_jsonrpc_call_kw_sin_autenticar_retorna_false(self):
        with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
            from connection.jsonrpc import JsonRPC
            rpc = JsonRPC(JSONRPC_CONFIG)
            status, msg = rpc._call_kw("product.template", "search_read", [], {})
            assert status is False
            assert "No autenticado" in msg

    def test_jsonrpc_call_kw_construye_payload_correcto(self):
        with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
            from connection.jsonrpc import JsonRPC
            rpc = JsonRPC(JSONRPC_CONFIG)
            rpc._authenticated = True
            mock_response = MagicMock()
            mock_response.json.return_value = {"result": []}
            with patch.object(rpc._session, "post", return_value=mock_response) as mock_post:
                rpc._call_kw("product.template", "search_read", [], {"domain": []})
                payload = mock_post.call_args[1]["json"]
                assert payload["params"]["model"]  == "product.template"
                assert payload["params"]["method"] == "search_read"

    def test_jsonrpc_call_kw_retorna_false_cuando_odoo_retorna_error(self):
        with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
            from connection.jsonrpc import JsonRPC
            rpc = JsonRPC(JSONRPC_CONFIG)
            rpc._authenticated = True
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "error": {"data": {"message": "Access Denied", "arguments": []}}
            }
            with patch.object(rpc._session, "post", return_value=mock_response):
                status, msg = rpc._call_kw("product.template", "search_read", [], {})
                assert status is False
                assert "Access Denied" in msg

    def test_jsonrpc_call_kw_retorna_true_con_result(self):
        with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
            from connection.jsonrpc import JsonRPC
            rpc = JsonRPC(JSONRPC_CONFIG)
            rpc._authenticated = True
            mock_response = MagicMock()
            mock_response.json.return_value = {"result": [{"id": 1}]}
            with patch.object(rpc._session, "post", return_value=mock_response):
                status, data = rpc._call_kw("product.template", "search_read", [], {})
                assert status is True
                assert data == [{"id": 1}]

    def test_jsonrpc_extract_odoo_error_extrae_message(self):
        with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
            from connection.jsonrpc import JsonRPC
            body = {"error": {"data": {"message": "Access Denied", "arguments": []}}}
            msg  = JsonRPC._extract_odoo_error(body)
            assert msg == "Access Denied"

    def test_jsonrpc_extract_odoo_error_extrae_arguments_sin_message(self):
        with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
            from connection.jsonrpc import JsonRPC
            body = {"error": {"data": {"message": "", "arguments": ["error arg"]}}}
            msg  = JsonRPC._extract_odoo_error(body)
            assert "error arg" in msg

    def test_jsonrpc_search_read_llama_call_kw_con_method_correcto(self):
        with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
            from connection.jsonrpc import JsonRPC
            rpc = JsonRPC(JSONRPC_CONFIG)
            rpc._authenticated = True
            with patch.object(rpc, "_call_kw", return_value=(True, [])) as mock_call:
                rpc.search_read("product.template", domain=[["active", "=", True]])
                _, kwargs = mock_call.call_args
                assert kwargs["method"] == "search_read"

    def test_jsonrpc_read_pasa_ids_en_args(self):
        with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
            from connection.jsonrpc import JsonRPC
            rpc = JsonRPC(JSONRPC_CONFIG)
            rpc._authenticated = True
            with patch.object(rpc, "_call_kw", return_value=(True, [])) as mock_call:
                rpc.read("product.template", ids=[1, 2, 3])
                _, kwargs = mock_call.call_args
                assert [1, 2, 3] in kwargs["args"]

    def test_jsonrpc_write_pasa_ids_y_fields_en_args(self):
        with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
            from connection.jsonrpc import JsonRPC
            rpc = JsonRPC(JSONRPC_CONFIG)
            rpc._authenticated = True
            with patch.object(rpc, "_call_kw", return_value=(True, True)) as mock_call:
                rpc.write("product.template", ids=[1847], fields={"name": "nuevo"})
                _, kwargs = mock_call.call_args
                assert [1847] in kwargs["args"]
                assert {"name": "nuevo"} in kwargs["args"]