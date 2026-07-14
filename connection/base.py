"""
ERPConnector — Clase base abstracta
Responsabilidades:
  - Define el contrato que todos los conectores deben cumplir
  - get() — método abstracto — trae datos del ERP
  - test_connection() — método abstracto — prueba la conexión
Patrones: Strategy · Template Method
Fase: 2 — Connection Layer
"""
from abc import ABC, abstractmethod

class ERPConnector(ABC):
    
    @abstractmethod
    def get(self, endpoint:str, params: dict ={}) -> tuple:
        """Trae datos del ERP, retorna tupla (status: bool, data: list)
            status: True si fue exitoso
            data  : Lista de dicts con los datos crudos
        """
        pass
    
    @abstractmethod
    def test_conntection(self) -> tuple:
        """Prueba la conexión al ERP, retorna tupla (status: boo, mensaje: str)
           status: True si la conexión fue exitosa
           mensaje: Descripción del resultado"""
        pass