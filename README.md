# Integrador ERP - WMS
### 360 Software - Medellin, Colombia

Sistema de integracion entre multiples ERPs y Odoo WMS.
Conecta SIESA WS, SIESA Connekta, SAP B1 y Excel (fallback) con Odoo.

---

## Arquitectura

```
ERP (SIESA WS / Connekta / SAP B1)
    | dato crudo
connection/
    | lista de dicts crudos
transform/
    | lista de dicts normalizados (alias canonicos)
core/
    | create() / write() via JSON-RPC
Odoo WMS
```

Cada capa tiene una responsabilidad clara y no conoce los detalles de las demas.

---

## Estructura de carpetas

```
integrador-360/
|
|-- config/
|   |-- loader.py           ConfigLoader — credenciales GCP + fallback local
|   +-- logger.py           IntegradorLogger — print (dev) / archivo rotativo (staging/prod)
|
|-- connection/
|   |-- base.py             ERPConnector (ABC) — contrato get() + test_connection()
|   |-- siesa_enterprise.py SIESA WS via SOAP (zeep) — Fenix, Faizan, Surtinegocios, Papis
|   |-- siesa_connekta.py   SIESA Connekta via REST — Tito Pabon, OIT, R.P. Simon Bolivar
|   |-- sap.py              SAP B1 via OData — BYCSA, Faber Castell
|   |-- excel_connector.py  Fallback Excel — cualquier cliente en emergencia
|   +-- jsonrpc.py          JSON-RPC Odoo — base del core (no hereda ERPConnector)
|
|-- transform/
|   |-- base.py             Transform (ABC) — contrato get_flow()
|   |-- transform_ws.py     TransformWS — pass-through, SQL ya trae alias canonicos
|   |-- transform_connekta.py TransformConnekta — mapping + hardcodes + conditionals
|   |-- transform_sap.py    TransformSAP — prefetch categorias + flatten + mapping
|   +-- utils/
|       |-- helpers.py      parse_fecha, clean_string, to_float, to_int, validate_record
|       +-- determination_functions.py  Catalogo cerrado de 7 funciones de determinacion
|
|-- core/
|   |-- base.py             CoreProcessor (ABC) — contrato process()
|   |-- process_items.py    Productos — bulk fetch + pre-resolver UOM/categoria/tax/route
|   |-- process_partners.py Clientes/proveedores — jerarquia sucursal + ranks
|   |-- process_purchases.py Ordenes de compra — groupby + purchase.order
|   |-- process_sales.py    Pedidos de venta — groupby + sale.order + zonas
|   |-- resolve_missing_masters.py  Orquestacion maestros faltantes (entre maestros y transacciones)
|   +-- utils/
|       +-- lookups.py      9 funciones de lookup con cache (uom, category, tax, route, etc.)
|
|-- db/
|   |-- schema.sql          DDL PostgreSQL — 5 tablas, triggers, indices, datos iniciales
|   +-- writer.py           DBWriter — escritura en executions (pendiente Fase 6)
|
|-- scheduler/
|   +-- runner.py            IntegradorScheduler (pendiente Fase 7)
|
|-- api/
|   +-- app.py               API FastAPI (pendiente Fase 8)
|
|-- frontend/                React + Vite (pendiente Fase 9-10)
|
|-- test/
|   |-- test_loader.py       15 tests
|   |-- test_connection.py   77 tests
|   |-- test_transform.py    140 tests
|   +-- test_core.py         313 tests
|
|-- main.py                  Orquestador del sistema (pendiente Fase 6)
+-- requirements.txt         42 dependencias
```

---

## Patrones de diseno

| Patron | Ubicacion | Descripcion |
|--------|-----------|-------------|
| Strategy | `connection/` y `transform/` | Conectores y transforms intercambiables por ERP |
| Factory | `main.py` | `build_connector()` y `build_transform()` instancian segun `erp_type` |
| Singleton | `connection/sap.py` | SessionId SAP se obtiene una vez y se reutiliza |
| Observer | `scheduler/runner.py` | APScheduler notifica cuando ejecutar |

---

## Clientes activos

| Cliente | ERP | Tipo |
|---------|-----|------|
| Fenix, Faizan, Surtinegocios, Papis | SIESA WS | `ws` |
| Tito Pabon, OIT, R.P. Simon Bolivar | SIESA Connekta | `connekta` |
| BYCSA, Faber Castell | SAP B1 | `sap` |

---

## Base de datos

PostgreSQL 16. 5 tablas:

| Tabla | Proposito |
|-------|-----------|
| `users` | Administradores del front (SSO Google Workspace) |
| `clients` | Empresas clientes (client_id, erp_type) |
| `flows` | Configuracion de flujos (flow_config JSONB, schedule_cron) |
| `executions` | Log de cada ejecucion (status, result, errores) |
| `change_history` | Historico de cambios para rollback |

DDL completo en `db/schema.sql`.

---

## Infraestructura Docker

```
docker-compose.yml
|-- postgres              BD compartida
|-- api                   FastAPI
|-- frontend              React + Vite
+-- integrador-{cliente}  1 contenedor por cliente (misma imagen, distinto CLIENT_ID)
```

Todos los datos persistentes viven en el servidor host via volumenes:

| Que | Ruta en el host |
|-----|-----------------|
| Datos PostgreSQL | `/var/lib/integrador/postgres` |
| Logs | `/var/log/integrador/` |
| GCP key | `/etc/integrador/gcp-key.json` |
| Credenciales fallback | `/etc/integrador/credentials/` |
| Excel fallback | `/etc/integrador/excel/` |

---

## Variables de entorno

| Variable | Descripcion | Ejemplo |
|----------|-------------|---------|
| `ENV` | Entorno de ejecucion | `dev`, `staging`, `prod` |
| `CLIENT_ID` | Slug del cliente (contenedores) | `fenix`, `titopabon` |
| `GCP_PROJECT_ID` | Proyecto de GCP | `hale-treat-398215` |
| `GOOGLE_APPLICATION_CREDENTIALS` | Ruta a la key de GCP | `/etc/integrador/gcp-key.json` |
| `DATABASE_URL` | Conexion a PostgreSQL | `postgresql://integrador:pass@postgres:5432/integrador` |

---

## Tests

```bash
pytest test/
```

| Archivo | Tests | Estado |
|---------|-------|--------|
| `test/test_loader.py` | 15 | Implementado |
| `test/test_connection.py` | 77 | Implementado |
| `test/test_transform.py` | 140 | Implementado |
| `test/test_core.py` | 313 | Implementado |
| `test/test_main.py` | — | Pendiente Fase 6 |
| `test/test_scheduler.py` | — | Pendiente Fase 7 |
| `test/test_api.py` | — | Pendiente Fase 8 |

Total: **545 tests pasando**.

---

## Estado del proyecto

| Fase | Nombre | Estado |
|------|--------|--------|
| 0 | Setup inicial | Completado |
| 1 | Config Layer GCP | Completado |
| 2 | Connection Layer | Completado y validado en servidor |
| 3 | Transform Layer | Completado — 140 tests |
| 4 | Core Layer | Completado — 313 tests, 91+ E2E en servidor |
| 5 | BD + Docker | Completado — schema, servidor GCP, docker-compose |
| 6 | Conexion BD + Main | En desarrollo |
| 7 | Scheduler | Pendiente |
| 8 | API FastAPI | Pendiente |
| 9-10 | Frontend | Pendiente |
| Final | Docker + Deploy | Pendiente |

---

