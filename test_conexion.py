"""
test_conexion.py — Verifica conectividad antes de correr pruebas
Ejecutar en el servidor: python test_conexion.py
"""
import os
os.environ["ENV"] = "staging"

from config.loader import ConfigLoader
from connection.siesa_enterprise import SiesaEnterprise
from connection.jsonrpc import JsonRPC

CLIENT_ID = "pruebaws"

print("=" * 50)
print("  Test de conexion - integrador-pruebaws")
print("=" * 50)

# 1. Cargar config desde GCP
print("\n1. Cargando config desde GCP...")
try:
    config = ConfigLoader(CLIENT_ID).load_config()
    config["client_id"] = CLIENT_ID
    print(f"   ERP tipo:  {config['erp']['tipo']}")
    print(f"   ERP URL:   {config['erp']['url']}")
    print(f"   Odoo URL:  {config['odoo']['url']}")
    print(f"   Odoo DB:   {config['odoo']['database']}")
    print("   [OK] Config cargada")
except Exception as e:
    print(f"   [FAIL] Error cargando config: {e}")
    exit(1)

# 2. Conectar a Odoo
print("\n2. Conectando a Odoo...")
try:
    odoo = JsonRPC(config)
    auth = odoo.authenticate()
    if auth:
        print("   [OK] Odoo autenticado")
    else:
        print("   [FAIL] Odoo no autentico")
        exit(1)
except Exception as e:
    print(f"   [FAIL] Error conectando a Odoo: {e}")
    exit(1)

# 3. Conectar al ERP
print("\n3. Conectando a SIESA WS...")
try:
    connector = SiesaEnterprise(config)
    status, msg = connector.test_connection()
    if status:
        print(f"   [OK] {msg}")
    else:
        print(f"   [FAIL] {msg}")
        exit(1)
except Exception as e:
    print(f"   [FAIL] Error conectando al ERP: {e}")
    exit(1)

print("\n" + "=" * 50)
print("  Todo OK - listo para correr pruebasF4_ws.py")
print("=" * 50)