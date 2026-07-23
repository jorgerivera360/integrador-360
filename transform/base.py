"""
TransformBase — Clase base abstracta
Patrones: Template Method · Strategy
Fase: 3 — Transform Layer
"""
from abc import ABC, abstractmethod

class Transform(ABC):
    @abstractmethod
    def get_flow(self, connector, flow_name: str, flow_config: dict) -> list:
        """Orquesta el flujo completo: llama al conector, normaliza y retorna lista de dicts listos para el core"""
        pass
