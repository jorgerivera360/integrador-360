"""
TransformBase — Clase base abstracta
Patrones: Template Method · Strategy
Fase: 3 — Transform Layer
"""
from abc import ABC, abstractmethod


class TransformError(Exception):
    """El flujo no se pudo obtener del ERP.

    Se lanza cuando la causa es una falla real: el ERP no responde, la
    configuracion esta incompleta, o el login fallo. NO se lanza cuando el
    ERP responde bien pero no tiene registros: ese caso devuelve lista vacia.

    La distincion importa porque main.py marca la ejecucion como 'error' y
    re-lanza, y el scheduler reintenta 3 veces con backoff
    vacia ante una falla hacia que un ERP caido se viera como un dia sin
    movimiento, y ademas se perdia el reintento.
    """


class Transform(ABC):
    @abstractmethod
    def get_flow(self, connector, flow_name: str, flow_type: str, flow_config: dict) -> list:
        """Orquesta el flujo completo: llama al conector, normaliza y retorna
        lista de dicts listos para el core.

        Lista vacia significa que el ERP no tenia registros.
        Lanza TransformError si el flujo no se pudo obtener."""
        pass