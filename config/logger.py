import os
import logging
from logging.handlers import RotatingFileHandler


def _setup_file_logger(client_id: str) -> logging.Logger:
    log_path = os.getenv("LOG_PATH", "/var/log/integrador")
    os.makedirs(log_path, exist_ok=True)

    log_file  = os.path.join(log_path, f"integrador-{client_id}.log")
    logger    = logging.getLogger(f"integrador.{client_id}")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        handler = RotatingFileHandler(
            log_file,
            maxBytes=10_000_000,
            backupCount=5
        )
        formatter = logging.Formatter(
            "%(asctime)s — %(name)s — %(levelname)s — %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


class IntegradorLogger:

    def __init__(self, client_id: str):
        self.client_id = client_id
        self.env       = os.getenv("ENV", "dev")
        self._logger   = None

        if self.env in ("staging", "prod"):
            self._logger = _setup_file_logger(client_id)

    def info(self, mensaje: str):
        if self.env == "dev":
            print(f"[INFO]  [{self.client_id}] {mensaje}")
        else:
            self._logger.info(mensaje)

    def warning(self, mensaje: str):
        if self.env == "dev":
            print(f"[WARN]  [{self.client_id}] {mensaje}")
        else:
            self._logger.warning(mensaje)

    def error(self, mensaje: str):
        if self.env == "dev":
            print(f"[ERROR] [{self.client_id}] {mensaje}")
        else:
            self._logger.error(mensaje)

    def critical(self, mensaje: str):
        if self.env == "dev":
            print(f"[CRIT]  [{self.client_id}] {mensaje}")
        else:
            self._logger.critical(mensaje)