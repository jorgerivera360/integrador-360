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