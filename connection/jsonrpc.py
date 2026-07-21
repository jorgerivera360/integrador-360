"""
JsonRPC — Base de conexión con Odoo
Responsabilidades:
  - authenticate() — obtiene token de sesión
  - search_read() — consulta registros en Odoo
  - create() — crea registros en Odoo
  - write() — actualiza registros en Odoo
Nota: No hereda ERPConnector — es la base del core
Fase: 2 — Connection Layer
"""

import requests
from config.logger import IntegradorLogger


class JsonRPC:

    def __init__(self, config: dict):
        self.url            = config["odoo"]["url"].rstrip("/")
        self.db       = config["odoo"]["database"]
        self.username = config["odoo"]["usuario"]
        self.password = config["odoo"]["clave"]
        self._session       = requests.Session()
        self._session_id    = None
        self._authenticated = False
        self.logger         = IntegradorLogger(client_id=config["client_id"])

    # ------------------------------------------------------------------
    # Autenticación
    # ------------------------------------------------------------------

    def authenticate(self) -> tuple:
        endpoint = f"{self.url}/web/session/authenticate"
        payload  = {
            "jsonrpc": "2.0",
            "method":  "call",
            "params": {
                "login":    self.username,
                "password": self.password,
                "db":       self.db,
            },
        }
        try:
            response = self._session.post(endpoint, json=payload, timeout=(5, 30))
            response.raise_for_status()
            body = response.json()

            if "error" in body:
                msg = self._extract_odoo_error(body)
                self.logger.error(f"Error en authenticate: {msg}")
                return False, msg

            result              = body.get("result", {})
            self._session_id    = result.get("session_id")
            self._authenticated = True
            self.logger.info(f"Autenticación exitosa en Odoo — db={self.db}")
            return True, f"Autenticado en {self.db}"

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error de red en authenticate: {e}")
            return False, str(e)


    def _call_kw(self, model: str, method: str, args: list, kwargs: dict) -> tuple:
        if not self._authenticated:
            self.logger.error("_call_kw invocado sin sesión activa")
            return False, "No autenticado — llama authenticate() primero"

        endpoint = f"{self.url}/web/dataset/call_kw"
        payload  = {
            "jsonrpc": "2.0",
            "method":  "call",
            "params": {
                "model":  model,
                "method": method,
                "args":   args,
                "kwargs": kwargs,
            },
        }
        try:
            response = self._session.post(endpoint, json=payload, timeout=(5, 30))
            response.raise_for_status()
            body = response.json()

            if "error" in body:
                msg = self._extract_odoo_error(body)
                self.logger.error(f"Error Odoo en {model}.{method}: {msg}")
                return False, msg

            return True, body["result"]

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error de red en {model}.{method}: {e}")
            return False, str(e)

    @staticmethod
    def _extract_odoo_error(body: dict) -> str:
        try:
            error     = body.get("error", {})
            data      = error.get("data", {})
            message   = data.get("message", "")
            arguments = data.get("arguments", [])
            if message:
                return message
            if arguments:
                return str(arguments)
            return str(error)
        except Exception:
            return str(body.get("error", "Error desconocido"))

    # ------------------------------------------------------------------
    # Métodos de lectura
    # ------------------------------------------------------------------

    def search_read(self,model:  str, domain: list | None = None, fields: list | None = None,
                    limit:  int  = 0, offset: int  = 0, order:  str  = "",) -> tuple:
        domain = domain or []
        fields = fields or []
        self.logger.info(f"search_read {model} — domain={domain} limit={limit} offset={offset}")
        return self._call_kw(
            model=model, method="search_read", args=[],
            kwargs={"domain": domain, "fields": fields, "limit": limit, "offset": offset, "order": order},
        )

    def search(self,model:  str, domain: list | None = None, limit:  int  = 0, offset: int  = 0, order:  str  = "",) -> tuple:
        domain = domain or []
        self.logger.info(f"search {model} — domain={domain}")
        return self._call_kw(
            model=model, method="search", args=[],
            kwargs={"domain": domain, "limit": limit, "offset": offset, "order": order},
        )

    def search_count(self, model: str, domain: list | None = None) -> tuple:
        domain = domain or []
        self.logger.info(f"search_count {model} — domain={domain}")
        return self._call_kw(
            model=model, method="search_count", args=[],
            kwargs={"domain": domain},
        )

    def read(self, model: str, ids: list, fields: list | None = None) -> tuple:
        fields = fields or []
        self.logger.info(f"read {model} — ids={ids}")
        return self._call_kw(
            model=model, method="read", args=[ids],
            kwargs={"fields": fields},
        )

    # ------------------------------------------------------------------
    # Métodos de escritura
    # ------------------------------------------------------------------

    def create(self, model: str, fields: dict | None = None) -> tuple:
        fields = fields or {}
        self.logger.info(f"create {model}")
        return self._call_kw(
            model=model, method="create", args=[fields], kwargs={},
        )

    def write(self, model: str, ids: list, fields: dict | None = None) -> tuple:
        fields = fields or {}
        self.logger.info(f"write {model} — ids={ids}")
        return self._call_kw(
            model=model, method="write", args=[ids, fields], kwargs={},
        )

    def unlink(self, model: str, ids: list) -> tuple:
        self.logger.info(f"unlink {model} — ids={ids}")
        return self._call_kw(
            model=model, method="unlink", args=[ids], kwargs={},
        )

    def action(self, model: str, method: str, ids: list, kwargs: dict | None = None) -> tuple:
        kwargs = kwargs or {}
        self.logger.info(f"action {model}.{method} — ids={ids}")
        return self._call_kw(
            model=model, method=method, args=[ids], kwargs=kwargs,
        )


    def test_connection(self) -> tuple:
        ok, msg = self.authenticate()
        if ok:
            return True, f"Conexión exitosa con Odoo — db={self.db}"
        return False, f"No se pudo conectar con Odoo — db={self.db}: {msg}"