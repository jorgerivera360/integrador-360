"""
ConfigLoader — Único punto de acceso a la configuración
Responsabilidades:
- load_config()      → credenciales ERP/Odoo desde GCP (fallback local)
- load_flows()       → flows activos desde la BD
- load_erp_type()    → tipo de ERP del cliente desde la BD
- _load_from_gcp()   → lee credenciales desde GCP Secret Manager
- _get_db_connection() → conexión a PostgreSQL via DATABASE_URL
Patrones: Factory
Fase: 6 — Conexión BD + Main
"""
import os
import json
import psycopg2
from dotenv import load_dotenv
from google.cloud import secretmanager
from config.logger import IntegradorLogger

load_dotenv()

class ConfigLoader:
    
    def __init__(self, client_id: str):
        self.client_id        = client_id
        self.env              = os.getenv("ENV", "dev")
        self.project_id       = os.getenv("GCP_PROJECT_ID")
        self.credentials_path = os.getenv("CREDENTIALS_PATH", "/etc/integrador/credentials")
        self.database_url     = os.getenv("DATABASE_URL")
        self.logger           = IntegradorLogger(client_id=client_id)

    def load_db_config(self) -> dict:
        result = {"erp_type": None, "flows": []}
        conn = None
        try:
            conn = self._get_db_connection()
            cur = conn.cursor()

            # erp_type
            cur.execute("""
                SELECT erp_type FROM clients
                WHERE client_id = %s AND is_active = true
            """, (self.client_id,))
            row = cur.fetchone()
            if row:
                result["erp_type"] = row[0]
                self.logger.info(f"BD: erp_type='{row[0]}' para {self.client_id}")
            else:
                self.logger.error(f"Cliente '{self.client_id}' no encontrado o inactivo en BD")
                cur.close()
                return result

            # flows activos
            cur.execute("""
                SELECT f.id, f.flow_name, f.flow_type, f.flow_config, f.schedule_cron, f.execution_order
                FROM flows f
                JOIN clients c ON f.client_id = c.id
                WHERE c.client_id = %s AND f.is_active = true AND c.is_active = true
                ORDER BY f.execution_order ASC
            """, (self.client_id,))
            columns = ["flow_id", "flow_name", "flow_type", "flow_config", "schedule_cron", "execution_order"]
            result["flows"] = [dict(zip(columns, row)) for row in cur.fetchall()]
            self.logger.info(f"BD: {len(result['flows'])} flows activos para {self.client_id}")

            cur.close()
            return result

        except RuntimeError as e:
            self.logger.error(f"load_db_config: {e}")
            return result
        except psycopg2.Error as e:
            self.logger.error(f"load_db_config: error de BD: {e}")
            return result
        except Exception as e:
            self.logger.error(f"load_db_config: error inesperado: {e}")
            return result
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _get_db_connection(self):
        if not self.database_url:
            self.logger.error("DATABASE_URL no configurada")
            raise RuntimeError("DATABASE_URL no configurada")
        try:
            conn = psycopg2.connect(self.database_url)
            return conn
        except psycopg2.OperationalError as e:
            self.logger.error(f"No se pudo conectar a PostgreSQL: {e}")
            raise

    def _load_from_gcp(self) -> dict:
        try:
            client   = secretmanager.SecretManagerServiceClient()
            name     = f"projects/{self.project_id}/secrets/integrador-{self.client_id}/versions/latest"
            response = client.access_secret_version(request={"name": name})
            payload  = response.payload.data.decode("UTF-8")
            config   = json.loads(payload)
            self.logger.info(f"Secret traído exitosamente desde GCP para {self.client_id}")
            self.save_credentials(config)
            return config
        except Exception as e:
            self.logger.error(f"GCP no disponible: {e}")
            return self.load_credentials()
    
    def save_credentials(self, config: dict):
        os.makedirs(self.credentials_path, exist_ok=True)
        file_path = os.path.join(
            self.credentials_path,
            f"integrador-{self.client_id}.json"
        )
        with open(file_path, "w") as f:
            json.dump(config, f, indent=2)
        self.logger.info(f"Credenciales guardadas localmente en {file_path}")

    def load_credentials(self) -> dict:
        file_path = os.path.join(
            self.credentials_path,
            f"integrador-{self.client_id}.json"
        )
        if not self.credentials_exist():
            self.logger.critical(
                f"GCP no disponible y no se encontraron credenciales locales para integrador-{self.client_id}"
            )
            raise RuntimeError(
                f"GCP no disponible y no se encontraron credenciales locales para integrador-{self.client_id}"
            )
        self.logger.warning(f"Cargando credenciales desde almacenamiento local para {self.client_id}")
        with open(file_path, "r") as f:
            return json.load(f)
        
    def credentials_exist(self) -> bool:
        file_path = os.path.join(
            self.credentials_path,
            f"integrador-{self.client_id}.json"
        )
        return os.path.exists(file_path)
    
    def load_config(self) -> dict:
        return self._load_from_gcp()