# Integrador ERP ↔ WMS
### 360 Software — Medellín, Colombia

Sistema de integración entre múltiples ERPs y Odoo WMS.
Conecta SIESA WS, SIESA Connekta y SAP con Odoo.

---

## Arquitectura

El sistema está organizado en capas. Cada capa tiene una
responsabilidad clara y no conoce los detalles de las demás.

```
ERP (SIESA / SAP / KubApp)
    ↓ dato crudo
connection/
    ↓ lista de dicts crudos
transform/
    ↓ lista de dicts normalizados
core/
    ↓ create() / write() via jsonrpc
Odoo WMS
```

---

## Estructura de carpetas

```
integrador-360/
│
├── main.py
│   Orquestador del sistema. Instancia el conector y el transform
│   correctos según el tipo de ERP, autentica en Odoo, llama
│   get_flow() y despacha al core. Maneja 3 modos de operación
│   según la variable ENV — prod, api o CLI.
│
├── connection/
│   Conectores que hablan el protocolo de cada ERP.
│   Todos heredan ERPConnector y deben implementar get()
│   y test_connection().
│   │
│   ├── base.py
│   │   Clase abstracta ERPConnector. Define el contrato
│   │   que todos los conectores deben cumplir.
│   │   Incluye _paginate() con la lógica de paginación
│   │   compartida por todos.
│   │
│   ├── siesa_enterprise.py
│   │   Conector SIESA WS. Usa SOAP con zeep.
│   │   Clientes: Fénix · Faizan · Surtinegocios · Papis
│   │
│   ├── siesa_connekta.py
│   │   Conector SIESA Connekta. Usa REST/JSON.
│   │   Detecta automáticamente formato Datos vs Table.
│   │   Clientes: Tito Pabón · OIT · R.P. Simón Bolívar
│   │
│   ├── sap.py
│   │   Conector SAP Business One. Usa OData.
│   │   Maneja SessionId con patrón Singleton.
│   │   Clientes: BYCSA · Faber Castell
│   │
│   ├── excel_connector.py
│   │   Conector fallback. Lee archivos xlsx y retorna
│   │   los datos en el mismo formato que siesa_enterprise.
│   │   Clientes: GNL y clientes sin ERP activo
│   │
│   └── jsonrpc.py
│       Base de conexión con Odoo. No hereda ERPConnector.
│       Provee authenticate(), search_read(), create() y write()
│       que heredan todos los archivos del core.
│
├── transform/
│   Normaliza el dato crudo del ERP al formato interno.
│   El core nunca sabe de dónde vienen los datos.
│   │
│   ├── base.py
│   │   Clase abstracta TransformBase. Contiene todos los
│   │   métodos compartidos — _clean_string(), _parse_date(),
│   │   _normalize_uom(), _validate_*(), _apply_field_mapping()
│   │   y _apply_filters(). Define get_flow() como abstracto.
│   │
│   ├── transform_ws.py
│   │   Transform SIESA WS. Construye el SQL interpolando
│   │   sql_params y siesa_mapping desde client_config.
│   │   Clientes: Fénix · Faizan · Surtinegocios · Papis
│   │
│   ├── transform_connekta.py
│   │   Transform SIESA Connekta. Organiza los parámetros
│   │   de la consulta. No construye SQL.
│   │   Clientes: Tito Pabón · OIT · R.P. Simón Bolívar
│   │
│   └── transform_sap.py
│       Transform SAP B1. Traduce códigos de categoría,
│       construye nombres de documento y filtra almacenes.
│       Clientes: BYCSA · Faber Castell
│
├── core/
│   Escribe los datos normalizados en Odoo.
│   Hace lookups en lote, anti-duplicado y upsert.
│   │
│   ├── base.py
│   │   Clase ProcessBase. Hereda JsonRPC. Contiene los
│   │   lookups en lote comunes — UOMs, impuestos,
│   │   departamentos y países.
│   │
│   ├── process_partners.py
│   │   Carga clientes y proveedores en res.partner.
│   │   Anti-duplicado por vat + sucursal.
│   │
│   ├── process_items.py
│   │   Carga productos en product.template.
│   │   Anti-duplicado por default_code.
│   │   tracking solo se escribe en create — nunca en write.
│   │
│   ├── process_purchases.py
│   │   Carga órdenes de compra en purchase.order.
│   │   Agrupa líneas por documento.
│   │   Anti-duplicado por name.
│   │
│   └── process_sales.py
│       Carga pedidos de venta en sale.order y stock.picking.
│       7 métodos según el tipo de movimiento.
│       Anti-duplicado por name.
│
├── scheduler/
│   │
│   └── runner.py
│       IntegradorScheduler. Arranca los maestros primero
│       en secuencia, registra los flujos en APScheduler
│       con triggers de interval y cron, y envuelve run()
│       con backoff exponencial — 60s, 120s, 240s.
│
├── config/
│   │
│   ├── loader.py
│   │   ConfigLoader. Único punto de acceso a la configuración.
│   │   Lee credenciales desde GCP Secret Manager. Si GCP falla
│   │   carga desde credenciales locales. En fase 6 también
│   │   leerá configuración UI desde la BD.
│   │
│   └── logger.py
│       IntegradorLogger. Maneja los logs del sistema.
│       En dev imprime en consola. En staging y prod
│       escribe en archivo con rotación automática.
│
├── db/
│   │
│   ├── schema.sql
│   │   Definición completa de las 9 tablas — clients, users,
│   │   user_permissions, client_config, sql_templates,
│   │   scheduler_state, flow_execution_logs, flow_record_errors,
│   │   client_notes y client_attachments.
│   │
│   └── logger.py
│       DBLogger. Escribe logs en la BD — log_flow_execution(),
│       log_record_error(), get_scheduler_state() y
│       set_scheduler_state(). Separado de ConfigLoader
│       por responsabilidad única.
│
├── api/
│   │
│   └── app.py
│       API REST con FastAPI. Expone todos los endpoints
│       que consume el frontend — configuración, ejecución,
│       monitoreo, usuarios, notas y adjuntos.
│       Autenticación SSO con Google Workspace.
│
├── frontend/
│   Panel web construido en React + Vite.
│   Consume la API de FastAPI.
│   │
│   └── src/
│       ├── components/     Componentes reutilizables —
│       │                   FlagToggle, LogsTable, SqlEditor,
│       │                   ClientCard, DataTable, Modal
│       │
│       ├── pages/          Secciones del panel —
│       │                   Dashboard, Clients, Flows, Flags,
│       │                   Mappings, SQLs, Logs, Connection,
│       │                   UOM, Notes, Attachments
│       │
│       ├── services/       Llamadas a la API —
│       │                   api.js, clients.js, config.js,
│       │                   flows.js, logs.js, users.js
│       │
│       ├── context/        Estado global —
│       │                   AppContext — cliente activo,
│       │                   usuario, sesión
│       │
│       └── App.jsx         Router principal con rutas
│                           protegidas por autenticación
│
├── tests/
│   Pruebas unitarias por capa.
│   │
│   ├── test_loader.py      Pruebas de config/loader.py
│   ├── test_connection.py  Pruebas de los conectores
│   ├── test_transform.py   Pruebas de los transforms
│   ├── test_core.py        Pruebas de los procesos del core
│   ├── test_main.py        Pruebas de main.py
│   ├── test_scheduler.py   Pruebas del scheduler
│   └── test_api.py         Pruebas de los endpoints
│
├── docs/
│   │
│   ├── instalacion.md      Pasos para instalar en servidor nuevo
│   ├── arquitectura.md     Descripción de capas y patrones
│   └── clientes.md         Cómo agregar un cliente nuevo
│
├── .env.example            Variables de entorno sin valores reales
├── .gitignore              Python · .env · credenciales · node_modules
├── requirements.txt        Dependencias Python del proyecto
└── README.md               Este archivo
```

---

## Patrones de diseño utilizados

```
Strategy        → connection/ y transform/
                  todos los conectores y transforms
                  son intercambiables

Factory         → main.py y config/loader.py
                  build_connector() y build_transform()
                  deciden qué instanciar según el tipo de ERP

Template Method → connection/base.py y transform/base.py
                  lógica compartida en la base
                  detalles específicos en cada subclase

Singleton       → connection/sap.py
                  el SessionId se obtiene una vez
                  y se reutiliza en toda la ejecución

Observer        → scheduler/runner.py
                  APScheduler observa el tiempo
                  y notifica cuando toca ejecutar
```

---

## Variables de entorno

Copia `.env.example` a `.env` y completa los valores:

```bash
cp .env.example .env
```

```
ENV=staging                                    # dev | staging | prod
CLIENT_ID=fenix                                # cliente a ejecutar
GCP_PROJECT_ID=hale-treat-398215               # proyecto de GCP
GOOGLE_APPLICATION_CREDENTIALS=ruta/gcp-key.json
LOG_PATH=/var/log/integrador                   # ruta de los logs
```

---

## Ubicación de archivos en el servidor

```
Proyecto:      /app/integrador-360/
Credenciales:  /etc/integrador/credentials/integrador-{client_id}.json
Logs:          /var/log/integrador/integrador-{client_id}.log
GCP key:       /etc/integrador/gcp-key.json
Entorno:       /app/integrador-360/.env
```

---

## Comportamiento por entorno

```
ENV=dev      → logs en consola con print()
ENV=staging  → logs en archivo
ENV=prod     → logs en archivo
```

---

## Fase 1 — Config Layer GCP ✅

### Qué se construyó

Clase `ConfigLoader` en `config/loader.py` — único punto de
acceso a la configuración en todo el sistema. Clase
`IntegradorLogger` en `config/logger.py` — manejo de logs
por entorno.

### Qué hace ConfigLoader

```
1. Recibe el client_id
2. Se conecta a GCP Secret Manager
3. Trae el secret integrador-{client_id}
4. Guarda las credenciales localmente como respaldo
5. Si GCP falla carga desde el respaldo local
6. Retorna el dict completo de configuración
```

### Métodos de ConfigLoader

```
__init__()           → recibe client_id · detecta ENV
_load_from_gcp()     → trae de GCP · guarda respaldo local
save_credentials()   → guarda JSON en sistema de archivos
load_credentials()   → carga JSON desde sistema de archivos
credentials_exist()  → verifica si existe el respaldo local
load_config()        → punto de entrada único
```

### Pendiente fase 6

```
_load_from_db()  → leerá configuración UI desde la BD
get_sql()        → traerá SQLs desde sql_templates
```

### Cómo usar

```python
from config.loader import ConfigLoader

loader = ConfigLoader(client_id='fenix')
config = loader.load_config()

# config["erp"]["tipo"]      → ws | connekta | sap | kubapp
# config["erp"]["url"]       → URL del ERP
# config["erp"]["usuario"]   → usuario del ERP
# config["erp"]["clave"]     → clave del ERP
# config["odoo"]["url"]      → URL de Odoo
# config["odoo"]["database"] → base de datos de Odoo
# config["odoo"]["usuario"]  → usuario de Odoo
# config["odoo"]["clave"]    → clave de Odoo
```

---

## Equipo

```
Jorge         — Desarrollador
Simón         — Desarrollador
Danilo        — Desarrollador
```

---

## Estado del proyecto

```
Fase 0  — Setup inicial          ✅ Completado
Fase 1  — Config Layer GCP       ✅ Completado - Faltan pruebas unitarias
Fase 2  — Connection Layer       ⬜ Pendiente
Fase 3  — Transform Layer        ⬜ Pendiente
Fase 4  — Core Layer             ⬜ Pendiente
Fase 5  — BD del integrador      ⬜ Pendiente
Fase 6  — Config Layer BD        ⬜ Pendiente
Fase 7  — Main                   ⬜ Pendiente
Fase 8  — Scheduler              ⬜ Pendiente
Fase 9  — API                    ⬜ Pendiente
Fase 10 — Frontend               ⬜ Pendiente
Fase 11 — End-to-end             ⬜ Pendiente
```