"""
check_cia.py — Averigua el id_cia de OrgComercia
"""
import os
os.environ["ENV"] = "staging"

from config.loader import ConfigLoader
from connection.siesa_enterprise import SiesaEnterprise

config = ConfigLoader("pruebaws").load_config()
config["client_id"] = "pruebaws"
connector = SiesaEnterprise(config)

status, data = connector.get(
    endpoint="EjecutarConsultaXML",
    params={"sql": "SELECT DISTINCT f120_id_cia AS cia FROM t120_mc_items"}
)
print("Status:", status)
print("CIAs encontradas:", data)