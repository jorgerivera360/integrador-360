"""
ExcelConnector — Conector fallback Excel
Responsabilidades:
  - Lee archivos xlsx desde la ruta configurada
  - Retorna datos en el mismo formato que SiesaEnterprise
  - Implementa get() y test_connection()
Hereda: ERPConnector
Fase: 2 — Connection Layer
"""

import os
import pandas as pd
from config.logger import IntegradorLogger
from connection.base import ERPConnector

class ExcelConnector(ERPConnector):
    
    ARCHIVOS_VALIDOS = [
        "productos",
        "partners",
        "entradas",
        "salidas"
    ]

    def __init__(self, config: dict):
        self.client_id = config["client_id"]
        self.ruta_base = f"/etc/integrador/excel/{self.client_id}/"
        self.logger    = IntegradorLogger(client_id=self.client_id)

    def _get_ruta_archivo(self, proceso: str) -> str:
        return os.path.join(
            self.ruta_base,
            f"{self.client_id}-{proceso}.xlsx"
        )
    
    def get(self, endpoint: str, params: dict = {}) -> tuple:
        if endpoint not in self.ARCHIVOS_VALIDOS:
            self.logger.error(f"Proceso '{endpoint}' no es válido para ExcelConnector — válidos: {self.ARCHIVOS_VALIDOS}")
            return False, f"Proceso '{endpoint}' no válido"
        
        ruta = self._get_ruta_archivo(endpoint)

        if not os.path.exists(ruta):
            self.logger.warning(f"Archivo no encontrado — {ruta} — retornando lista vacía")
            return True, []
        
        try:
            df   = pd.read_excel(ruta, header=0, dtype=str)
            records = df.to_dict(orient="records")
            data    = [{k: (None if pd.isnull(v) else v) for k, v in row.items()} for row in records]
            self.logger.info(f"Excel '{endpoint}' leído correctamente — {len(data)} registros")
            return True, data
        except Exception as e:
            self.logger.error(f"Error al leer {ruta}: {e}")
            return False, str(e)
        
    def test_connection(self) -> tuple:
        archivos_encontrados = []
        archivos_faltantes   = []

        for proceso in self.ARCHIVOS_VALIDOS:
            ruta = self._get_ruta_archivo(proceso)
            if os.path.exists(ruta):
                archivos_encontrados.append(proceso)
            else:
                archivos_faltantes.append(proceso)

        if not archivos_encontrados:
            self.logger.warning(f"No se encontró ningún archivo Excel para {self.client_id} en {self.ruta_base}")
            return False, f"No se encontró ningún archivo Excel en {self.ruta_base}"

        self.logger.info(f"Archivos encontrados: {archivos_encontrados} — faltantes: {archivos_faltantes}")
        return True, f"Archivos disponibles: {archivos_encontrados}"
    