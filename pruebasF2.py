#!/usr/bin/env python3


import sys
import os
import json
from datetime import datetime


# ---------- helpers de display ----------

def header(titulo):
    print(f"\n{'='*60}")
    print(f"  {titulo}")
    print(f"{'='*60}")

def ok(msg):
    print(f"  [OK]    {msg}")

def err(msg):
    print(f"  [ERROR] {msg}")

def info(msg):
    print(f"  [INFO]  {msg}")

def muestra(data, n=3):
    if not data:
        info("Sin registros")
        return
    info(f"{len(data)} registros totales — mostrando primeros {min(n, len(data))}:")
    for i, row in enumerate(data[:n]):
        linea = json.dumps(row, ensure_ascii=False, default=str)
        print(f"    [{i+1}] {linea[:200]}")


# ---------- GCP ----------

def probar_gcp(client_id):
    header(f"GCP — ConfigLoader  ({client_id})")
    from config.loader import ConfigLoader
    try:
        config = ConfigLoader(client_id).load_config()
        ok(f"Config cargada desde GCP")
        info(f"ERP tipo : {config['erp']['tipo']}")
        info(f"Odoo URL : {config['odoo']['url']}")
        return config
    except Exception as e:
        err(f"Error cargando config: {e}")
        return None


# ---------- SAP ----------

def probar_sap(config):
    header("SAP B1 — connection/sap.py")
    from connection.sap import SAP
    sap = SAP(config)

    status, msg = sap.test_connection()
    (ok if status else err)(f"test_connection(): {msg}")
    if not status:
        return

    info("get('Items') — primeros 3 con ItemCode y ItemName...")
    s, data = sap.get("Items", params={"select": "ItemCode,ItemName", "filter": "Valid eq 'tYES'"})
    (ok if s else err)(f"get(): {len(data) if s else data} {'registros' if s else ''}")
    if s:
        muestra(data)


# ---------- SIESA WS ----------

def probar_ws(config):
    header("SIESA WS — connection/siesa_enterprise.py")
    from connection.siesa_enterprise import SiesaEnterprise
    ws = SiesaEnterprise(config)

    status, msg = ws.test_connection()
    (ok if status else err)(f"test_connection(): {msg}")
    if not status:
        return

    info("get() — SELECT TOP 3 f430_id, f430_rowid FROM t430...")
    s, data = ws.get("", params={"sql": "SELECT TOP 3 f430_id, f430_rowid FROM t430 WITH(NOLOCK)"})
    (ok if s else err)(f"get(): {len(data) if s else data} {'registros' if s else ''}")
    if s:
        muestra(data)


# ---------- SIESA Connekta ----------

# Ajusta estos nombres segun las consultas reales configuradas en Connekta por cliente
CONNEKTA_QUERIES = {
    "oit":     "productosysolucionesquimicas_items_wms",
    "titopab": "items_wms",
}

def probar_connekta(config, client_id):
    header("SIESA Connekta — connection/siesa_connekta.py")
    from connection.siesa_connekta import SiesaConnekta
    ck = SiesaConnekta(config)

    status, msg = ck.test_connection()
    (ok if status else err)(f"test_connection(): {msg}")
    if not status:
        return

    query_desc = CONNEKTA_QUERIES.get(client_id, "items_wms")
    info(f"get() — query_desc='{query_desc}', single_page=True, tam_pag=3...")
    s, data = ck.get("", params={"query_desc": query_desc, "single_page": True, "tam_pag": 3})
    (ok if s else err)(f"get(): {len(data) if s else data} {'registros' if s else ''}")
    if s:
        muestra(data)


# ---------- Excel ----------

def probar_excel(config):
    header("Excel fallback — connection/excel_connector.py")
    import pandas as pd
    from connection.excel_connector import ExcelConnector

    client_id = config["client_id"]
    ruta_base = f"/etc/integrador/excel/{client_id}/"
    ruta_arch = f"{ruta_base}{client_id}-productos.xlsx"

    # Crear archivo de prueba
    info(f"Creando archivo de prueba en {ruta_arch}...")
    try:
        os.makedirs(ruta_base, exist_ok=True)
        df = pd.DataFrame([
            {"referencia": "TEST001", "descripcion": "Producto prueba 1", "precio": "15000"},
            {"referencia": "TEST002", "descripcion": "Producto prueba 2", "precio": None},
            {"referencia": "TEST003", "descripcion": "Producto prueba 3", "precio": "8500"},
        ])
        df.to_excel(ruta_arch, index=False)
        ok("Archivo creado")
    except Exception as e:
        err(f"No se pudo crear el archivo: {e}")
        return

    ec = ExcelConnector(config)

    # Lectura normal
    s, data = ec.get("productos")
    (ok if s else err)(f"get('productos'): {len(data) if s else data} {'registros' if s else ''}")
    if s:
        muestra(data)
        tiene_none = any(v is None for row in data for v in row.values())
        (ok if tiene_none else err)(f"Celda vacia -> None: {'correcto' if tiene_none else 'fallo'}")

    # Error: endpoint invalido
    info("Probando endpoint invalido ('ventas')...")
    s2, msg2 = ec.get("ventas")
    (ok if not s2 else err)(f"Retorno False correcto: {not s2} — '{msg2}'")

    # Error: archivo inexistente
    info("Probando archivo inexistente ('partners')...")
    s3, data3 = ec.get("partners")
    (ok if (s3 and data3 == []) else err)(f"Retorno (True, []) correcto: {s3 and data3 == []}")


# ---------- Errores de config ----------

def probar_errores():
    header("Pruebas de error — config")
    from config.loader import ConfigLoader

    info("Cliente inexistente en GCP ('cliente_fantasma')...")
    try:
        ConfigLoader("cliente_fantasma").load_config()
        err("Debia fallar pero no fallo")
    except Exception as e:
        ok(f"Fallo correctamente: {type(e).__name__} — {e}")


# ---------- Main ----------

CLIENTES = {
    "bycsa":    "sap",      "fabercas":  "sap",
    "fenix":    "ws",       "faizan":    "ws",
    "surtin":   "ws",       "papis":     "ws",
    "oit":      "connekta", "titopab":   "connekta", "rpsimbol": "connekta",
}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("\nUso: python pruebas.py <client_id>")
        print("\nClientes disponibles:")
        for c, t in CLIENTES.items():
            print(f"  {c:<12} ({t})")
        sys.exit(1)

    client_id = sys.argv[1]
    print(f"\n{'='*60}")
    print(f"  Pruebas de integracion — {client_id}")
    print(f"  {datetime.now():%Y-%m-%d %H:%M:%S}  |  ENV={os.getenv('ENV', 'no definido')}")
    print(f"{'='*60}")

    config = probar_gcp(client_id)
    if not config:
        sys.exit(1)

    tipo = config["erp"]["tipo"]

    if tipo == "sap":
        probar_sap(config)
    elif tipo == "ws":
        probar_ws(config)
    elif tipo == "connekta":
        probar_connekta(config, client_id)
    else:
        err(f"Tipo '{tipo}' no tiene prueba implementada en este script")

    probar_excel(config)
    probar_errores()

    print(f"\n{'='*60}")
    print(f"  Fin — {datetime.now():%H:%M:%S}")
    print(f"{'='*60}\n")