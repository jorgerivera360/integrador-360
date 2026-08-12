"""
test_main.py — Pruebas de db/writer.py y main.py
Total: 54 pruebas en 6 clases
  - TestDBWriter: 20
  - TestBuildConnector: 5
  - TestBuildTransform: 5
  - TestConnectionData: 3
  - TestDispatchFlow: 8
  - TestRun: 13
Fase: 6 — Conexion BD + Main
"""
import os
import json
import pytest
from unittest.mock import patch, MagicMock, call

# -- Config ficticio

MAIN_CONFIG = {
    "client_id": "test_client",
    "erp": {
        "tipo":       "ws",
        "url":        "https://test-ws.asmx?wsdl",
        "compania":   "1",
        "usuario":    "test",
        "clave":      "test",
        "conexion":   "Test",
        "proveedor":  "BEXCONNECT",
        "proxy_host": None,
        "proxy_port": None
    },
    "odoo": {
        "url":      "https://test.odoo.com",
        "database": "test_db",
        "usuario":  "test@test.com",
        "clave":    "test123"
    }
}

SAP_CONFIG = {
    "client_id": "test_client",
    "erp": {
        "tipo":     "sap",
        "url":      "https://test-sap:50000",
        "compania": "TEST",
        "usuario":  "test",
        "clave":    "test"
    },
    "odoo": {
        "url":      "https://test.odoo.com",
        "database": "test_db",
        "usuario":  "test@test.com",
        "clave":    "test123"
    }
}

CONNEKTA_CONFIG = {
    "client_id": "test_client",
    "erp": {
        "tipo":       "connekta",
        "url":        "https://test-connekta.com/api",
        "url_qa":     "",
        "idcompania": "1234",
        "connikey":   "key123",
        "connitoken": "token123"
    },
    "odoo": {
        "url":      "https://test.odoo.com",
        "database": "test_db",
        "usuario":  "test@test.com",
        "clave":    "test123"
    }
}

EXCEL_CONFIG = {
    "client_id": "test_client",
    "erp": {"tipo": "excel"},
    "odoo": {
        "url":      "https://test.odoo.com",
        "database": "test_db",
        "usuario":  "test@test.com",
        "clave":    "test123"
    }
}

FLOW_ITEMS = {
    "flow_id": 1,
    "flow_name": "items",
    "flow_type": "items",
    "flow_config": {"sql": "SELECT 1 AS referencia", "uom_mapping": {}},
    "schedule_cron": "0 */2 * * *"
}

FLOW_CUSTOMER = {
    "flow_id": 2,
    "flow_name": "partners",
    "flow_type": "customer",
    "flow_config": {"sql": "SELECT 1 AS nombre"},
    "schedule_cron": "5 */2 * * *"
}

FLOW_SUPPLIER = {
    "flow_id": 3,
    "flow_name": "partners",
    "flow_type": "supplier",
    "flow_config": {"sql": "SELECT 1 AS nombre"},
    "schedule_cron": "10 */2 * * *"
}

FLOW_PURCHASES = {
    "flow_id": 4,
    "flow_name": "compras",
    "flow_type": "purchases",
    "flow_config": {"sql": "SELECT 1 AS compra", "warehouse_mapping": {"001": 15}},
    "schedule_cron": "30 */2 * * *"
}

FLOW_SALES = {
    "flow_id": 5,
    "flow_name": "ventas",
    "flow_type": "sales",
    "flow_config": {"sql": "SELECT 1 AS pedido", "warehouse_mapping": {"001": 20}},
    "schedule_cron": "35 */2 * * *"
}

FLOW_CONFIGS_MAESTROS = {
    "items":    {"sql": "SELECT 1"},
    "customer": {"sql": "SELECT 1"},
    "supplier": {"sql": "SELECT 1"},
}


# ============================================================
# TestDBWriter — 20 pruebas
# ============================================================

@patch.dict(os.environ, {"ENV": "dev"})
class TestDBWriter:

    def test_constructor_guarda_atributos(self):
        from db.writer import DBWriter
        logger = MagicMock()
        writer = DBWriter(database_url="postgresql://test", logger=logger)
        assert writer.database_url == "postgresql://test"
        assert writer.logger == logger

    def test_constructor_sin_logger(self):
        from db.writer import DBWriter
        writer = DBWriter(database_url="postgresql://test")
        assert writer.logger is None

    def test_get_db_connection_sin_url_lanza_error(self):
        from db.writer import DBWriter
        writer = DBWriter(database_url=None)
        with pytest.raises(RuntimeError, match="DATABASE_URL"):
            writer._get_db_connection()

    @patch("db.writer.psycopg2")
    def test_get_db_connection_llama_psycopg2_connect(self, mock_psycopg2):
        from db.writer import DBWriter
        mock_psycopg2.connect.return_value = MagicMock()
        writer = DBWriter(database_url="postgresql://test")
        conn = writer._get_db_connection()
        mock_psycopg2.connect.assert_called_once_with("postgresql://test")
        assert conn is not None

    @patch("db.writer.psycopg2")
    def test_start_execution_retorna_id(self, mock_psycopg2):
        from db.writer import DBWriter
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_psycopg2.connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cur
        mock_cur.fetchone.return_value = (42,)

        writer = DBWriter(database_url="postgresql://test", logger=MagicMock())
        result = writer.start_execution(flow_id=1, triggered_by="scheduler")
        assert result == 42

    @patch("db.writer.psycopg2")
    def test_start_execution_con_triggered_user(self, mock_psycopg2):
        from db.writer import DBWriter
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_psycopg2.connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cur
        mock_cur.fetchone.return_value = (10,)

        writer = DBWriter(database_url="postgresql://test", logger=MagicMock())
        result = writer.start_execution(flow_id=1, triggered_by="manual", triggered_user=3)
        assert result == 10
        args = mock_cur.execute.call_args[0][1]
        assert args == (1, "manual", 3)

    @patch("db.writer.psycopg2")
    def test_start_execution_hace_commit(self, mock_psycopg2):
        from db.writer import DBWriter
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_psycopg2.connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cur
        mock_cur.fetchone.return_value = (1,)

        writer = DBWriter(database_url="postgresql://test", logger=MagicMock())
        writer.start_execution(flow_id=1)
        mock_conn.commit.assert_called_once()

    @patch("db.writer.psycopg2")
    def test_start_execution_bd_falla_retorna_none(self, mock_psycopg2):
        from db.writer import DBWriter
        mock_psycopg2.connect.side_effect = Exception("BD caida")

        writer = DBWriter(database_url="postgresql://test", logger=MagicMock())
        result = writer.start_execution(flow_id=1)
        assert result is None

    @patch("db.writer.psycopg2")
    def test_start_execution_sin_logger_no_falla(self, mock_psycopg2):
        from db.writer import DBWriter
        mock_psycopg2.connect.side_effect = Exception("BD caida")

        writer = DBWriter(database_url="postgresql://test", logger=None)
        result = writer.start_execution(flow_id=1)
        assert result is None

    @patch("db.writer.psycopg2")
    def test_start_execution_cierra_conexion(self, mock_psycopg2):
        from db.writer import DBWriter
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_psycopg2.connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cur
        mock_cur.fetchone.return_value = (1,)

        writer = DBWriter(database_url="postgresql://test", logger=MagicMock())
        writer.start_execution(flow_id=1)
        mock_conn.close.assert_called_once()

    @patch("db.writer.psycopg2")
    def test_start_execution_cierra_conexion_si_falla(self, mock_psycopg2):
        from db.writer import DBWriter
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_psycopg2.connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cur
        mock_cur.execute.side_effect = Exception("query fallo")

        writer = DBWriter(database_url="postgresql://test", logger=MagicMock())
        writer.start_execution(flow_id=1)
        mock_conn.close.assert_called_once()

    @patch("db.writer.psycopg2")
    def test_start_execution_loguea_info(self, mock_psycopg2):
        from db.writer import DBWriter
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_psycopg2.connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cur
        mock_cur.fetchone.return_value = (99,)

        logger = MagicMock()
        writer = DBWriter(database_url="postgresql://test", logger=logger)
        writer.start_execution(flow_id=5)
        logger.info.assert_called_once()
        assert "99" in logger.info.call_args[0][0]

    @patch("db.writer.psycopg2")
    def test_finish_execution_actualiza(self, mock_psycopg2):
        from db.writer import DBWriter
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_psycopg2.connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cur

        writer = DBWriter(database_url="postgresql://test", logger=MagicMock())
        writer.finish_execution(execution_id=42, status="success", result={"creados": 10})
        mock_cur.execute.assert_called_once()
        args = mock_cur.execute.call_args[0][1]
        assert args[0] == "success"
        assert json.loads(args[1]) == {"creados": 10}
        assert args[3] == 42

    @patch("db.writer.psycopg2")
    def test_finish_execution_con_error_message(self, mock_psycopg2):
        from db.writer import DBWriter
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_psycopg2.connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cur

        writer = DBWriter(database_url="postgresql://test", logger=MagicMock())
        writer.finish_execution(execution_id=42, status="error", error_message="Traceback: ...")
        args = mock_cur.execute.call_args[0][1]
        assert args[0] == "error"
        assert args[1] is None
        assert args[2] == "Traceback: ..."

    def test_finish_execution_id_none_retorna_inmediato(self):
        from db.writer import DBWriter
        writer = DBWriter(database_url="postgresql://test", logger=MagicMock())
        writer.finish_execution(execution_id=None, status="success")

    @patch("db.writer.psycopg2")
    def test_finish_execution_bd_falla_no_explota(self, mock_psycopg2):
        from db.writer import DBWriter
        mock_psycopg2.connect.side_effect = Exception("BD caida")

        writer = DBWriter(database_url="postgresql://test", logger=MagicMock())
        writer.finish_execution(execution_id=42, status="error")

    @patch("db.writer.psycopg2")
    def test_finish_execution_result_none(self, mock_psycopg2):
        from db.writer import DBWriter
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_psycopg2.connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cur

        writer = DBWriter(database_url="postgresql://test", logger=MagicMock())
        writer.finish_execution(execution_id=42, status="error", result=None)
        args = mock_cur.execute.call_args[0][1]
        assert args[1] is None

    @patch("db.writer.psycopg2")
    def test_finish_execution_hace_commit(self, mock_psycopg2):
        from db.writer import DBWriter
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_psycopg2.connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cur

        writer = DBWriter(database_url="postgresql://test", logger=MagicMock())
        writer.finish_execution(execution_id=1, status="success")
        mock_conn.commit.assert_called_once()

    @patch("db.writer.psycopg2")
    def test_finish_execution_cierra_conexion(self, mock_psycopg2):
        from db.writer import DBWriter
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_psycopg2.connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cur

        writer = DBWriter(database_url="postgresql://test", logger=MagicMock())
        writer.finish_execution(execution_id=1, status="success")
        mock_conn.close.assert_called_once()

    @patch("db.writer.psycopg2")
    def test_finish_execution_cierra_conexion_si_falla(self, mock_psycopg2):
        from db.writer import DBWriter
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_psycopg2.connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cur
        mock_cur.execute.side_effect = Exception("query fallo")

        writer = DBWriter(database_url="postgresql://test", logger=MagicMock())
        writer.finish_execution(execution_id=1, status="success")
        mock_conn.close.assert_called_once()


# ============================================================
# TestBuildConnector — 5 pruebas
# ============================================================

@patch.dict(os.environ, {"ENV": "dev"})
class TestBuildConnector:

    def test_ws_retorna_siesa_enterprise(self):
        from main import build_connector
        from connection.siesa_enterprise import SiesaEnterprise
        connector = build_connector("ws", MAIN_CONFIG)
        assert isinstance(connector, SiesaEnterprise)

    def test_connekta_retorna_siesa_connekta(self):
        from main import build_connector
        from connection.siesa_connekta import SiesaConnekta
        connector = build_connector("connekta", CONNEKTA_CONFIG)
        assert isinstance(connector, SiesaConnekta)

    def test_sap_retorna_sap(self):
        from main import build_connector
        from connection.sap import SAP
        connector = build_connector("sap", SAP_CONFIG)
        assert isinstance(connector, SAP)

    def test_excel_retorna_excel_connector(self):
        from main import build_connector
        from connection.excel_connector import ExcelConnector
        connector = build_connector("excel", EXCEL_CONFIG)
        assert isinstance(connector, ExcelConnector)

    def test_tipo_invalido_lanza_value_error(self):
        from main import build_connector
        with pytest.raises(ValueError, match="no soportado"):
            build_connector("oracle", MAIN_CONFIG)


# ============================================================
# TestBuildTransform — 5 pruebas
# ============================================================

@patch.dict(os.environ, {"ENV": "dev"})
class TestBuildTransform:

    def test_ws_retorna_transform_ws(self):
        from main import build_transform
        from transform.transform_ws import TransformWS
        transform = build_transform("ws", MAIN_CONFIG)
        assert isinstance(transform, TransformWS)

    def test_connekta_retorna_transform_connekta(self):
        from main import build_transform
        from transform.transform_connekta import TransformConnekta
        transform = build_transform("connekta", CONNEKTA_CONFIG)
        assert isinstance(transform, TransformConnekta)

    def test_sap_retorna_transform_sap(self):
        from main import build_transform
        from transform.transform_sap import TransformSAP
        transform = build_transform("sap", SAP_CONFIG)
        assert isinstance(transform, TransformSAP)

    def test_excel_retorna_transform_ws(self):
        from main import build_transform
        from transform.transform_ws import TransformWS
        transform = build_transform("excel", EXCEL_CONFIG)
        assert isinstance(transform, TransformWS)

    def test_tipo_invalido_lanza_value_error(self):
        from main import build_transform
        with pytest.raises(ValueError, match="no soportado"):
            build_transform("oracle", MAIN_CONFIG)


# ============================================================
# TestConnectionData — 3 pruebas
# ============================================================

@patch.dict(os.environ, {"ENV": "dev"})
class TestConnectionData:

    @patch("main.JsonRPC")
    def test_autenticacion_exitosa_retorna_odoo(self, mock_jsonrpc_cls):
        from main import connection_data
        mock_odoo = MagicMock()
        mock_odoo.authenticate.return_value = (True, "OK")
        mock_jsonrpc_cls.return_value = mock_odoo

        result = connection_data(MAIN_CONFIG)
        assert result == mock_odoo
        mock_odoo.authenticate.assert_called_once()

    @patch("main.JsonRPC")
    def test_autenticacion_falla_lanza_runtime_error(self, mock_jsonrpc_cls):
        from main import connection_data
        mock_odoo = MagicMock()
        mock_odoo.authenticate.return_value = (False, "Credenciales invalidas")
        mock_jsonrpc_cls.return_value = mock_odoo

        with pytest.raises(RuntimeError, match="No se pudo autenticar"):
            connection_data(MAIN_CONFIG)

    @patch("main.JsonRPC")
    def test_pasa_config_al_constructor(self, mock_jsonrpc_cls):
        from main import connection_data
        mock_odoo = MagicMock()
        mock_odoo.authenticate.return_value = (True, "OK")
        mock_jsonrpc_cls.return_value = mock_odoo

        connection_data(MAIN_CONFIG)
        mock_jsonrpc_cls.assert_called_once_with(MAIN_CONFIG)


# ============================================================
# TestDispatchFlow — 8 pruebas
# ============================================================

@patch.dict(os.environ, {"ENV": "dev"})
class TestDispatchFlow:

    @patch("main.ProcessItems")
    def test_items_usa_process_items(self, mock_cls):
        from main import _dispatch_flow
        mock_cls.return_value.process.return_value = {"creados": 5}
        result = _dispatch_flow([], "items", MagicMock(), MAIN_CONFIG, {})
        mock_cls.assert_called_once()
        assert result == {"creados": 5}

    @patch("main.ProcessPartners")
    def test_customer_usa_process_partners(self, mock_cls):
        from main import _dispatch_flow
        mock_cls.return_value.process.return_value = {"creados": 3}
        result = _dispatch_flow([], "customer", MagicMock(), MAIN_CONFIG, {})
        mock_cls.assert_called_once()

    @patch("main.ProcessPartners")
    def test_supplier_usa_process_partners(self, mock_cls):
        from main import _dispatch_flow
        mock_cls.return_value.process.return_value = {"creados": 2}
        result = _dispatch_flow([], "supplier", MagicMock(), MAIN_CONFIG, {})
        mock_cls.assert_called_once()

    @patch("main.ProcessPurchases")
    def test_purchases_usa_process_purchases(self, mock_cls):
        from main import _dispatch_flow
        mock_cls.return_value.process.return_value = {"creados": 1}
        result = _dispatch_flow([], "purchases", MagicMock(), MAIN_CONFIG, {})
        mock_cls.assert_called_once()

    @patch("main.ProcessSales")
    def test_sales_usa_process_sales(self, mock_cls):
        from main import _dispatch_flow
        mock_cls.return_value.process.return_value = {"creados": 4}
        result = _dispatch_flow([], "sales", MagicMock(), MAIN_CONFIG, {})
        mock_cls.assert_called_once()

    def test_tipo_invalido_lanza_value_error(self):
        from main import _dispatch_flow
        with pytest.raises(ValueError, match="no soportado"):
            _dispatch_flow([], "inventario", MagicMock(), MAIN_CONFIG, {})

    @patch("main.ProcessItems")
    def test_pasa_odoo_config_flow_config(self, mock_cls):
        from main import _dispatch_flow
        mock_cls.return_value.process.return_value = {}
        odoo = MagicMock()
        fc = {"uom_mapping": {"UND": "Unidades"}}

        _dispatch_flow([], "items", odoo, MAIN_CONFIG, fc)
        mock_cls.assert_called_once_with(odoo, MAIN_CONFIG, fc)

    @patch("main.ProcessItems")
    def test_pasa_data_a_process(self, mock_cls):
        from main import _dispatch_flow
        mock_cls.return_value.process.return_value = {}
        data = [{"referencia": "P001"}, {"referencia": "P002"}]

        _dispatch_flow(data, "items", MagicMock(), MAIN_CONFIG, {})
        mock_cls.return_value.process.assert_called_once_with(data)


# ============================================================
# TestRun — 13 pruebas
# ============================================================

@patch.dict(os.environ, {"ENV": "dev"})
class TestRun:

    @patch("main._dispatch_flow")
    @patch("main.connection_data")
    @patch("main.build_transform")
    @patch("main.build_connector")
    def test_flow_maestro_exitoso(self, mock_bc, mock_bt, mock_cd, mock_df):
        from main import run
        mock_bt.return_value.get_flow.return_value = [{"referencia": "P001"}]
        mock_df.return_value = {"creados": 1, "actualizados": 0, "fallidos": [], "total": 1}

        result = run(FLOW_ITEMS, MAIN_CONFIG, "ws")
        assert result["creados"] == 1
        mock_bc.assert_called_once_with("ws", MAIN_CONFIG)
        mock_bt.assert_called_once_with("ws", MAIN_CONFIG)

    @patch("main.resolve_missing_masters")
    @patch("main._dispatch_flow")
    @patch("main.connection_data")
    @patch("main.build_transform")
    @patch("main.build_connector")
    def test_flow_transaccion_llama_resolve(self, mock_bc, mock_bt, mock_cd, mock_df, mock_resolve):
        from main import run
        data = [{"compra": "OC-001", "producto": "P001"}]
        mock_bt.return_value.get_flow.return_value = data
        mock_df.return_value = {"creados": 1, "fallidos": [], "total": 1}

        run(FLOW_PURCHASES, MAIN_CONFIG, "ws", flow_configs=FLOW_CONFIGS_MAESTROS)
        mock_resolve.assert_called_once()
        args = mock_resolve.call_args[0]
        assert args[3] == data
        assert args[4] is None

    @patch("main.resolve_missing_masters")
    @patch("main._dispatch_flow")
    @patch("main.connection_data")
    @patch("main.build_transform")
    @patch("main.build_connector")
    def test_flow_sales_pasa_data_sales(self, mock_bc, mock_bt, mock_cd, mock_df, mock_resolve):
        from main import run
        data = [{"pedido": "PV-001", "producto": "P001"}]
        mock_bt.return_value.get_flow.return_value = data
        mock_df.return_value = {"creados": 1, "fallidos": [], "total": 1}

        run(FLOW_SALES, MAIN_CONFIG, "ws", flow_configs=FLOW_CONFIGS_MAESTROS)
        args = mock_resolve.call_args[0]
        assert args[3] is None
        assert args[4] == data

    @patch("main._dispatch_flow")
    @patch("main.connection_data")
    @patch("main.build_transform")
    @patch("main.build_connector")
    def test_resolve_no_se_llama_para_maestros(self, mock_bc, mock_bt, mock_cd, mock_df):
        from main import run
        mock_bt.return_value.get_flow.return_value = [{"referencia": "P001"}]
        mock_df.return_value = {"creados": 1, "fallidos": [], "total": 1}

        with patch("main.resolve_missing_masters") as mock_resolve:
            run(FLOW_ITEMS, MAIN_CONFIG, "ws", flow_configs=FLOW_CONFIGS_MAESTROS)
            mock_resolve.assert_not_called()

    @patch("main._dispatch_flow")
    @patch("main.connection_data")
    @patch("main.build_transform")
    @patch("main.build_connector")
    def test_resolve_no_se_llama_sin_flow_configs(self, mock_bc, mock_bt, mock_cd, mock_df):
        from main import run
        mock_bt.return_value.get_flow.return_value = [{"compra": "OC-001"}]
        mock_df.return_value = {"creados": 1, "fallidos": [], "total": 1}

        with patch("main.resolve_missing_masters") as mock_resolve:
            run(FLOW_PURCHASES, MAIN_CONFIG, "ws", flow_configs=None)
            mock_resolve.assert_not_called()

    @patch("main.build_transform")
    @patch("main.build_connector")
    def test_data_vacia_retorna_sin_procesar(self, mock_bc, mock_bt):
        from main import run
        mock_bt.return_value.get_flow.return_value = []

        result = run(FLOW_ITEMS, MAIN_CONFIG, "ws")
        assert result["creados"] == 0
        assert result["total"] == 0

    @patch("main._dispatch_flow")
    @patch("main.connection_data")
    @patch("main.build_transform")
    @patch("main.build_connector")
    def test_status_success_sin_fallidos(self, mock_bc, mock_bt, mock_cd, mock_df):
        from main import run
        mock_bt.return_value.get_flow.return_value = [{"referencia": "P001"}]
        mock_df.return_value = {"creados": 1, "fallidos": [], "total": 1}

        db_writer = MagicMock()
        db_writer.start_execution.return_value = 99
        run(FLOW_ITEMS, MAIN_CONFIG, "ws", db_writer=db_writer)
        db_writer.finish_execution.assert_called_once_with(99, "success", {"creados": 1, "fallidos": [], "total": 1})

    @patch("main._dispatch_flow")
    @patch("main.connection_data")
    @patch("main.build_transform")
    @patch("main.build_connector")
    def test_status_partial_con_fallidos(self, mock_bc, mock_bt, mock_cd, mock_df):
        from main import run
        mock_bt.return_value.get_flow.return_value = [{"referencia": "P001"}]
        result_con_fallidos = {
            "creados": 1,
            "fallidos": [{"referencia": "P002", "razon": "UOM no existe"}],
            "total": 2
        }
        mock_df.return_value = result_con_fallidos

        db_writer = MagicMock()
        db_writer.start_execution.return_value = 99
        run(FLOW_ITEMS, MAIN_CONFIG, "ws", db_writer=db_writer)
        db_writer.finish_execution.assert_called_once_with(99, "partial", result_con_fallidos)

    @patch("main._dispatch_flow")
    @patch("main.connection_data")
    @patch("main.build_transform")
    @patch("main.build_connector")
    def test_excepcion_registra_error_en_bd(self, mock_bc, mock_bt, mock_cd, mock_df):
        from main import run
        mock_bt.return_value.get_flow.return_value = [{"referencia": "P001"}]
        mock_df.side_effect = Exception("Odoo exploto")

        db_writer = MagicMock()
        db_writer.start_execution.return_value = 99

        with pytest.raises(Exception, match="Odoo exploto"):
            run(FLOW_ITEMS, MAIN_CONFIG, "ws", db_writer=db_writer)

        db_writer.finish_execution.assert_called_once()
        args = db_writer.finish_execution.call_args[0]
        assert args[0] == 99
        assert args[1] == "error"
        assert args[2] is None
        assert "Odoo exploto" in args[3]

    @patch("main._dispatch_flow")
    @patch("main.connection_data")
    @patch("main.build_transform")
    @patch("main.build_connector")
    def test_sin_db_writer_ejecuta_sin_registrar(self, mock_bc, mock_bt, mock_cd, mock_df):
        from main import run
        mock_bt.return_value.get_flow.return_value = [{"referencia": "P001"}]
        mock_df.return_value = {"creados": 1, "fallidos": [], "total": 1}

        result = run(FLOW_ITEMS, MAIN_CONFIG, "ws", db_writer=None)
        assert result["creados"] == 1

    @patch("main._dispatch_flow")
    @patch("main.connection_data")
    @patch("main.build_transform")
    @patch("main.build_connector")
    def test_db_writer_recibe_triggered_by_y_user(self, mock_bc, mock_bt, mock_cd, mock_df):
        from main import run
        mock_bt.return_value.get_flow.return_value = [{"referencia": "P001"}]
        mock_df.return_value = {"creados": 1, "fallidos": [], "total": 1}

        db_writer = MagicMock()
        db_writer.start_execution.return_value = 50
        run(FLOW_ITEMS, MAIN_CONFIG, "ws", db_writer=db_writer,
            triggered_by="manual", triggered_user=3)
        db_writer.start_execution.assert_called_once_with(1, "manual", 3)

    @patch("main.build_transform")
    @patch("main.build_connector")
    def test_data_vacia_registra_success_en_bd(self, mock_bc, mock_bt):
        from main import run
        mock_bt.return_value.get_flow.return_value = []

        db_writer = MagicMock()
        db_writer.start_execution.return_value = 77
        run(FLOW_ITEMS, MAIN_CONFIG, "ws", db_writer=db_writer)
        db_writer.finish_execution.assert_called_once()
        args = db_writer.finish_execution.call_args[0]
        assert args[0] == 77
        assert args[1] == "success"

    @patch("main.build_connector")
    def test_error_en_transform_registra_error(self, mock_bc):
        from main import run
        with patch("main.build_transform") as mock_bt:
            mock_bt.return_value.get_flow.side_effect = Exception("SQL invalido")

            db_writer = MagicMock()
            db_writer.start_execution.return_value = 88

            with pytest.raises(Exception, match="SQL invalido"):
                run(FLOW_ITEMS, MAIN_CONFIG, "ws", db_writer=db_writer)

            db_writer.finish_execution.assert_called_once()
            args = db_writer.finish_execution.call_args[0]
            assert args[1] == "error"
            assert "SQL invalido" in args[3]