"""
ConfigLoader — Único punto de acceso a la configuración
Responsabilidades:
  - __init__()            → recibe client_id · detecta entorno desde ENV
  - _load_from_gcp()      → lee credenciales desde GCP Secret Manager
                            guarda credenciales localmente como respaldo
  - _load_from_env()      → fallback manual con SECRET_JSON en .env
  - save_credentials()    → guarda credenciales en sistema de archivos
  - load_credentials()    → carga credenciales desde sistema de archivos
  - credentials_exist()   → verifica si existen credenciales locales
  - load_config()         → Factory · decide la fuente · retorna dict completo
Pendiente fase 6:
  - _load_from_db()       → lee configuración UI desde la BD
  - get_sql()             → trae SQL por nombre desde sql_templates
Patrones: Factory
"""
import os
import json
from dotenv import load_dotenv
from google.cloud import secretmanager
from config.logger import IntegradorLogger

load_dotenv()

class ConfigLoader:
    
    def __init__(self, client_id: str):
        self.client_id  = client_id
        self.env        = os.getenv("ENV", "dev")
        self.project_id = os.getenv("GCP_PROJECT_ID")
        self.credentials_path  = os.getenv("CREDENTIALS_PATH", "/etc/integrador/credentials")
        self.logger     = IntegradorLogger(client_id=client_id)

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