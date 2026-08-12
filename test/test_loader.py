"""
test_loader.py — Pruebas de config/loader.py
Casos de prueba:
  - Trae secret de GCP correctamente
  - Fallback con .env funciona
  - Fusión GCP + BD correcta
  - Error si el secret no existe
  - Dict retornado tiene todos los campos
Fase: 1 y 6
"""
import os
import json
import pytest
from unittest.mock import patch, MagicMock
from config.loader import ConfigLoader

# -- Constructor -- #

def test_constructor_client_id():
    loader = ConfigLoader(client_id="fenix")
    resultado = loader.client_id 
    assert resultado == "fenix"

def test_constructor_env_desde_variable():
    with patch.dict(os.environ, {'ENV': 'staging'}):
        loader = ConfigLoader(client_id='fenix')
        assert loader.env == 'staging'

def test_constructor_project_id_desde_variable():
    with patch.dict(os.environ, {'GCP_PROJECT_ID': 'mi-proyecto-123'}):
        loader = ConfigLoader(client_id='fenix')
        assert loader.project_id == 'mi-proyecto-123'

def test_constructor_credentials_path_default():
    with patch.dict(os.environ, {}, clear=True):
        loader = ConfigLoader(client_id='fenix')
        assert loader.credentials_path == '/etc/integrador/credentials'


# -- Load From GCP -- #

def test_load_from_gcp_trae_secret_correctamente(tmp_path):
    config_mock = {
        "erp":  {"tipo": "ws", "url": "http://test"},
        "odoo": {"url": "http://odoo-test"}
    }
    with patch('config.loader.secretmanager.SecretManagerServiceClient') as mock_client:
        mock_response = MagicMock()
        mock_response.payload.data = json.dumps(config_mock).encode('UTF-8')
        mock_client.return_value.access_secret_version.return_value = mock_response

        with patch.dict(os.environ, {
            'GCP_PROJECT_ID':    'proyecto-test',
            'CREDENTIALS_PATH':  str(tmp_path)
        }):
            loader    = ConfigLoader(client_id='cliente_prueba')
            resultado = loader._load_from_gcp()
            assert resultado == config_mock

def test_load_from_gcp_dict_tiene_clave_erp_y_odoo(tmp_path):
    config_mock = {
        "erp":  {"tipo": "ws"},
        "odoo": {"url": "http://odoo-test"}
    }
    with patch('config.loader.secretmanager.SecretManagerServiceClient') as mock_client:
        mock_response = MagicMock()
        mock_response.payload.data = json.dumps(config_mock).encode('UTF-8')
        mock_client.return_value.access_secret_version.return_value = mock_response

        with patch.dict(os.environ, {
            'GCP_PROJECT_ID':   'proyecto-test',
            'CREDENTIALS_PATH': str(tmp_path)
        }):
            loader    = ConfigLoader(client_id='cliente_prueba')
            resultado = loader._load_from_gcp()
            assert 'erp'  in resultado
            assert 'odoo' in resultado

def test_load_from_gcp_llama_save_credentials(tmp_path):
    config_mock = {
        "erp":  {"tipo": "ws"},
        "odoo": {"url": "http://odoo-test"}
    }
    with patch('config.loader.secretmanager.SecretManagerServiceClient') as mock_client:
        mock_response = MagicMock()
        mock_response.payload.data = json.dumps(config_mock).encode('UTF-8')
        mock_client.return_value.access_secret_version.return_value = mock_response

        with patch.dict(os.environ, {
            'ENV':              'dev',
            'GCP_PROJECT_ID':   'proyecto-test',
            'CREDENTIALS_PATH': str(tmp_path)
        }, clear=True):
            loader = ConfigLoader(client_id='cliente_prueba')
            loader._load_from_gcp()

            archivo = tmp_path / "integrador-cliente_prueba.json"
            assert archivo.exists()

def test_load_from_gcp_cuando_falla_llama_load_credentials(tmp_path):
    config = {
        "erp":  {"tipo": "ws"},
        "odoo": {"url": "http://odoo-test"}
    }
    archivo = tmp_path / "integrador-cliente_prueba.json"
    archivo.write_text(json.dumps(config))

    with patch('config.loader.secretmanager.SecretManagerServiceClient') as mock_client:
        mock_client.return_value.access_secret_version.side_effect = Exception("GCP caído")

        with patch.dict(os.environ, {
            'ENV':              'dev',
            'GCP_PROJECT_ID':   'proyecto-test',
            'CREDENTIALS_PATH': str(tmp_path)
        }, clear=True):
            loader    = ConfigLoader(client_id='cliente_prueba')
            resultado = loader._load_from_gcp()
            assert resultado == config

def test_load_from_gcp_error_se_registra_con_nivel_error(tmp_path):
    config = {
        "erp":  {"tipo": "ws"},
        "odoo": {"url": "http://odoo-test"}
    }
    archivo = tmp_path / "integrador-cliente_prueba.json"
    archivo.write_text(json.dumps(config))

    with patch('config.loader.secretmanager.SecretManagerServiceClient') as mock_client:
        mock_client.return_value.access_secret_version.side_effect = Exception("GCP caído")

        with patch.dict(os.environ, {
            'ENV':              'dev',
            'GCP_PROJECT_ID':   'proyecto-test',
            'CREDENTIALS_PATH': str(tmp_path)
        }, clear=True):
            loader = ConfigLoader(client_id='cliente_prueba')
            with patch.object(loader.logger, 'error') as mock_error:
                loader._load_from_gcp()
                mock_error.assert_called_once()
                assert 'GCP' in mock_error.call_args[0][0]

# -- save_credentials() -- #

def test_save_credentials_guarda_archivo_con_nombre_correcto(tmp_path):
    config = {"erp": {"tipo": "ws"}, "odoo": {"url": "http://test"}}

    with patch.dict(os.environ, {
        'ENV':              'dev',
        'CREDENTIALS_PATH': str(tmp_path)
    }, clear=True):
        loader = ConfigLoader(client_id='cliente_prueba')
        loader.save_credentials(config)

        archivo = tmp_path / "integrador-cliente_prueba.json"
        assert archivo.exists()

def test_save_credentials_archivo_es_json_valido(tmp_path):
    config = {"erp": {"tipo": "ws"}, "odoo": {"url": "http://test"}}

    with patch.dict(os.environ, {
        'ENV':              'dev',
        'CREDENTIALS_PATH': str(tmp_path)
    }, clear=True):
        loader = ConfigLoader(client_id='cliente_prueba')
        loader.save_credentials(config)

        archivo = tmp_path / "integrador-cliente_prueba.json"
        try:
            json.loads(archivo.read_text())
            es_json_valido = True
        except json.JSONDecodeError:
            es_json_valido = False

        assert es_json_valido

def test_save_credentials_contenido_es_identico_al_dict(tmp_path):
    config = {"erp": {"tipo": "ws"}, "odoo": {"url": "http://test"}}

    with patch.dict(os.environ, {
        'ENV':              'dev',
        'CREDENTIALS_PATH': str(tmp_path)
    }, clear=True):
        loader = ConfigLoader(client_id='cliente_prueba')
        loader.save_credentials(config)

        archivo   = tmp_path / "integrador-cliente_prueba.json"
        contenido = json.loads(archivo.read_text())
        assert contenido == config

# -- load_credentials() -- #

def test_load_credentials_carga_correctamente(tmp_path):
    config  = {"erp": {"tipo": "ws"}, "odoo": {"url": "http://test"}}
    archivo = tmp_path / "integrador-cliente_prueba.json"
    archivo.write_text(json.dumps(config))

    with patch.dict(os.environ, {
        'ENV':              'dev',
        'CREDENTIALS_PATH': str(tmp_path)
    }, clear=True):
        loader    = ConfigLoader(client_id='cliente_prueba')
        resultado = loader.load_credentials()
        assert resultado == config

def test_load_credentials_lanza_runtime_error_sin_archivo(tmp_path):
    with patch.dict(os.environ, {
        'ENV':              'dev',
        'CREDENTIALS_PATH': str(tmp_path)
    }, clear=True):
        loader = ConfigLoader(client_id='cliente_prueba')
        with pytest.raises(RuntimeError):
            loader.load_credentials()

def test_load_credentials_mensaje_error_incluye_client_id(tmp_path):
    with patch.dict(os.environ, {
        'ENV':              'dev',
        'CREDENTIALS_PATH': str(tmp_path)
    }, clear=True):
        loader = ConfigLoader(client_id='cliente_prueba')
        with pytest.raises(RuntimeError) as exc_info:
            loader.load_credentials()
        assert 'cliente_prueba' in str(exc_info.value)

# ============================================================
# Tests de BD — _get_db_connection(), constructor y load_db_config()
# Fase 6
# ============================================================

# -- _get_db_connection() -- #

def test_get_db_connection_sin_database_url_lanza_runtime_error():
    with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
        loader = ConfigLoader(client_id="fenix")
        loader.database_url = None
        with pytest.raises(RuntimeError, match="DATABASE_URL"):
            loader._get_db_connection()


@patch("config.loader.psycopg2")
def test_get_db_connection_error_conexion_lanza_operational_error(mock_psycopg2):
    mock_psycopg2.OperationalError = Exception
    mock_psycopg2.connect.side_effect = mock_psycopg2.OperationalError("Connection refused")

    with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
        loader = ConfigLoader(client_id="fenix")
        loader.database_url = "postgresql://test:test@localhost/test"
        with pytest.raises(Exception, match="Connection refused"):
            loader._get_db_connection()


@patch("config.loader.psycopg2")
def test_get_db_connection_exitosa_retorna_conexion(mock_psycopg2):
    mock_conn = MagicMock()
    mock_psycopg2.connect.return_value = mock_conn

    with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
        loader = ConfigLoader(client_id="fenix")
        loader.database_url = "postgresql://test:test@localhost/test"
        conn = loader._get_db_connection()
        assert conn == mock_conn
        mock_psycopg2.connect.assert_called_once_with("postgresql://test:test@localhost/test")


# -- Constructor — database_url -- #

def test_constructor_database_url_desde_env():
    with patch.dict(os.environ, {
        "ENV": "dev",
        "DATABASE_URL": "postgresql://user:pass@host/db"
    }):
        loader = ConfigLoader(client_id="fenix")
        assert loader.database_url == "postgresql://user:pass@host/db"


def test_constructor_database_url_none_si_no_existe():
    with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
        loader = ConfigLoader(client_id="fenix")
        assert loader.database_url is None


# -- load_db_config() -- #

@patch("config.loader.psycopg2")
def test_load_db_config_retorna_erp_type_y_flows(mock_psycopg2):
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_psycopg2.connect.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cur
    mock_psycopg2.Error = Exception

    mock_cur.fetchone.return_value = ("ws",)
    mock_cur.fetchall.return_value = [
        (1, "items", "items", {"sql": "SELECT 1"}, "0 */2 * * *")
    ]

    with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
        loader = ConfigLoader(client_id="fenix")
        loader.database_url = "postgresql://test:test@localhost/test"
        result = loader.load_db_config()

    assert result["erp_type"] == "ws"
    assert len(result["flows"]) == 1
    assert result["flows"][0]["flow_name"] == "items"


@patch("config.loader.psycopg2")
def test_load_db_config_cliente_no_encontrado(mock_psycopg2):
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_psycopg2.connect.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cur
    mock_psycopg2.Error = Exception

    mock_cur.fetchone.return_value = None

    with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
        loader = ConfigLoader(client_id="inexistente")
        loader.database_url = "postgresql://test:test@localhost/test"
        result = loader.load_db_config()

    assert result["erp_type"] is None
    assert result["flows"] == []


@patch("config.loader.psycopg2")
def test_load_db_config_sin_flows_activos(mock_psycopg2):
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_psycopg2.connect.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cur
    mock_psycopg2.Error = Exception

    mock_cur.fetchone.return_value = ("ws",)
    mock_cur.fetchall.return_value = []

    with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
        loader = ConfigLoader(client_id="fenix")
        loader.database_url = "postgresql://test:test@localhost/test"
        result = loader.load_db_config()

    assert result["erp_type"] == "ws"
    assert result["flows"] == []


@patch("config.loader.psycopg2")
def test_load_db_config_multiples_flows(mock_psycopg2):
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_psycopg2.connect.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cur
    mock_psycopg2.Error = Exception

    mock_cur.fetchone.return_value = ("connekta",)
    mock_cur.fetchall.return_value = [
        (1, "items", "items", {"mapping": {}}, "0 6 * * *"),
        (2, "partners", "customer", {"mapping": {}}, "5 6 * * *"),
        (3, "compras", "purchases", {"mapping": {}}, "30 6 * * *"),
    ]

    with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
        loader = ConfigLoader(client_id="titopabon")
        loader.database_url = "postgresql://test:test@localhost/test"
        result = loader.load_db_config()

    assert result["erp_type"] == "connekta"
    assert len(result["flows"]) == 3
    assert result["flows"][0]["flow_type"] == "items"
    assert result["flows"][1]["flow_type"] == "customer"
    assert result["flows"][2]["flow_type"] == "purchases"


@patch("config.loader.psycopg2")
def test_load_db_config_columns_correctos(mock_psycopg2):
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_psycopg2.connect.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cur
    mock_psycopg2.Error = Exception

    mock_cur.fetchone.return_value = ("sap",)
    mock_cur.fetchall.return_value = [
        (7, "items", "items", {"endpoint": "Items"}, None)
    ]

    with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
        loader = ConfigLoader(client_id="fabercastell")
        loader.database_url = "postgresql://test:test@localhost/test"
        result = loader.load_db_config()

    flow = result["flows"][0]
    assert "flow_id" in flow
    assert "flow_name" in flow
    assert "flow_type" in flow
    assert "flow_config" in flow
    assert "schedule_cron" in flow
    assert flow["flow_id"] == 7
    assert flow["schedule_cron"] is None


@patch("config.loader.psycopg2")
def test_load_db_config_flow_config_es_dict(mock_psycopg2):
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_psycopg2.connect.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cur
    mock_psycopg2.Error = Exception

    flow_config_esperado = {
        "sql": "SELECT referencia FROM tabla",
        "uom_mapping": {"UND": "Unidades"}
    }
    mock_cur.fetchone.return_value = ("ws",)
    mock_cur.fetchall.return_value = [
        (1, "items", "items", flow_config_esperado, "0 */2 * * *")
    ]

    with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
        loader = ConfigLoader(client_id="fenix")
        loader.database_url = "postgresql://test:test@localhost/test"
        result = loader.load_db_config()

    assert result["flows"][0]["flow_config"] == flow_config_esperado
    assert isinstance(result["flows"][0]["flow_config"], dict)


def test_load_db_config_database_url_no_configurada():
    with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
        loader = ConfigLoader(client_id="fenix")
        loader.database_url = None
        result = loader.load_db_config()

    assert result["erp_type"] is None
    assert result["flows"] == []


@patch("config.loader.psycopg2")
def test_load_db_config_error_psycopg2(mock_psycopg2):
    mock_psycopg2.connect.side_effect = Exception("BD caida")
    mock_psycopg2.Error = Exception
    mock_psycopg2.OperationalError = Exception

    with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
        loader = ConfigLoader(client_id="fenix")
        loader.database_url = "postgresql://test:test@localhost/test"
        result = loader.load_db_config()

    assert result["erp_type"] is None
    assert result["flows"] == []


@patch("config.loader.psycopg2")
def test_load_db_config_cierra_conexion_en_exito(mock_psycopg2):
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_psycopg2.connect.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cur
    mock_psycopg2.Error = Exception

    mock_cur.fetchone.return_value = ("ws",)
    mock_cur.fetchall.return_value = []

    with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
        loader = ConfigLoader(client_id="fenix")
        loader.database_url = "postgresql://test:test@localhost/test"
        loader.load_db_config()

    mock_conn.close.assert_called_once()


@patch("config.loader.psycopg2")
def test_load_db_config_cierra_conexion_en_error(mock_psycopg2):
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_psycopg2.connect.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cur
    mock_psycopg2.Error = Exception

    mock_cur.fetchone.side_effect = Exception("query fallo")

    with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
        loader = ConfigLoader(client_id="fenix")
        loader.database_url = "postgresql://test:test@localhost/test"
        loader.load_db_config()

    mock_conn.close.assert_called_once()


@patch("config.loader.psycopg2")
def test_load_db_config_loguea_error_cliente_no_encontrado(mock_psycopg2):
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_psycopg2.connect.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cur
    mock_psycopg2.Error = Exception

    mock_cur.fetchone.return_value = None

    with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
        loader = ConfigLoader(client_id="fantasma")
        loader.database_url = "postgresql://test:test@localhost/test"
        with patch.object(loader.logger, "error") as mock_error:
            loader.load_db_config()
            mock_error.assert_called_once()
            assert "fantasma" in mock_error.call_args[0][0]