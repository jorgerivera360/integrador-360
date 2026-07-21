```markdown
  # Arquitectura del Integrador V2

  ## Capas del sistema

  ERP (SIESA WS / SIESA Connekta / SAP B1 / KubApp / Excel)
      ↓
  connection/     ← habla el protocolo del ERP, retorna lista de dicts crudos
      ↓
  transform/      ← normaliza al formato interno, aplica mappings y filtros
      ↓
  core/           ← escribe en Odoo via JSON-RPC, anti-duplicado y upsert
      ↓
  Odoo WMS

  Capas transversales que alimentan todas las anteriores:

  config/         ← credenciales desde GCP Secret Manager + fallback local
  scheduler/      ← APScheduler con backoff exponencial
  db/             ← logs de ejecución y estado del scheduler
  api/            ← FastAPI expone todo al frontend

  ---

  ## Patrones de diseño

  | Patrón | Ubicación | Por qué |
  |--------|-----------|---------|
  | Strategy | `connection/` y `transform/` | Cada ERP es intercambiable sin cambiar el core |
  | Template Method | `base.py` de cada capa | Lógica compartida en la base, detalles en subclases |
  | Factory | `main.py` y `config/loader.py` | Decide qué conector/transform instanciar según el tipo de ERP |
  | Singleton | `connection/sap.py` | El SessionId se obtiene una vez y se reutiliza |
  | Observer | `scheduler/runner.py` | APScheduler notifica cuándo ejecutar |

  ---

  ## Flujo del dato

  1. ConfigLoader carga credenciales desde GCP (o fallback local)
  2. Factory en main.py instancia el conector y el transform correctos
  3. connector.get(endpoint, params) → lista de dicts crudos del ERP
  4. transform.get_flow(data) → lista de dicts normalizados
  5. process_*.run(data) → create() / write() en Odoo via JSON-RPC
  6. DBLogger registra resultado de la ejecución

  ---

  ## Contrato de los conectores

  Todos los conectores heredan `ERPConnector` e implementan:

  ```python
  def get(self, endpoint: str, params: dict = {}) -> tuple:
      # Retorna (True, lista_de_dicts) o (False, str_error)

  def test_connection(self) -> tuple:
      # Retorna (True, mensaje_ok) o (False, mensaje_error)

  Cada conector maneja su propia paginación internamente.

  ---
  Contrato de JSON-RPC con Odoo

  JsonRPC no hereda ERPConnector — es la base de core/.

  Reglas críticas:
  - tracking, vat, default_code → solo en create(), nunca en write()
  - write() recibe ids: list, no int
  - timeout (5, 30) en todas las peticiones
  - Cookies manejadas automáticamente por requests.Session()

  ---
  Configuración

  Los secretos viven en GCP Secret Manager con el nombre integrador-{client_id}.
  La estructura del JSON varía por tipo de ERP — ver docs/instalacion.md.

  El ConfigLoader intenta GCP primero. Si falla, carga desde:
  /etc/integrador/credentials/integrador-{client_id}.json

  En staging y prod, la variable ENV la inyecta systemd.
  En desarrollo local, se carga desde .env.

  ---

  ## `docs/instalacion.md`

  Está muy completo y bien escrito. Solo hay **dos cambios** necesarios:

  **1. Formato del secret de Connekta** — la URL ya no lleva los params hardcodeados. Reemplaza el bloque JSON de Connekta por este:

  ```json
  {
    "erp": {
      "tipo":       "connekta",
      "url":        "https://servicios.siesacloud.com/api/connekta/v3/ejecutarconsulta",
      "urlqa":      "https://serviciosqa.siesacloud.com/api/connekta/v3/ejecutarconsulta",
      "idcompania": "XXXX",
      "connikey":   "llave_connekta",
      "connitoken": "token_connekta"
    },
    "odoo": {
      "url":      "https://cliente.360software.com.co",
      "database": "cliente_v17_prod",
      "usuario":  "integrador@cliente.com",
      "clave":    "contraseña_odoo"
    }
  }

  2. Agregar sección de validación al final, antes del cierre:

  ---

  ## 8. Validar la conexión con todos los ERPs

  Usar el script `pruebasF2.py` incluido en el proyecto:

  ```bash
  source /app/integrador-360/venv/bin/activate
  cd /app/integrador-360

  python3 pruebasF2.py fenix        # SIESA WS
  python3 pruebasF2.py fabercastell # SAP B1
  python3 pruebasF2.py oit          # SIESA Connekta

  El script verifica GCP, la conexión al ERP, el Excel fallback
  y los errores de configuración. Ver salida esperada en docs/clientes.md.

  ---

  ## `docs/clientes.md`

  ```markdown
  # Cómo agregar un cliente nuevo

  ## Paso 1 — Crear el secret en GCP

  GCP Console → Secret Manager → Crear secreto
  Nombre: integrador-{client_id}
  Valor:  JSON con credenciales según el tipo de ERP

  Ver formatos de JSON por tipo de ERP en `docs/instalacion.md`.

  ---

  ## Paso 2 — Verificar la conexión desde el servidor

  ```bash
  source /app/integrador-360/venv/bin/activate
  cd /app/integrador-360

  python3 -c "
  from config.loader import ConfigLoader
  c = ConfigLoader('nuevo_cliente').load_config()
  print('Tipo ERP:', c['erp']['tipo'])
  print('Odoo URL:', c['odoo']['url'])
  "

  ---
  Paso 3 — Probar el conector completo

  python3 pruebasF2.py nuevo_cliente

  Salida esperada:

  [OK]  Config cargada desde GCP
  [OK]  test_connection(): Conexión exitosa con ...
  [OK]  get(): N registros
  [OK]  Archivo creado
  [OK]  get('productos'): 3 registros
  [OK]  Celda vacia -> None: correcto
  [OK]  Retorno False correcto: True
  [OK]  Retorno (True, []) correcto: True
  [OK]  Fallo correctamente: RuntimeError

  ---
  Paso 4 — Agregar el cliente al scheduler (Fase 8)

  Pendiente de implementación.

  ---
  Paso 5 — Registrar el cliente en la BD (Fase 6)

  Pendiente de implementación.

  ---
  Mapeo de client_id por cliente activo

  ┌────────────────────┬──────────────┬────────────────┬────────────────────────────────────┐
  │      Cliente       │  client_id   │      ERP       │                Odoo                │
  ├────────────────────┼──────────────┼────────────────┼────────────────────────────────────┤
  │ Fénix              │ fenix        │ SIESA WS       │ fenix.360software.com.co           │
  ├────────────────────┼──────────────┼────────────────┼────────────────────────────────────┤
  │ Faizan             │ faizan       │ SIESA WS       │ faizan.360software.com.co          │
  ├────────────────────┼──────────────┼────────────────┼────────────────────────────────────┤
  │ Surtinegocios      │ surtin       │ SIESA WS       │ surtinegocios.360software.com.co   │
  ├────────────────────┼──────────────┼────────────────┼────────────────────────────────────┤
  │ Papis              │ papis        │ SIESA WS       │ papis.360software.com.co           │
  ├────────────────────┼──────────────┼────────────────┼────────────────────────────────────┤
  │ Tito Pabón         │ titopab      │ SIESA Connekta │ titopabon.360software.com.co       │
  ├────────────────────┼──────────────┼────────────────┼────────────────────────────────────┤
  │ OIT                │ oit          │ SIESA Connekta │ oit.360software.com.co             │
  ├────────────────────┼──────────────┼────────────────┼────────────────────────────────────┤
  │ R.P. Simón Bolívar │ rpsimbol     │ SIESA Connekta │ rpsimbol.360software.com.co        │
  ├────────────────────┼──────────────┼────────────────┼────────────────────────────────────┤
  │ BYCSA              │ bycsa        │ SAP B1         │ bycsa.360software.com.co           │
  ├────────────────────┼──────────────┼────────────────┼────────────────────────────────────┤
  │ Faber Castell      │ fabercastell │ SAP B1         │ fabercastellv17.360software.com.co │
  ├────────────────────┼──────────────┼────────────────┼────────────────────────────────────┤
  │ ```                │              │                │                                    │
  └────────────────────┴──────────────┴────────────────┴────────────────────────────────────┘