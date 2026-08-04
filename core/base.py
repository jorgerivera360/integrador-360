"""
  CoreProcessor — Clase base abstracta del core (Strategy)
  Responsabilidades:
    - Contrato único: process(data) → dict
    - Cada subclase implementa la carga a Odoo para su entidad
    - Los lookups compartidos viven en core/utils/lookups.py
    - Las utilidades compartidas viven en core/utils/helpers.py
  Fase: 4 — Core Layer
  """
from abc import ABC, abstractmethod

class CoreProcessor(ABC):

    @abstractmethod
    def process(self, data: list) -> dict:
        """Procesa la lista de registros y retorna resumen de resultado"""
        pass