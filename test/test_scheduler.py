"""
test_scheduler.py — 38 pruebas unitarias para scheduler/runner.py
Clase: IntegradorScheduler
Todo mockeado — sin llamadas reales a GCP, BD, Odoo ni APScheduler
Fase: 7 — Scheduler
"""
import unittest
from unittest.mock import patch, MagicMock, call


SAMPLE_CONFIG = {
    "erp": {"tipo": "ws", "url": "http://test"},
    "odoo": {"url": "https://test.odoo.com", "database": "test", "usuario": "user", "clave": "pass"},
}

SAMPLE_FLOWS = [
    {"flow_id": 1, "flow_name": "items", "flow_type": "items", "flow_config": {"sql": "SELECT 1"}, "schedule_cron": "0 * * * *"},
    {"flow_id": 2, "flow_name": "partners", "flow_type": "customer", "flow_config": {"sql": "SELECT 2"}, "schedule_cron": "0 * * * *"},
    {"flow_id": 3, "flow_name": "partners", "flow_type": "supplier", "flow_config": {"sql": "SELECT 3"}, "schedule_cron": None},
    {"flow_id": 4, "flow_name": "compras", "flow_type": "purchases", "flow_config": {"sql": "SELECT 4"}, "schedule_cron": "*/2 * * * *"},
    {"flow_id": 5, "flow_name": "ventas", "flow_type": "sales", "flow_config": {"sql": "SELECT 5"}, "schedule_cron": "*/2 * * * *"},
]


def _build_scheduler(flows=None, config=None, erp_type="ws"):
    """Helper para construir IntegradorScheduler con todo mockeado."""
    with patch.dict("os.environ", {"ENV": "dev", "DATABASE_URL": "postgresql://test", "CLIENT_ID": "testclient"}):
        with patch("scheduler.runner.ConfigLoader") as MockLoader:
            with patch("scheduler.runner.IntegradorLogger"):
                with patch("scheduler.runner.DBWriter"):
                    with patch("scheduler.runner.BlockingScheduler") as MockScheduler:
                        loader_instance = MockLoader.return_value
                        loader_instance.load_config.return_value = config or {**SAMPLE_CONFIG}
                        loader_instance.load_db_config.return_value = {
                            "erp_type": erp_type,
                            "flows": flows if flows is not None else [f.copy() for f in SAMPLE_FLOWS],
                        }
                        from scheduler.runner import IntegradorScheduler
                        scheduler = IntegradorScheduler("testclient")
                        return scheduler


@patch.dict("os.environ", {"ENV": "dev", "DATABASE_URL": "postgresql://test"})
class TestSchedulerConstructor(unittest.TestCase):

    @patch("scheduler.runner.BlockingScheduler")
    @patch("scheduler.runner.DBWriter")
    @patch("scheduler.runner.IntegradorLogger")
    @patch("scheduler.runner.ConfigLoader")
    def test_constructor_guarda_client_id(self, MockLoader, MockLogger, MockWriter, MockSched):
        MockLoader.return_value.load_config.return_value = {**SAMPLE_CONFIG}
        MockLoader.return_value.load_db_config.return_value = {"erp_type": "ws", "flows": []}
        from scheduler.runner import IntegradorScheduler
        s = IntegradorScheduler("fenix")
        self.assertEqual(s.client_id, "fenix")

    @patch("scheduler.runner.BlockingScheduler")
    @patch("scheduler.runner.DBWriter")
    @patch("scheduler.runner.IntegradorLogger")
    @patch("scheduler.runner.ConfigLoader")
    def test_constructor_crea_logger(self, MockLoader, MockLogger, MockWriter, MockSched):
        MockLoader.return_value.load_config.return_value = {**SAMPLE_CONFIG}
        MockLoader.return_value.load_db_config.return_value = {"erp_type": "ws", "flows": []}
        from scheduler.runner import IntegradorScheduler
        s = IntegradorScheduler("fenix")
        MockLogger.assert_called_with(client_id="fenix")

    @patch("scheduler.runner.BlockingScheduler")
    @patch("scheduler.runner.DBWriter")
    @patch("scheduler.runner.IntegradorLogger")
    @patch("scheduler.runner.ConfigLoader")
    def test_constructor_carga_config_gcp(self, MockLoader, MockLogger, MockWriter, MockSched):
        MockLoader.return_value.load_config.return_value = {**SAMPLE_CONFIG}
        MockLoader.return_value.load_db_config.return_value = {"erp_type": "ws", "flows": []}
        from scheduler.runner import IntegradorScheduler
        s = IntegradorScheduler("fenix")
        MockLoader.return_value.load_config.assert_called_once()
        self.assertEqual(s.config["client_id"], "fenix")
        self.assertEqual(s.config["odoo"]["url"], "https://test.odoo.com")

    @patch("scheduler.runner.BlockingScheduler")
    @patch("scheduler.runner.DBWriter")
    @patch("scheduler.runner.IntegradorLogger")
    @patch("scheduler.runner.ConfigLoader")
    def test_constructor_config_gcp_vacia_lanza_error(self, MockLoader, MockLogger, MockWriter, MockSched):
        MockLoader.return_value.load_config.return_value = None
        from scheduler.runner import IntegradorScheduler
        with self.assertRaises(RuntimeError):
            IntegradorScheduler("fenix")

    @patch("scheduler.runner.BlockingScheduler")
    @patch("scheduler.runner.DBWriter")
    @patch("scheduler.runner.IntegradorLogger")
    @patch("scheduler.runner.ConfigLoader")
    def test_constructor_carga_flows_bd(self, MockLoader, MockLogger, MockWriter, MockSched):
        MockLoader.return_value.load_config.return_value = {**SAMPLE_CONFIG}
        MockLoader.return_value.load_db_config.return_value = {"erp_type": "sap", "flows": SAMPLE_FLOWS}
        from scheduler.runner import IntegradorScheduler
        s = IntegradorScheduler("fenix")
        self.assertEqual(s.erp_type, "sap")
        self.assertEqual(len(s.flows), 5)

    @patch("scheduler.runner.BlockingScheduler")
    @patch("scheduler.runner.DBWriter")
    @patch("scheduler.runner.IntegradorLogger")
    @patch("scheduler.runner.ConfigLoader")
    def test_constructor_crea_scheduler_apscheduler(self, MockLoader, MockLogger, MockWriter, MockSched):
        MockLoader.return_value.load_config.return_value = {**SAMPLE_CONFIG}
        MockLoader.return_value.load_db_config.return_value = {"erp_type": "ws", "flows": []}
        from scheduler.runner import IntegradorScheduler
        s = IntegradorScheduler("fenix")
        MockSched.assert_called_once()
        self.assertIsNotNone(s.scheduler)


@patch.dict("os.environ", {"ENV": "dev", "DATABASE_URL": "postgresql://test"})
class TestReloadFlow(unittest.TestCase):

    @patch("scheduler.runner.psycopg2")
    def test_reload_flow_retorna_dict_fresco(self, mock_pg):
        s = _build_scheduler()
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_pg.connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cur
        mock_cur.fetchone.return_value = (1, "items", "items", {"sql": "SELECT 1"}, "0 * * * *", True)

        result = s._reload_flow(1)
        self.assertEqual(result["flow_id"], 1)
        self.assertEqual(result["flow_name"], "items")
        self.assertEqual(result["is_active"], True)
        self.assertIsInstance(result["flow_config"], dict)

    @patch("scheduler.runner.psycopg2")
    def test_reload_flow_no_encontrado_retorna_none(self, mock_pg):
        s = _build_scheduler()
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_pg.connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cur
        mock_cur.fetchone.return_value = None

        result = s._reload_flow(999)
        self.assertIsNone(result)

    @patch("scheduler.runner.psycopg2")
    def test_reload_flow_bd_falla_retorna_none(self, mock_pg):
        s = _build_scheduler()
        mock_pg.connect.side_effect = Exception("BD caída")

        result = s._reload_flow(1)
        self.assertIsNone(result)

    @patch("scheduler.runner.psycopg2")
    def test_reload_flow_cierra_conexion(self, mock_pg):
        s = _build_scheduler()
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_pg.connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cur
        mock_cur.fetchone.return_value = (1, "items", "items", {}, None, True)

        s._reload_flow(1)
        mock_cur.close.assert_called_once()
        mock_conn.close.assert_called_once()


@patch.dict("os.environ", {"ENV": "dev", "DATABASE_URL": "postgresql://test"})
class TestLoadFlowConfigs(unittest.TestCase):

    @patch("scheduler.runner.psycopg2")
    def test_load_flow_configs_retorna_dict_maestros(self, mock_pg):
        s = _build_scheduler()
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_pg.connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cur
        mock_cur.fetchall.return_value = [
            ("items", {"sql": "SELECT items"}),
            ("customer", {"sql": "SELECT customers"}),
            ("supplier", {"sql": "SELECT suppliers"}),
        ]

        result = s._load_flow_configs()
        self.assertEqual(len(result), 3)
        self.assertIn("items", result)
        self.assertIn("customer", result)
        self.assertIn("supplier", result)

    @patch("scheduler.runner.psycopg2")
    def test_load_flow_configs_sin_maestros_retorna_vacio(self, mock_pg):
        s = _build_scheduler()
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_pg.connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cur
        mock_cur.fetchall.return_value = []

        result = s._load_flow_configs()
        self.assertEqual(result, {})

    @patch("scheduler.runner.psycopg2")
    def test_load_flow_configs_bd_falla_retorna_vacio(self, mock_pg):
        s = _build_scheduler()
        mock_pg.connect.side_effect = Exception("BD caída")

        result = s._load_flow_configs()
        self.assertEqual(result, {})


@patch.dict("os.environ", {"ENV": "dev", "DATABASE_URL": "postgresql://test"})
class TestRunFlow(unittest.TestCase):

    @patch("scheduler.runner.run")
    def test_run_flow_recarga_y_ejecuta(self, mock_run):
        s = _build_scheduler()
        flow = {"flow_id": 1, "flow_name": "items", "flow_type": "items"}
        fresh = {"flow_id": 1, "flow_name": "items", "flow_type": "items",
                  "flow_config": {"sql": "SELECT 1"}, "schedule_cron": "0 * * * *", "is_active": True}
        s._reload_flow = MagicMock(return_value=fresh)
        mock_run.return_value = {"creados": 5, "actualizados": 10, "fallidos": []}

        result = s._run_flow(flow)
        s._reload_flow.assert_called_once_with(1)
        mock_run.assert_called_once()
        self.assertEqual(result["creados"], 5)

    def test_run_flow_flow_no_encontrado_retorna_none(self):
        s = _build_scheduler()
        flow = {"flow_id": 999, "flow_name": "items", "flow_type": "items"}
        s._reload_flow = MagicMock(return_value=None)

        result = s._run_flow(flow)
        self.assertIsNone(result)

    def test_run_flow_flow_inactivo_retorna_none(self):
        s = _build_scheduler()
        flow = {"flow_id": 1, "flow_name": "items", "flow_type": "items"}
        fresh = {"flow_id": 1, "flow_name": "items", "flow_type": "items",
                  "flow_config": {}, "schedule_cron": None, "is_active": False}
        s._reload_flow = MagicMock(return_value=fresh)

        result = s._run_flow(flow)
        self.assertIsNone(result)

    @patch("scheduler.runner.run")
    def test_run_flow_transaccion_carga_flow_configs(self, mock_run):
        s = _build_scheduler()
        flow = {"flow_id": 4, "flow_name": "compras", "flow_type": "purchases"}
        fresh = {"flow_id": 4, "flow_name": "compras", "flow_type": "purchases",
                  "flow_config": {}, "schedule_cron": "*/2 * * * *", "is_active": True}
        s._reload_flow = MagicMock(return_value=fresh)
        s._load_flow_configs = MagicMock(return_value={"items": {}, "customer": {}, "supplier": {}})
        mock_run.return_value = {"creados": 0, "actualizados": 0, "fallidos": []}

        s._run_flow(flow)
        s._load_flow_configs.assert_called_once()
        _, kwargs = mock_run.call_args
        self.assertIsNotNone(kwargs.get("flow_configs") or mock_run.call_args[1].get("flow_configs"))

    @patch("scheduler.runner.run")
    def test_run_flow_maestro_no_carga_flow_configs(self, mock_run):
        s = _build_scheduler()
        flow = {"flow_id": 1, "flow_name": "items", "flow_type": "items"}
        fresh = {"flow_id": 1, "flow_name": "items", "flow_type": "items",
                  "flow_config": {}, "schedule_cron": "0 * * * *", "is_active": True}
        s._reload_flow = MagicMock(return_value=fresh)
        s._load_flow_configs = MagicMock()
        mock_run.return_value = {"creados": 0, "actualizados": 0, "fallidos": []}

        s._run_flow(flow)
        s._load_flow_configs.assert_not_called()

    @patch("scheduler.runner.run")
    def test_run_flow_loguea_resultado(self, mock_run):
        s = _build_scheduler()
        flow = {"flow_id": 1, "flow_name": "items", "flow_type": "items"}
        fresh = {"flow_id": 1, "flow_name": "items", "flow_type": "items",
                  "flow_config": {}, "schedule_cron": None, "is_active": True}
        s._reload_flow = MagicMock(return_value=fresh)
        mock_run.return_value = {"creados": 3, "actualizados": 7, "fallidos": [{"ref": "x"}]}

        s._run_flow(flow)
        s.logger.info.assert_called()
        last_log = s.logger.info.call_args_list[-1][0][0]
        self.assertIn("creados=3", last_log)
        self.assertIn("actualizados=7", last_log)
        self.assertIn("fallidos=1", last_log)

    @patch("scheduler.runner.run")
    def test_run_flow_excepcion_se_propaga(self, mock_run):
        s = _build_scheduler()
        flow = {"flow_id": 1, "flow_name": "items", "flow_type": "items"}
        fresh = {"flow_id": 1, "flow_name": "items", "flow_type": "items",
                  "flow_config": {}, "schedule_cron": None, "is_active": True}
        s._reload_flow = MagicMock(return_value=fresh)
        mock_run.side_effect = RuntimeError("Odoo caído")

        with self.assertRaises(RuntimeError):
            s._run_flow(flow)


@patch.dict("os.environ", {"ENV": "dev", "DATABASE_URL": "postgresql://test"})
class TestRunWithRetry(unittest.TestCase):

    def test_retry_exito_primer_intento(self):
        s = _build_scheduler()
        flow = {"flow_id": 1, "flow_name": "items", "flow_type": "items"}
        s._run_flow = MagicMock(return_value={"creados": 5, "actualizados": 0, "fallidos": []})

        result = s._run_with_retry(flow)
        self.assertEqual(result["creados"], 5)
        self.assertEqual(s._run_flow.call_count, 1)

    @patch("scheduler.runner.time")
    def test_retry_fallo_y_exito_segundo_intento(self, mock_time):
        s = _build_scheduler()
        flow = {"flow_id": 1, "flow_name": "items", "flow_type": "items"}
        s._run_flow = MagicMock(side_effect=[
            RuntimeError("Timeout"),
            {"creados": 5, "actualizados": 0, "fallidos": []}
        ])

        result = s._run_with_retry(flow)
        self.assertEqual(result["creados"], 5)
        self.assertEqual(s._run_flow.call_count, 2)
        mock_time.sleep.assert_called_once_with(30)

    @patch("scheduler.runner.time")
    def test_retry_tres_fallos_aborta(self, mock_time):
        s = _build_scheduler()
        flow = {"flow_id": 1, "flow_name": "items", "flow_type": "items"}
        s._run_flow = MagicMock(side_effect=RuntimeError("Fallo permanente"))

        result = s._run_with_retry(flow)
        self.assertIsNone(result)
        self.assertEqual(s._run_flow.call_count, 3)
        s.logger.error.assert_called()

    @patch("scheduler.runner.time")
    def test_retry_backoff_exponencial(self, mock_time):
        s = _build_scheduler()
        flow = {"flow_id": 1, "flow_name": "items", "flow_type": "items"}
        s._run_flow = MagicMock(side_effect=RuntimeError("Fallo"))

        s._run_with_retry(flow)
        sleep_calls = mock_time.sleep.call_args_list
        self.assertEqual(len(sleep_calls), 2)
        self.assertEqual(sleep_calls[0], call(30))
        self.assertEqual(sleep_calls[1], call(60))

    @patch("scheduler.runner.time")
    def test_retry_loguea_cada_intento(self, mock_time):
        s = _build_scheduler()
        flow = {"flow_id": 1, "flow_name": "items", "flow_type": "items"}
        s._run_flow = MagicMock(side_effect=RuntimeError("Error de red"))

        s._run_with_retry(flow)
        warning_calls = [c[0][0] for c in s.logger.warning.call_args_list]
        self.assertTrue(any("intento 1/3" in w for w in warning_calls))
        self.assertTrue(any("intento 2/3" in w for w in warning_calls))


@patch.dict("os.environ", {"ENV": "dev", "DATABASE_URL": "postgresql://test"})
class TestArranqueOrdenado(unittest.TestCase):

    def test_arranque_ejecuta_solo_los_flows_con_cron(self):
        # _arranque_ordenado filtra por schedule_cron: los flows sin cron son
        # de ejecucion manual y no deben correr al arrancar el contenedor.
        # SAMPLE_FLOWS tiene 5 flows, uno de ellos sin cron.
        flows = [f.copy() for f in SAMPLE_FLOWS]
        s = _build_scheduler(flows=flows)
        s._run_with_retry = MagicMock(return_value=None)

        s._arranque_ordenado()
        self.assertEqual(s._run_with_retry.call_count, 4)

    def test_arranque_omite_el_flow_sin_cron(self):
        flows = [f.copy() for f in SAMPLE_FLOWS]
        s = _build_scheduler(flows=flows)
        ejecutados = []
        s._run_with_retry = MagicMock(side_effect=lambda f: ejecutados.append(f["flow_id"]))

        s._arranque_ordenado()
        self.assertNotIn(3, ejecutados)

    def test_arranque_sin_ningun_cron_no_ejecuta_nada(self):
        flows = [{"flow_id": 9, "flow_name": "manual", "flow_type": "items",
                  "flow_config": {}, "schedule_cron": None}]
        s = _build_scheduler(flows=flows)
        s._run_with_retry = MagicMock()

        s._arranque_ordenado()
        s._run_with_retry.assert_not_called()

    def test_arranque_con_cron_vacio_tambien_se_omite(self):
        flows = [{"flow_id": 9, "flow_name": "manual", "flow_type": "items",
                  "flow_config": {}, "schedule_cron": ""}]
        s = _build_scheduler(flows=flows)
        s._run_with_retry = MagicMock()

        s._arranque_ordenado()
        s._run_with_retry.assert_not_called()

    def test_arranque_respeta_orden(self):
        flows = [f.copy() for f in SAMPLE_FLOWS]
        s = _build_scheduler(flows=flows)
        executed = []
        s._run_with_retry = MagicMock(side_effect=lambda f: executed.append(f["flow_name"]))

        s._arranque_ordenado()
        self.assertEqual(executed[0], "items")
        self.assertEqual(executed[1], "partners")
        self.assertEqual(executed[-1], "ventas")

    def test_arranque_flow_falla_continua_con_siguientes(self):
      # De los 5 flows de SAMPLE_FLOWS solo 4 tienen cron, asi que el
      # arranque los recorre a esos 4 aunque alguno devuelva None.
      flows = [f.copy() for f in SAMPLE_FLOWS]
      s = _build_scheduler(flows=flows)
      s._run_with_retry = MagicMock(side_effect=[
          {"creados": 5, "actualizados": 0, "fallidos": []},
          None,  # este flow "falló" (retry agotado, retornó None)
          {"creados": 0, "actualizados": 3, "fallidos": []},
          None,
      ])

      s._arranque_ordenado()
      self.assertEqual(s._run_with_retry.call_count, 4)

    def test_arranque_loguea_inicio_y_fin(self):
        s = _build_scheduler(flows=[])
        s._run_with_retry = MagicMock()

        s._arranque_ordenado()
        info_calls = [c[0][0] for c in s.logger.info.call_args_list]
        self.assertTrue(any("Arranque ordenado:" in i for i in info_calls))
        self.assertTrue(any("Arranque ordenado completado" in i for i in info_calls))


@patch.dict("os.environ", {"ENV": "dev", "DATABASE_URL": "postgresql://test"})
class TestRegisterFlows(unittest.TestCase):

    def test_register_flow_con_cron(self):
        flows = [{"flow_id": 1, "flow_name": "compras", "flow_type": "purchases",
                  "flow_config": {}, "schedule_cron": "*/2 * * * *"}]
        s = _build_scheduler(flows=flows)

        s._register_flows()
        s.scheduler.add_job.assert_called_once()
        args, kwargs = s.scheduler.add_job.call_args
        self.assertEqual(kwargs["id"], "testclient_compras")

    def test_register_ignora_flow_sin_cron(self):
        flows = [{"flow_id": 3, "flow_name": "partners", "flow_type": "supplier",
                  "flow_config": {}, "schedule_cron": None}]
        s = _build_scheduler(flows=flows)

        s._register_flows()
        s.scheduler.add_job.assert_not_called()

    def test_register_flow_inactivo_se_registra(self):
        flows = [{"flow_id": 1, "flow_name": "items", "flow_type": "items",
                  "flow_config": {}, "schedule_cron": "0 * * * *",
                  "is_active": False}]
        s = _build_scheduler(flows=flows)

        s._register_flows()
        s.scheduler.add_job.assert_called_once()

    def test_register_cron_invalido_loguea_error(self):
        flows = [{"flow_id": 1, "flow_name": "items", "flow_type": "items",
                  "flow_config": {}, "schedule_cron": "invalid_cron"}]
        s = _build_scheduler(flows=flows)
        s.scheduler.add_job.side_effect = ValueError("Invalid cron")

        s._register_flows()
        s.logger.error.assert_called()

    def test_register_loguea_conteo(self):
        flows = [
            {"flow_id": 1, "flow_name": "items", "flow_type": "items",
              "flow_config": {}, "schedule_cron": "0 * * * *"},
            {"flow_id": 3, "flow_name": "partners", "flow_type": "supplier",
              "flow_config": {}, "schedule_cron": None},
        ]
        s = _build_scheduler(flows=flows)

        s._register_flows()
        info_calls = [c[0][0] for c in s.logger.info.call_args_list]
        self.assertTrue(any("1/2 flows registrados" in i for i in info_calls))


@patch.dict("os.environ", {"ENV": "dev", "DATABASE_URL": "postgresql://test"})
class TestStart(unittest.TestCase):

    def test_start_llama_arranque_register_scheduler(self):
        s = _build_scheduler()
        s._arranque_ordenado = MagicMock()
        s._register_flows = MagicMock()
        s.scheduler.start = MagicMock()

        s.start()
        s._arranque_ordenado.assert_called_once()
        s._register_flows.assert_called_once()
        s.scheduler.start.assert_called_once()

    def test_start_arranque_falla_continua_con_register(self):
        s = _build_scheduler()
        s._arranque_ordenado = MagicMock(side_effect=RuntimeError("BD caída"))
        s._register_flows = MagicMock()
        s.scheduler.start = MagicMock()

        s.start()
        s._register_flows.assert_called_once()
        s.scheduler.start.assert_called_once()

    def test_start_keyboard_interrupt_detiene_limpio(self):
        s = _build_scheduler()
        s._arranque_ordenado = MagicMock()
        s._register_flows = MagicMock()
        s.scheduler.start = MagicMock(side_effect=KeyboardInterrupt)

        s.start()
        s.logger.info.assert_called()

    def test_start_error_fatal_loguea_y_relanza(self):
        s = _build_scheduler()
        s._arranque_ordenado = MagicMock()
        s._register_flows = MagicMock()
        s.scheduler.start = MagicMock(side_effect=RuntimeError("Crash"))

        with self.assertRaises(RuntimeError):
            s.start()
        s.logger.critical.assert_called()


if __name__ == "__main__":
    unittest.main()