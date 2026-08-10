import os
os.environ["ENV"] = "staging"

from config.loader import ConfigLoader
from connection.siesa_enterprise import SiesaEnterprise

config = ConfigLoader("pruebaws").load_config()
config["client_id"] = "pruebaws"
connector = SiesaEnterprise(config)

sql = (
    'SET QUOTED_IDENTIFIER OFF;'
    ' SELECT TOP 5'
    ' f120_id AS referencia,'
    ' ISNULL(f120_descripcion, "") AS descripcion,'
    ' ISNULL(TRIM(f120_id_unidad_inventario), "UNID") AS unidad'
    ' FROM t120_mc_items'
    ' WHERE f120_id_cia = 1'
    ' ORDER BY f120_id ASC;'
    ' SET QUOTED_IDENTIFIER ON;'
)

status, data = connector.get(endpoint="EjecutarConsultaXML", params={"sql": sql})
print("Status:", status)
print("Registros:", len(data) if status else data)
if status and data:
    for row in data:
        print(f"  {row}")