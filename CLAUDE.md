# integrador-360 — Contexto técnico del proyecto

## Equipo y roles

| Persona | Rol | Carga |
|---------|-----|-------|
| Jorge Rivera | Tech Lead | 65 % |
| Simón | Desarrollador | 20 % |
| Danilo | Desarrollador | 15 % |

## Identidades del sistema

- **GCP Project ID:** `hale-treat-398215`
- **GitHub repo:** `jorgerivera360/integrador-360`
- **GCP Service Account:** `integrador-service-account` (rol: Secret Manager Secret Accessor)
- **GCP key en servidores:** `/etc/integrador/gcp-key.json`
- **Servidor de pruebas:** `wms-servertest`

## Clientes activos

Fénix, Faizan, Surtinegocios, Papis, Tito Pabón, OIT, R.P. Simón Bolívar, BYCSA, Faber Castell.

## ERPs conectados → Odoo WMS

SIESA WS · SIESA Connekta · SAP B1 · KubApp · Excel (fallback de emergencia)

---

## Arquitectura en capas

```
ERP
 └─ connection/      (Strategy + Template Method)
     └─ transform/   (Strategy + Template Method)
         └─ core/
             └─ Odoo WMS

Config Layer (GCP + BD)  ──┐
Scheduler (APScheduler)  ──┴─→ alimenta todas las capas
```

### Patrones de diseño establecidos

| Patrón | Ubicación | Descripción |
|--------|-----------|-------------|
| Strategy + Template Method | `connection/` y `transform/` | Conectores intercambiables |
| Factory | `main.py` y `config/loader.py` | Decide qué instanciar según tipo de ERP |
| Singleton | `connection/sap.py` | SessionId SAP se obtiene una vez |
| Observer | `scheduler/runner.py` | APScheduler notifica cuando ejecutar |

## Stack tecnológico

- **Backend:** FastAPI
- **Scheduler:** APScheduler
- **Frontend:** React + Vite
- **Testing:** pytest
- **Credenciales:** GCP Secret Manager
- **SOAP:** zeep
- **HTTP:** `requests.Session()`
- **Logs:** archivo rotativo (staging/prod), `print()` (dev)

---

## Plan de fases (11 fases, ~55 días hábiles / 2.5 meses)

Cada fase acumula el código de la anterior (las ramas se crean desde `develop`).

---

## Fase 1 — Config Layer GCP ✅

### `config/logger.py` — `IntegradorLogger`

- **Dev:** usa `print()`
- **Staging/Prod:** `RotatingFileHandler` → `/var/log/integrador/`, 10 MB máx, 5 backups
- Variable de entorno `ENV` controla el modo

### `config/loader.py` — `ConfigLoader`

Métodos: `__init__()`, `_load_from_gcp()`, `save_credentials()`, `load_credentials()`, `credentials_exist()`, `load_config()`

**Decisión arquitectónica clave:** las credenciales se guardan localmente en  
`/etc/integrador/credentials/integrador-{client_id}.json`  
como fallback cuando GCP no está disponible.  
El método `_load_from_env()` fue **descartado** — GCP ya maneja el fallback internamente.

### Convención de secrets GCP

```
Nombre en GCP: integrador-{client_id}
```

**Estructura real validada (ejemplo tipo `ws`):**

```json
{
  "client_id": "fenix",
  "erp": {
    "tipo":       "ws",
    "url":        "http://...",
    "compania":   "1",
    "usuario":    "...",
    "clave":      "...",
    "conexion":   "...",
    "proveedor":  "BEXCONNECT",
    "proxy_host": null,
    "proxy_port": null
  },
  "odoo": {
    "url":      "https://fenix.360software.com.co",
    "database": "fenix",
    "usuario":  "integracion@360software.com.co",
    "clave":    "..."
  }
}
```

> **Crítico:** las llaves del dict `odoo` son `database`, `usuario`, `clave` — **no** `db`, `username`, `password`.  
> Para Connekta, `erp` usa: `url`, `urlqa`, `idcompania`, `connikey`, `connitoken`.  
> El `idcompania` se agrega en runtime como query param: `?idCompania={id}&descripcion={query_desc}`.

### Tipos de ERP en el campo `erp.tipo`

| Tipo | Conector | Clientes |
|------|----------|----------|
| `"ws"` | `SiesaEnterprise` | Fénix, Faizan, Surtinegocios, Papis |
| `"connekta"` | `SiesaConnekta` | Tito Pabón, OIT, R.P. Simón Bolívar |
| `"sap"` | `SAP` | BYCSA, Faber Castell |
| `"kubapp"` | (pendiente) | Autovenz |

### Entorno y systemd

- En producción, **systemd inyecta todas las variables de entorno** → no se necesitan archivos `.env`
- `load_dotenv()` **no sobreescribe** variables ya definidas por systemd

---

## Fase 2 — Connection Layer ✅ — Validada en servidor

| Archivo | Estado |
|---------|--------|
| `connection/base.py` | ✅ `ERPConnector` abstracta completa |
| `connection/sap.py` | ✅ SAP B1 completo |
| `connection/siesa_enterprise.py` | ✅ SIESA WS completo |
| `connection/excel_connector.py` | ✅ Fallback Excel completo |
| `connection/siesa_connekta.py` | ✅ Implementado completo |
| `connection/jsonrpc.py` | ✅ Implementado completo |

### Validación en `wms-servertest` (rama `develop`, ENV=staging)

Script de prueba: `pruebasF2.py`

| Cliente | ERP | Resultado |
|---------|-----|-----------|
| fenix | SIESA WS | ✅ Conectado — `SELECT 1 AS test` exitoso |
| fabercastell | SAP B1 | ✅ Conectado — 4554 registros reales |
| oit | SIESA Connekta | ✅ Conectado — productos reales |
| bycsa | SAP B1 | ⚠️ Timeout de red — no es error de código |
| todos | Excel fallback | ✅ Lectura, NaN→None, errores correctos |

### Fixes aplicados durante validación (en rama `develop`)

**`siesa_enterprise.py` — serialize_object + SELECT universal:**
```python
from zeep import Client, helpers   # helpers es el import adicional

# En get(), después de EjecutarConsultaXML():
result = client.service.EjecutarConsultaXML(xml)
result = helpers.serialize_object(result, target_cls=dict)  # convierte CompoundValue → dict
datos  = result['_value_1']['_value_1']

# test_connection() — SELECT 1 universal (no depende de tablas del cliente):
def test_connection(self) -> tuple:
    status, data = self.get(endpoint="EjecutarConsultaXML", params={"sql": "SELECT 1 AS test"})
    if status:
        return True, f"Conexión exitosa con SIESA WS — {self.conexion}"
    return False, f"No se pudo conectar con SIESA WS — {self.conexion}: {data}"
```

**`sap.py` — timeout en login:**
```python
response = requests.post(url, headers=headers, data=payload, verify=False, timeout=30)
```

**`excel_connector.py` — lectura robusta:**
```python
df      = pd.read_excel(ruta, header=0, dtype=str)
records = df.to_dict(orient="records")
data    = [{k: (None if pd.isnull(v) else v) for k, v in row.items()} for row in records]
```

---

### `connection/base.py` — `ERPConnector` (clase abstracta)

```python
from abc import ABC, abstractmethod

class ERPConnector(ABC):

    @abstractmethod
    def get(self, endpoint: str, params: dict = {}) -> tuple:
        """Retorna (status: bool, data: list | str)"""
        pass

    @abstractmethod
    def test_connection(self) -> tuple:
        """Retorna (status: bool, mensaje: str)"""
        pass
```

---

### `connection/sap.py` — SAP B1 ✅

- Patrón: Strategy + Singleton (`session_id`)
- `verify=False` — SAP B1 usa SSL autofirmado

**Constructor:**
```python
def __init__(self, config: dict):
    self.url        = config["erp"]["url"]
    self.compania   = config["erp"]["compania"]
    self.usuario    = config["erp"]["usuario"]
    self.clave      = config["erp"]["clave"]
    self.session_id = None
    self.logger     = IntegradorLogger(client_id=config["client_id"])
```

| Método | Descripción |
|--------|-------------|
| `login_api()` | POST `/b1s/v1/Login` — guarda `SessionId`; `timeout=30` |
| `_get_headers()` | `{"SessionId": ..., "Cookie": "B1SESSION=..."}` |
| `get(endpoint, params)` | Paginación OData con `$skip` y `odata.nextLink`; acepta `filter` y `select` |
| `test_connection()` | Llama `login_api()` |

---

### `connection/siesa_enterprise.py` — SIESA WS ✅

- Patrón: Strategy
- Protocolo: SOAP via **zeep**
- Timeout: 600 s (consultas pesadas de inventario)

**Constructor:**
```python
def __init__(self, config: dict):
    self.url        = config["erp"]["url"]
    self.conexion   = config["erp"]["conexion"]
    self.compania   = config["erp"]["compania"]
    self.usuario    = config["erp"]["usuario"]
    self.clave      = config["erp"]["clave"]
    self.proveedor  = config["erp"]["proveedor"]
    self.proxy_host = config["erp"]["proxy_host"]
    self.proxy_port = config["erp"]["proxy_port"]
    self.logger     = IntegradorLogger(client_id=config["client_id"])
```

| Método | Descripción |
|--------|-------------|
| `_build_xml(sql)` | Construye XML SOAP con NombreConexion, IdCia, Sql, etc. |
| `_get_client()` | Crea sesión requests con proxy opcional; `Transport(timeout=600)` |
| `_clean_string(valor)` | Elimina caracteres no imprimibles; no modifica no-strings |
| `get(endpoint, params)` | `params["sql"]` = SQL; serializa con `helpers.serialize_object()` |
| `test_connection()` | `SELECT 1 AS test` — universal para cualquier cliente |

---

### `connection/excel_connector.py` — fallback de emergencia ✅

- Patrón: Strategy
- Procesos válidos: `productos`, `partners`, `entradas`, `salidas`
- Ruta: `/etc/integrador/excel/{client_id}/{client_id}-{proceso}.xlsx`
- No usa GCP — el fallback no puede depender de lo que causó el fallo

**Constructor:**
```python
def __init__(self, config: dict):
    self.client_id = config["client_id"]
    self.ruta_base = f"/etc/integrador/excel/{self.client_id}/"
    self.logger    = IntegradorLogger(client_id=self.client_id)
```

| Método | Descripción |
|--------|-------------|
| `_get_ruta_archivo(proceso)` | `{ruta_base}/{client_id}-{proceso}.xlsx` |
| `get(endpoint, params)` | `dtype=str` + dict comprehension NaN→None |
| `test_connection()` | Verifica cuáles de los 4 archivos existen |

---

### `connection/siesa_connekta.py` — SIESA Connekta ✅

- Patrón: Strategy
- Protocolo: REST/JSON
- `verify=True`

**Constructor:**
```python
def __init__(self, config: dict):
    self.url         = config["erp"]["url"]
    self.url_qa      = config["erp"].get("url_qa", "")
    self.id_compania = config["erp"]["idcompania"]
    self.conni_key   = config["erp"]["connikey"]
    self.conni_token = config["erp"]["connitoken"]
    self.client_id   = config["client_id"]
    self.logger      = IntegradorLogger(client_id=self.client_id)
```

**Construcción de URL en `get()`:**
```
{url}?idCompania={id_compania}&descripcion={query_desc}
     &paginacion=numPag={n}|tamPag={t}   ← solo si no_paginar=False
```

`params` acepta: `query_desc`, `single_page`, `tam_pag` (default 100), `no_paginar`

**Detección automática de formato:**
```python
items = detalle.get("Datos")
if items is None:
    items = detalle.get("Table")   # compatibilidad versiones antiguas de Connekta
```

| Método | Descripción |
|--------|-------------|
| `_get_headers()` | `ConniKey`, `ConniToken`, `Content-Type`, `Accept` |
| `get(endpoint, params)` | URL dinámica; paginación automática; detecta Datos vs Table |
| `test_connection()` | GET al endpoint base — 200/400/404 = OK |

---

### `connection/jsonrpc.py` — base JSON-RPC Odoo ✅

> **No hereda `ERPConnector`** — es la base del `core/`. Capas distintas, contratos distintos.

**Constructor:**
```python
def __init__(self, config: dict):
    self.url            = config["odoo"]["url"].rstrip("/")
    self.db             = config["odoo"]["database"]
    self.username       = config["odoo"]["usuario"]   # atributo interno: username
    self.password       = config["odoo"]["clave"]     # atributo interno: password
    self._session       = requests.Session()
    self._session_id    = None
    self._authenticated = False
    self.logger         = IntegradorLogger(client_id=config["client_id"])
```

> Las **llaves del dict GCP** son `usuario`/`clave`. Los **atributos de instancia** son `self.username`/`self.password`. Son distintos a propósito.

| Método | Descripción |
|--------|-------------|
| `authenticate()` | Login Odoo — guarda `_session_id`; pone `_authenticated=True` |
| `_call_kw(model, method, args, kwargs)` | Núcleo privado — todos los métodos lo usan; timeout `(5, 30)` |
| `_extract_odoo_error(body)` | `@staticmethod` defensivo con `.get()` — nunca lanza `KeyError` |
| `search_read(model, domain, fields, limit, offset, order)` | Busca y lee registros |
| `search(model, domain, limit, offset, order)` | Retorna solo IDs |
| `search_count(model, domain)` | Cuenta registros |
| `read(model, ids, fields)` | Lee campos — `ids` va en `args`, no en `kwargs` (protocolo Odoo) |
| `create(model, fields)` | Crea un registro |
| `write(model, ids, fields)` | Actualiza — `ids` es `list`, no `int` |
| `unlink(model, ids)` | Elimina |
| `action(model, method, ids, kwargs)` | Ejecuta métodos de negocio |
| `test_connection()` | Llama `authenticate()` |

**Reglas importantes:**
- `write()` recibe `ids: list` (legacy usaba `code: int`)
- `tracking`, `vat`, `default_code` → solo en `create()`, **nunca** en `write()` (Odoo lanza error)
- Default args usan `None` en vez de `[]` o `{}` (evita bug clásico de mutables compartidos)
- Timeout `(5, 30)` en todos los requests: 5 s para conectar, 30 s para leer

---

## Estrategia de ramas Git

| Rama | Propósito |
|------|-----------|
| `main` | Solo documentación (README, docs/) |
| `develop` | Integración de fases completadas |
| `fase{N}/{nombre}` | Desarrollo activo de cada fase |

Las ramas de fase se crean desde `develop` y acumulan todo el código previo.

---

## Suite de pruebas — `test/` (carpeta sin 's')

> **La carpeta es `test/`**, no `tests/`. Cualquier configuración de pytest debe apuntar a `test/`.

| Archivo | Estado | Pruebas |
|---------|--------|---------|
| `test/test_loader.py` | ⬜ Stub | 29 diseñadas, sin implementar |
| `test/test_connection.py` | ✅ Completo | 77 / 77 |
| `test/test_transform.py` | ⬜ Stub | — |
| `test/test_core.py` | ⬜ Stub | — |
| `test/test_main.py` | ⬜ Stub | — |
| `test/test_scheduler.py` | ⬜ Stub | — |
| `test/test_api.py` | ⬜ Stub | — |

### `test/test_connection.py` — 77/77 ✅

| Clase | Módulo probado | Pruebas |
|-------|----------------|---------|
| `TestERPConnector` | `connection/base.py` | 4 |
| `TestSAP` | `connection/sap.py` | 16 |
| `TestSiesaEnterprise` | `connection/siesa_enterprise.py` | 17 |
| `TestSiesaConnekta` | `connection/siesa_connekta.py` | 15 |
| `TestExcelConnector` | `connection/excel_connector.py` | 8 |
| `TestJsonRPC` | `connection/jsonrpc.py` | 17 |

**Convenciones:**
- Ninguna prueba hace llamadas reales — todo mockeado con `patch` y `MagicMock`
- `patch.dict(os.environ, {"ENV": "dev"})` en todas las clases para evitar que `IntegradorLogger` cree archivos de log
- `TestERPConnector` es la excepción — `ERPConnector` es abstracta y no instancia el logger

---

## Fases pendientes

| Fase | Módulo | Archivos clave |
|------|--------|----------------|
| 3 | Transform Layer | `transform/base.py`, `transform_sap.py`, `transform_ws.py`, `transform_connekta.py` |
| 4 | Core Layer | `core/base.py`, `process_items.py`, `process_partners.py`, `process_purchases.py`, `process_sales.py` |
| 5 | BD integrador | `db/schema.sql`, `db/logger.py` |
| 6 | Tests completos | todos los stubs en `test/` |
| 7 | Main / Factory | `main.py` |
| 8 | Scheduler | `scheduler/runner.py` |
| 9 | API FastAPI | `api/app.py` |
| 10-11 | Frontend | `frontend/` |

---

## Código legacy de clientes (referencia)

```
C:\Users\Jorge Rivera\Documents\360S\Clientes\
  ├── Aurofarma / Autovenz / Faber Castell / Fazan / Fenix
  ├── GNL / Grupo empresarial papis / Juan de Hoyos
  ├── OIT / Repuestos Simón Bolivar / Surtinegocios
  ├── Tito Pabón / Veneplast / bycsa
  └── Secretos/   ← JSONs de credenciales por cliente
```

- `OIT/connection/conexion_conektap.py` — referencia para `siesa_connekta.py`
- `GNL/connection/rpc_wms.py` — único legacy con XML-RPC (protocolo descartado)
- Queries SQL actuales de Fénix: `Clientes/Fenix/query_master/` y `query_transaction/`

---

## Correcciones importantes al modelo de IA

- **Factory vs Strategy:** los métodos `load_*` de `ConfigLoader` usan Factory, no Strategy
- **Llaves del dict GCP:** `database`, `usuario`, `clave` — nunca `db`, `username`, `password`
- **Atributos de instancia JsonRPC:** `self.username` y `self.password` (no `self.usuario`/`self.clave`)
- **`JsonRPC` no hereda `ERPConnector`** — son capas distintas con contratos distintos
- **No existe `_paginate()`** en `ERPConnector` — cada conector maneja su propia paginación
- **`SELECT 1 AS test`** en SIESA WS — no usar tablas específicas del cliente (`t430`, etc.)
- No escribir archivos de código fuente directamente — mostrar en consola para que Jorge lo pegue manualmente
