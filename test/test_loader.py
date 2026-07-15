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
import logging
import pytest
from unittest.mock import patch, MagicMock, patch as mock_patch
from config.loader import ConfigLoader
from config.logger import IntegradorLogger


@pytest.fixture(autouse=True)
def limpiar_handlers_logger():
    yield
    # Limpia los handlers de cualquier logger que comience con 'integrador'
    for name in list(logging.Logger.manager.loggerDict.keys()):
        if name.startswith("integrador"):
            logger = logging.getLogger(name)
            for handler in list(logger.handlers):
                handler.close()
                logger.removeHandler(handler)


# ════════════════════════════════════════════════════
# CONSTRUCTOR
# ════════════════════════════════════════════════════

def test_constructor_client_id():
    with patch.dict(os.environ, {'ENV': 'dev'}, clear=True):
        loader = ConfigLoader(client_id='fenix')
        assert loader.client_id == 'fenix'


def test_constructor_env_desde_variable():
    with patch.dict(os.environ, {'ENV': 'staging'}, clear=True):
        loader = ConfigLoader(client_id='fenix')
        assert loader.env == 'staging'


def test_constructor_project_id_desde_variable():
    with patch.dict(os.environ, {'ENV': 'dev', 'GCP_PROJECT_ID': 'mi-proyecto-123'}, clear=True):
        loader = ConfigLoader(client_id='fenix')
        assert loader.project_id == 'mi-proyecto-123'


def test_constructor_credentials_path_default():
    with patch.dict(os.environ, {}, clear=True):
        loader = ConfigLoader(client_id='fenix')
        assert loader.credentials_path == '/etc/integrador/credentials'


# ════════════════════════════════════════════════════
# _load_from_gcp()
# ════════════════════════════════════════════════════

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
            'ENV':              'dev',
            'GCP_PROJECT_ID':   'proyecto-test',
            'CREDENTIALS_PATH': str(tmp_path)
        }, clear=True):
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
            'ENV':              'dev',
            'GCP_PROJECT_ID':   'proyecto-test',
            'CREDENTIALS_PATH': str(tmp_path)
        }, clear=True):
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


# ════════════════════════════════════════════════════
# save_credentials()
# ════════════════════════════════════════════════════

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


# ════════════════════════════════════════════════════
# load_credentials()
# ════════════════════════════════════════════════════

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


def test_load_credentials_registra_warning_al_cargar_local(tmp_path):
    config  = {"erp": {"tipo": "ws"}, "odoo": {"url": "http://test"}}
    archivo = tmp_path / "integrador-cliente_prueba.json"
    archivo.write_text(json.dumps(config))

    with patch.dict(os.environ, {
        'ENV':              'dev',
        'CREDENTIALS_PATH': str(tmp_path)
    }, clear=True):
        loader = ConfigLoader(client_id='cliente_prueba')
        with patch.object(loader.logger, 'warning') as mock_warning:
            loader.load_credentials()
            mock_warning.assert_called_once()


def test_load_credentials_registra_critical_sin_archivo(tmp_path):
    with patch.dict(os.environ, {
        'ENV':              'dev',
        'CREDENTIALS_PATH': str(tmp_path)
    }, clear=True):
        loader = ConfigLoader(client_id='cliente_prueba')
        with patch.object(loader.logger, 'critical') as mock_critical:
            with pytest.raises(RuntimeError):
                loader.load_credentials()
            mock_critical.assert_called_once()


# ════════════════════════════════════════════════════
# credentials_exist()
# ════════════════════════════════════════════════════

def test_credentials_exist_retorna_true_cuando_existe(tmp_path):
    archivo = tmp_path / "integrador-cliente_prueba.json"
    archivo.write_text('{"erp": {}, "odoo": {}}')

    with patch.dict(os.environ, {
        'ENV':              'dev',
        'CREDENTIALS_PATH': str(tmp_path)
    }, clear=True):
        loader = ConfigLoader(client_id='cliente_prueba')
        assert loader.credentials_exist() == True


def test_credentials_exist_retorna_false_cuando_no_existe(tmp_path):
    with patch.dict(os.environ, {
        'ENV':              'dev',
        'CREDENTIALS_PATH': str(tmp_path)
    }, clear=True):
        loader = ConfigLoader(client_id='cliente_prueba')
        assert loader.credentials_exist() == False


# ════════════════════════════════════════════════════
# load_config()
# ════════════════════════════════════════════════════

def test_load_config_retorna_dict_con_erp_y_odoo(tmp_path):
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
            loader    = ConfigLoader(client_id='cliente_prueba')
            resultado = loader.load_config()
            assert 'erp'  in resultado
            assert 'odoo' in resultado


def test_load_config_funciona_con_gcp_disponible(tmp_path):
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
            loader    = ConfigLoader(client_id='cliente_prueba')
            resultado = loader.load_config()
            assert resultado == config_mock


def test_load_config_funciona_cuando_gcp_falla_y_hay_credenciales(tmp_path):
    config  = {"erp": {"tipo": "ws"}, "odoo": {"url": "http://test"}}
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
            resultado = loader.load_config()
            assert resultado == config


def test_load_config_falla_cuando_gcp_falla_y_no_hay_credenciales(tmp_path):
    with patch('config.loader.secretmanager.SecretManagerServiceClient') as mock_client:
        mock_client.return_value.access_secret_version.side_effect = Exception("GCP caído")

        with patch.dict(os.environ, {
            'ENV':              'dev',
            'GCP_PROJECT_ID':   'proyecto-test',
            'CREDENTIALS_PATH': str(tmp_path)
        }, clear=True):
            loader = ConfigLoader(client_id='cliente_prueba')
            with pytest.raises(RuntimeError):
                loader.load_config()


# ════════════════════════════════════════════════════
# FLUJO COMPLETO
# ════════════════════════════════════════════════════

def test_flujo_completo_primera_ejecucion_gcp_trae_y_guarda(tmp_path):
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
            loader.load_config()

            archivo = tmp_path / "integrador-cliente_prueba.json"
            assert archivo.exists()
            assert json.loads(archivo.read_text()) == config_mock


def test_flujo_completo_segunda_ejecucion_gcp_caido_carga_local(tmp_path):
    config_mock = {
        "erp":  {"tipo": "ws"},
        "odoo": {"url": "http://odoo-test"}
    }

    # Primera ejecución — GCP funciona — guarda localmente
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
            loader.load_config()

    # Segunda ejecución — GCP cae — carga desde local
    with patch('config.loader.secretmanager.SecretManagerServiceClient') as mock_client:
        mock_client.return_value.access_secret_version.side_effect = Exception("GCP caído")

        with patch.dict(os.environ, {
            'ENV':              'dev',
            'GCP_PROJECT_ID':   'proyecto-test',
            'CREDENTIALS_PATH': str(tmp_path)
        }, clear=True):
            loader    = ConfigLoader(client_id='cliente_prueba')
            resultado = loader.load_config()
            assert resultado == config_mock


def test_flujo_completo_dict_identico_en_ambos_casos(tmp_path):
    config_mock = {
        "erp":  {"tipo": "ws"},
        "odoo": {"url": "http://odoo-test"}
    }

    # Primera ejecución — GCP funciona
    with patch('config.loader.secretmanager.SecretManagerServiceClient') as mock_client:
        mock_response = MagicMock()
        mock_response.payload.data = json.dumps(config_mock).encode('UTF-8')
        mock_client.return_value.access_secret_version.return_value = mock_response

        with patch.dict(os.environ, {
            'ENV':              'dev',
            'GCP_PROJECT_ID':   'proyecto-test',
            'CREDENTIALS_PATH': str(tmp_path)
        }, clear=True):
            loader     = ConfigLoader(client_id='cliente_prueba')
            resultado1 = loader.load_config()

    # Segunda ejecución — GCP cae
    with patch('config.loader.secretmanager.SecretManagerServiceClient') as mock_client:
        mock_client.return_value.access_secret_version.side_effect = Exception("GCP caído")

        with patch.dict(os.environ, {
            'ENV':              'dev',
            'GCP_PROJECT_ID':   'proyecto-test',
            'CREDENTIALS_PATH': str(tmp_path)
        }, clear=True):
            loader     = ConfigLoader(client_id='cliente_prueba')
            resultado2 = loader.load_config()

    assert resultado1 == resultado2


# ════════════════════════════════════════════════════
# IntegradorLogger
# ════════════════════════════════════════════════════

def test_logger_env_dev_logs_van_a_consola(capsys):
    with patch.dict(os.environ, {'ENV': 'dev'}, clear=True):
        logger = IntegradorLogger(client_id='fenix')
        logger.info("mensaje de prueba")

        captured = capsys.readouterr()
        assert "mensaje de prueba" in captured.out


def test_logger_env_staging_logs_van_a_archivo(tmp_path):
    with patch.dict(os.environ, {
        'ENV':      'staging',
        'LOG_PATH': str(tmp_path)
    }, clear=True):
        logger = IntegradorLogger(client_id='fenix')
        logger.info("mensaje de prueba")

        archivo = tmp_path / "integrador-fenix.log"
        assert archivo.exists()


def test_logger_archivo_se_crea_en_log_path(tmp_path):
    with patch.dict(os.environ, {
        'ENV':      'staging',
        'LOG_PATH': str(tmp_path)
    }, clear=True):
        logger = IntegradorLogger(client_id='fenix')
        logger.info("mensaje de prueba")

        archivo = tmp_path / "integrador-fenix.log"
        assert archivo.exists()
        assert "mensaje de prueba" in archivo.read_text()