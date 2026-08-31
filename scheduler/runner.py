"""
IntegradorScheduler — Scheduler del sistema
Responsabilidades:
- __init__()           — carga config GCP, flows BD, inicializa APScheduler
- _reload_flow()       — re-lee un flow de BD (config fresco + is_active)
- _load_flow_configs() — lee flow_configs de maestros para resolve
- _run_flow()          — verifica is_active, ejecuta main.run()
- _run_with_retry()    — backoff exponencial (3 intentos: 30s, 60s, 120s)
- _arranque_ordenado() — ejecuta todos los flows en orden de execution_order
- _register_flows()    — registra crons en APScheduler
- start()              — arranque ordenado → register → loop infinito
Patrones: Observer · BlockingScheduler
Librería: APScheduler · ThreadPoolExecutor
Fase: 7 — Scheduler
"""
import os
import sys
import time
import psycopg2
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.executors.pool import ThreadPoolExecutor

from config.loader import ConfigLoader
from config.logger import IntegradorLogger
from db.writer import DBWriter
from main import run


class IntegradorScheduler:

    def __init__(self, client_id):
        self.client_id = client_id
        self.logger = IntegradorLogger(client_id=client_id)
        self.logger.info(f"Scheduler | Inicializando para cliente '{client_id}'")

        # Config GCP (credenciales ERP + Odoo)
        try:
            loader = ConfigLoader(client_id=client_id)
            self.config = loader.load_config()
            if not self.config:
                raise RuntimeError("Config GCP vacía")
            self.config["client_id"] = client_id
            self.logger.info(f"Scheduler | Config GCP cargada — odoo={self.config['odoo']['url']}")
        except Exception as e:
            self.logger.critical(f"Scheduler | Error cargando config GCP: {e}")
            raise

        # Flows de BD
        try:
            db_config = loader.load_db_config()
            self.erp_type = db_config["erp_type"]
            self.flows = db_config["flows"]
            if not self.erp_type:
                raise RuntimeError(f"Cliente '{client_id}' no encontrado en BD")
            self.logger.info(
                f"Scheduler | BD cargada — erp_type={self.erp_type}, "
                f"{len(self.flows)} flows"
            )
        except Exception as e:
            self.logger.critical(f"Scheduler | Error cargando flows de BD: {e}")
            raise

        # DB Writer
        self.database_url = os.getenv("DATABASE_URL")
        self.db_writer = DBWriter(database_url=self.database_url, logger=self.logger)

        # APScheduler
        self.scheduler = BlockingScheduler(
            executors={"default": ThreadPoolExecutor(max_workers=6)},
            job_defaults={"max_instances": 1, "coalesce": True}
        )

        self.logger.info("Scheduler | Inicialización completa")

    def _reload_flow(self, flow_id):
        """Re-lee un flow de BD para obtener config fresco y is_active actual."""
        try:
            conn = psycopg2.connect(self.database_url)
            cur = conn.cursor()
            cur.execute(
                "SELECT id, flow_name, flow_type, flow_config, schedule_cron, is_active "
                "FROM flows WHERE id = %s",
                (flow_id,)
            )
            row = cur.fetchone()
            cur.close()
            conn.close()

            if not row:
                return None
            return {
                "flow_id": row[0], "flow_name": row[1], "flow_type": row[2],
                "flow_config": row[3], "schedule_cron": row[4], "is_active": row[5]
            }
        except Exception as e:
            self.logger.error(f"Scheduler | Error recargando flow {flow_id}: {e}")
            return None

    def _load_flow_configs(self):
        """Lee flow_configs de maestros activos para resolve de transacciones."""
        try:
            conn = psycopg2.connect(self.database_url)
            cur = conn.cursor()
            cur.execute("""
                SELECT flow_type, flow_config FROM flows
                WHERE client_id = (SELECT id FROM clients WHERE client_id = %s)
                AND flow_type IN ('items', 'customer', 'supplier')
                AND is_active = true
            """, (self.client_id,))
            flow_configs = {}
            for row in cur.fetchall():
                flow_type, flow_config = row
                if flow_type not in flow_configs:
                    flow_configs[flow_type] = []
                flow_configs[flow_type].append(flow_config)
            cur.close()
            conn.close()
            return flow_configs
        except Exception as e:
            self.logger.error(f"Scheduler | Error cargando flow_configs de maestros: {e}")
            return {}

    def _run_flow(self, flow):
        """Recarga flow de BD, verifica is_active, ejecuta main.run().
        Deja propagar excepciones para que _run_with_retry pueda reintentar."""
        flow_id = flow["flow_id"]
        flow_name = flow["flow_name"]

        # Recargar flow fresco de BD
        fresh = self._reload_flow(flow_id)
        if not fresh:
            self.logger.warning(
                f"Scheduler | Flow '{flow_name}' (id={flow_id}) no encontrado en BD — saltando"
            )
            return None

        if not fresh["is_active"]:
            self.logger.info(f"Scheduler | Flow '{fresh['flow_name']}' inactivo — saltando")
            return None

        # flow_configs para resolve (solo transacciones)
        flow_configs = None
        if fresh["flow_type"] in ("purchases", "sales"):
            flow_configs = self._load_flow_configs()

        self.logger.info(
            f"Scheduler | Ejecutando flow '{fresh['flow_name']}' ({fresh['flow_type']})"
        )
        result = run(
            flow=fresh,
            config=self.config,
            erp_type=self.erp_type,
            flow_configs=flow_configs,
            db_writer=self.db_writer,
            triggered_by="scheduler"
        )

        creados = result.get("creados", 0)
        actualizados = result.get("actualizados", 0)
        fallidos = len(result.get("fallidos", []))
        self.logger.info(
            f"Scheduler | Flow '{fresh['flow_name']}' completado: "
            f"creados={creados}, actualizados={actualizados}, fallidos={fallidos}"
        )
        return result

    def _run_with_retry(self, flow):
        """Ejecuta _run_flow con backoff exponencial (3 intentos: 30s, 60s, 120s)."""
        flow_name = flow["flow_name"]
        max_retries = 3
        base_delay = 30

        for intento in range(1, max_retries + 1):
            try:
                return self._run_flow(flow)
            except Exception as e:
                if intento == max_retries:
                    self.logger.error(
                        f"Scheduler | Flow '{flow_name}' falló después de "
                        f"{max_retries} intentos: {e}"
                    )
                    return None
                delay = base_delay * (2 ** (intento - 1))
                self.logger.warning(
                    f"Scheduler | Flow '{flow_name}' falló "
                    f"(intento {intento}/{max_retries}), reintentando en {delay}s: {e}"
                )
                time.sleep(delay)

    def _arranque_ordenado(self):
        """Ejecuta todos los flows en orden de execution_order.
        self.flows ya viene ordenado por execution_order desde load_db_config()."""
        self.logger.info(
            f"Scheduler | Arranque ordenado: {len(self.flows)} flows"
        )

        for flow in self.flows:
            if flow.get("schedule_cron"):
                self._run_with_retry(flow)

        self.logger.info("Scheduler | Arranque ordenado completado")

    def _register_flows(self):
        """Registra flows con schedule_cron en APScheduler.
        Registra todos (incluso inactivos) — _run_flow verifica is_active en cada ejecución.
        Así activar/desactivar desde el front surte efecto sin reiniciar el contenedor."""
        registrados = 0
        for flow in self.flows:
            cron = flow.get("schedule_cron")
            if not cron:
                self.logger.info(
                    f"Scheduler | Flow '{flow['flow_name']}' sin cron — solo manual"
                )
                continue

            try:
                self.scheduler.add_job(
                    self._run_with_retry,
                    CronTrigger.from_crontab(cron),
                    args=[flow],
                    id=f"{self.client_id}_{flow['flow_name']}",
                    name=f"{flow['flow_name']} ({flow['flow_type']})",
                    replace_existing=True
                )
                registrados += 1
                self.logger.info(
                    f"Scheduler | Registrado '{flow['flow_name']}' → cron '{cron}'"
                )
            except Exception as e:
                self.logger.error(
                    f"Scheduler | Error registrando '{flow['flow_name']}': {e}"
                )

        self.logger.info(f"Scheduler | {registrados}/{len(self.flows)} flows registrados")

    def start(self):
        """Arranque ordenado → registrar crons → loop infinito."""
        self.logger.info(f"Scheduler | Iniciando cliente '{self.client_id}'")

        try:
            self._arranque_ordenado()
        except Exception as e:
            self.logger.error(f"Scheduler | Error en arranque ordenado: {e}")

        self._register_flows()

        self.logger.info("Scheduler | Entrando en loop de APScheduler")
        try:
            self.scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            self.logger.info("Scheduler | Detenido por señal del sistema")
        except Exception as e:
            self.logger.critical(f"Scheduler | Error fatal en loop: {e}")
            raise


if __name__ == "__main__":
    client_id = os.getenv("CLIENT_ID")
    if not client_id:
        print("ERROR: Variable CLIENT_ID no definida")
        sys.exit(1)

    scheduler = IntegradorScheduler(client_id)
    scheduler.start()