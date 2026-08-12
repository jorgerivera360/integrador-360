"""
DBWriter — Escritura de ejecuciones en PostgreSQL
Responsabilidades:
  - start_execution()    → registra inicio de un flow (status='running')
  - finish_execution()   → registra fin de un flow (status, result, error)
  - _get_db_connection() → conexión a PostgreSQL via DATABASE_URL
Regla: si la BD no responde, el flow sigue — solo no registra.
Fase: 6 — Conexión BD + Main
"""
import json
import psycopg2


class DBWriter:

    def __init__(self, database_url: str, logger=None):
        self.database_url = database_url
        self.logger = logger

    def _get_db_connection(self):
        if not self.database_url:
            raise RuntimeError("DATABASE_URL no configurada")
        return psycopg2.connect(self.database_url)

    def start_execution(self, flow_id: int, triggered_by: str = "scheduler", triggered_user: int = None) -> int:
        conn = None
        try:
            conn = self._get_db_connection()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO executions (flow_id, triggered_by, triggered_user)
                VALUES (%s, %s, %s)
                RETURNING id
            """, (flow_id, triggered_by, triggered_user))
            execution_id = cur.fetchone()[0]
            conn.commit()
            cur.close()
            if self.logger:
                self.logger.info(f"Ejecución iniciada: execution_id={execution_id}, flow_id={flow_id}")
            return execution_id
        except Exception as e:
            if self.logger:
                self.logger.error(f"start_execution: no se pudo registrar en BD: {e}")
            return None
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def finish_execution(self, execution_id: int, status: str, result: dict = None, error_message: str = None):
        if execution_id is None:
            return
        conn = None
        try:
            conn = self._get_db_connection()
            cur = conn.cursor()
            cur.execute("""
                UPDATE executions
                SET status = %s, result = %s, error_message = %s, finished_at = NOW()
                WHERE id = %s
            """, (status, json.dumps(result) if result else None, error_message, execution_id))
            conn.commit()
            cur.close()
            if self.logger:
                self.logger.info(f"Ejecución finalizada: execution_id={execution_id}, status={status}")
        except Exception as e:
            if self.logger:
                self.logger.error(f"finish_execution: no se pudo actualizar en BD: {e}")
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass