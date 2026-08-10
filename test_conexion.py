import os
os.environ["ENV"] = "staging"

from config.loader import ConfigLoader
from connection.siesa_enterprise import SiesaEnterprise

config = ConfigLoader("pruebaws").load_config()
config["client_id"] = "pruebaws"
connector = SiesaEnterprise(config)

# SQL minimo de ventas - solo 2 campos
sql = (
    'SET QUOTED_IDENTIFIER OFF;'
    ' SELECT TOP 1'
    ' t430.f430_consec_docto AS pedido,'
    ' t200.f200_nit AS cliente'
    ' FROM t201_mm_clientes t201'
    ' INNER JOIN t200_mm_terceros t200'
    '     ON t201.f201_rowid_tercero = t200.f200_rowid AND t201.f201_id_cia = t200.f200_id_cia'
    ' INNER JOIN t430_cm_pv_docto t430'
    '     ON t200.f200_id_cia = t430.f430_id_cia AND t200.f200_rowid = t430.f430_rowid_tercero_fact'
    '        AND t201.f201_id_sucursal = t430.f430_id_sucursal_fact'
    ' WHERE t430.f430_id_cia = 1;'
    ' SET QUOTED_IDENTIFIER ON;'
)

status, data = connector.get(endpoint="EjecutarConsultaXML", params={"sql": sql})
print("Status:", status)
print("Data:", data)