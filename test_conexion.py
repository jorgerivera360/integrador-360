import os
os.environ["ENV"] = "staging"

from config.loader import ConfigLoader
from connection.siesa_enterprise import SiesaEnterprise

config = ConfigLoader("pruebaws").load_config()
config["client_id"] = "pruebaws"
connector = SiesaEnterprise(config)

status, data = connector.get(
    endpoint="EjecutarConsultaXML",
    params={"sql": "SELECT f120_id_cia AS cia, COUNT(*) AS total FROM t120_mc_items GROUP BY f120_id_cia"}
)
print("Status:", status)
for row in data:
    print(f"  CIA {row['cia']}: {row['total']} items")