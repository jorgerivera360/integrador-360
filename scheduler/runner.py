"""
IntegradorScheduler — Scheduler del sistema
Responsabilidades:
- __init__()             — carga config GCP, flows BD, inicializa APScheduler
- _reload_flow()         — re-lee un flow de BD (config fresco + is_active)
- _load_flow_configs()   — lee flow_configs de maestros para resolve
- _run_flow()            — verifica is_active, ejecuta main.run()
- _run_with_retry()      — backoff exponencial (3 intentos: 30s, 60s, 120s)
- _arranque_ordenado()   — ejecuta los flows con cron (opt-in: ARRANQUE_ORDENADO=true)
- _job_id()              — id estable de job, por flow_id
- _read_flows_for_sync() — lee todos los flows del cliente (None si falla la BD)
- _sync_flows()          — reconcilia jobs de APScheduler contra la BD
- _register_flows()      — registro inicial, delega en _sync_flows()
- start()                — register → sync periódico → loop (arranque ordenado opt-in)
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
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.executors.pool import ThreadPoolExecutor

from config.loader import ConfigLoader
from config.logger import IntegradorLogger
from db.writer import DBWriter
from main import run


class IntegradorScheduler:

    SYNC_JOB_ID = "__sync_flows__"

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

        # Sync de flows: {job_id: (cron, flow_name)}
        self._job_state = {}
        self.sync_seconds = int(os.getenv("FLOW_SYNC_SECONDS", "60"))

        # Arranque ordenado: apagado por defecto. Reiniciar un contenedor
        # no debe disparar integraciones — de eso se encarga el cron.
        self.arranque_ordenado = os.getenv("ARRANQUE_ORDENADO", "false").lower() == "true"

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
        """Ejecuta todos los flows en secuencia."""
        self.logger.info(
            f"Scheduler | Arranque ordenado: {len(self.flows)} flows"
        )

        for flow in self.flows:
            if flow.get("schedule_cron"):
                self._run_with_retry(flow)

        self.logger.info("Scheduler | Arranque ordenado completado")

    def _job_id(self, flow_id):
        """Id estable de job. Va por flow_id, no por flow_name:
        flow_name es etiqueta libre y renombrable desde el front."""
        return f"{self.client_id}_flow_{flow_id}"

    def _read_flows_for_sync(self):
        """Lee TODOS los flows del cliente, activos e inactivos.
        Devuelve None si la consulta falló — nunca lista vacía por error,
        porque una lista vacía significa 'dar de baja todos los jobs'."""
        conn = None
        try:
            conn = psycopg2.connect(self.database_url)
            cur = conn.cursor()
            cur.execute("""
                SELECT f.id, f.flow_name, f.flow_type, f.flow_config,
                       f.schedule_cron, f.is_active
                FROM flows f
                JOIN clients c ON f.client_id = c.id
                WHERE c.client_id = %s AND c.is_active = true
            """, (self.client_id,))
            columns = ["flow_id", "flow_name", "flow_type", "flow_config",
                       "schedule_cron", "is_active"]
            flows = [dict(zip(columns, row)) for row in cur.fetchall()]
            cur.close()
            return flows
        except Exception as e:
            self.logger.error(f"Scheduler | Sync: error leyendo flows: {e}")
            return None
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _sync_flows(self):
        """Reconcilia los jobs de APScheduler contra la BD.
        Alta, baja, renombrado y cambio de cron surten efecto sin reiniciar."""
        flows = self._read_flows_for_sync()
        if flows is None:
            return

        deseados = {
            self._job_id(f["flow_id"]): f
            for f in flows if f.get("schedule_cron")
        }
        actuales = {
            job.id for job in self.scheduler.get_jobs()
            if job.id != self.SYNC_JOB_ID
        }

        for job_id in actuales - set(deseados):
            try:
                self.scheduler.remove_job(job_id)
                self._job_state.pop(job_id, None)
                self.logger.info(f"Scheduler | Sync: job '{job_id}' dado de baja")
            except Exception as e:
                self.logger.error(f"Scheduler | Sync: error eliminando '{job_id}': {e}")

        for job_id, flow in deseados.items():
            estado = (flow["schedule_cron"], flow["flow_name"])
            if self._job_state.get(job_id) == estado:
                continue
            accion = "actualizado" if job_id in actuales else "registrado"
            try:
                self.scheduler.add_job(
                    self._run_with_retry,
                    CronTrigger.from_crontab(flow["schedule_cron"]),
                    args=[flow],
                    id=job_id,
                    name=f"{flow['flow_name']} ({flow['flow_type']})",
                    replace_existing=True
                )
                self._job_state[job_id] = estado
                self.logger.info(
                    f"Scheduler | Sync: '{flow['flow_name']}' {accion} "
                    f"→ cron '{flow['schedule_cron']}'"
                )
            except Exception as e:
                self._job_state[job_id] = estado
                self.logger.error(
                    f"Scheduler | Sync: error registrando '{flow['flow_name']}': {e}"
                )

    def _register_flows(self):
        """Registro inicial. Delega en _sync_flows para no duplicar la lógica."""
        self._sync_flows()

    def start(self):
        """Registrar crons → sync periódico → loop infinito.
        El arranque ordenado solo corre si ARRANQUE_ORDENADO=true."""
        self.logger.info(f"Scheduler | Iniciando cliente '{self.client_id}'")

        if self.arranque_ordenado:
            self.logger.info("Scheduler | Arranque ordenado ACTIVADO por ARRANQUE_ORDENADO")
            try:
                self._arranque_ordenado()
            except Exception as e:
                self.logger.error(f"Scheduler | Error en arranque ordenado: {e}")
        else:
            self.logger.info(
                "Scheduler | Arranque ordenado desactivado — los flows corren solo por cron"
            )

        self._register_flows()

        self.scheduler.add_job(
            self._sync_flows,
            IntervalTrigger(seconds=self.sync_seconds),
            id=self.SYNC_JOB_ID,
            name="Sync de flows desde BD",
            replace_existing=True
        )
        self.logger.info(
            f"Scheduler | Sync de flows cada {self.sync_seconds}s"
        )

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