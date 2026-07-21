# Integrador ERP ↔ WMS
  ### 360 Software — Medellín, Colombia

  Sistema de integración entre múltiples ERPs y Odoo WMS.
  Conecta SIESA WS, SIESA Connekta y SAP con Odoo.

  ---

  ## Arquitectura

  El sistema está organizado en capas. Cada capa tiene una
  responsabilidad clara y no conoce los detalles de las demás.
 
  ERP (SIESA / SAP / KubApp)
      ↓ dato crudo
  connection/
      ↓ lista de dicts crudos
  transform/
      ↓ lista de dicts normalizados
  core/
      ↓ create() / write() via jsonrpc
  Odoo WMS

  ---

  ## Estructura de carpetas

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
  │   y test_connection(). Cada conector maneja su propia
  │   paginación — no existe _paginate() centralizado.
  │   │
  │   ├── base.py
  │   │   Clase abstracta ERPConnector. Define el contrato
  │   │   que todos los conectores deben cumplir.
  │   │
  │   ├── siesa_enterprise.py
  │   │   Conector SIESA WS. Usa SOAP con zeep.
  │   │   Limpia caracteres de control del XML.
  │   │   Serializa objetos zeep con helpers.serialize_object().
  │   │   Clientes: Fénix · Faizan · Surtinegocios · Papis
  │   │
  │   ├── siesa_connekta.py
  │   │   Conector SIESA Connekta. Usa REST/JSON.
  │   │   Detecta automáticamente formato Datos vs Table.
  │   │   Construye URL dinámica con idCompania y query_desc.
  │   │   Clientes: Tito Pabón · OIT · R.P. Simón Bolívar
  │   │
  │   ├── sap.py
  │   │   Conector SAP Business One. Usa OData.
  │   │   Maneja SessionId con patrón Singleton.
  │   │   Clientes: BYCSA · Faber Castell
  │   │
  │   ├── excel_connector.py
  │   │   Conector fallback de emergencia. Lee archivos xlsx
  │   │   con dtype=str y convierte NaN a None.
  │   │   Se activa para cualquier cliente cuando su ERP falla.
  │   │
  │   └── jsonrpc.py
  │       Base de conexión con Odoo. No hereda ERPConnector.
  │       Usa requests.Session() para manejo automático de cookies.
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
  │   │   _normalize_uom(), validate*(), _apply_field_mapping()
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
  │   │   carga desde credenciales locales en el servidor.
  │   │
  │   └── logger.py
  │       IntegradorLogger. Maneja los logs del sistema.
  │       En dev imprime en consola. En staging y prod
  │       escribe en archivo con rotación automática (10 MB, 5 backups).
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
  │       ├── components/     Componentes reutilizables
  │       ├── pages/          Secciones del panel
  │       ├── services/       Llamadas a la API
  │       ├── context/        Estado global — AppContext
  │       └── App.jsx         Router principal
  │
  ├── test/
  │   Pruebas unitarias por capa. Carpeta sin 's'.
  │   │
  │   ├── test_loader.py      Pruebas de config/loader.py
  │   ├── test_connection.py  77/77 pruebas — completo ✅
  │   ├── test_transform.py   Pendiente
  │   ├── test_core.py        Pendiente
  │   ├── test_main.py        Pendiente
  │   ├── test_scheduler.py   Pendiente
  │   └── test_api.py         Pendiente
  │
  ├── docs/
  │   │
  │   ├── instalacion.md      Pasos para instalar en servidor nuevo
  │   ├── arquitectura.md     Descripción de capas y patrones
  │   └── clientes.md         Cómo agregar un cliente nuevo
  │
  ├── pruebasF2.py            Script de integración en servidor
  ├── .env.example            Variables de entorno sin valores reales
  ├── .gitignore              Python · .env · credenciales · node_modules
  ├── requirements.txt        Dependencias Python del proyecto
  └── README.md               Este archivo

  ---

  ## Patrones de diseño utilizados

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

  ---

  ## Variables de entorno

  Copia `.env.example` a `.env` y completa los valores:

  ```bash
  cp .env.example .env

  ENV=staging
  GOOGLE_APPLICATION_CREDENTIALS=/etc/integrador/gcp-key.json
  GCP_PROJECT_ID=hale-treat-398215

  ▎ En producción, systemd inyecta estas variables — no se necesita .env.

  ---
  Ubicación de archivos en el servidor

  Proyecto:      /app/integrador-360/
  Credenciales:  /etc/integrador/credentials/integrador-{client_id}.json
  Logs:          /var/log/integrador/integrador-{client_id}.log
  GCP key:       /etc/integrador/gcp-key.json
  Excel:         /etc/integrador/excel/{client_id}/{client_id}-{proceso}.xlsx
  Entorno:       /app/integrador-360/.env

  ---
  Comportamiento por entorno

  ENV=dev      → logs en consola con print()
  ENV=staging  → logs en archivo rotativo
  ENV=prod     → logs en archivo rotativo

  ---
  Estado del proyecto

  Fase 0  — Setup inicial          ✅ Completado
  Fase 1  — Config Layer GCP       ✅ Completado
  Fase 2  — Connection Layer       ✅ Completado y validado en servidor
  Fase 3  — Transform Layer        ⬜ Pendiente
  Fase 4  — Core Layer             ⬜ Pendiente
  Fase 5  — BD del integrador      ⬜ Pendiente
  Fase 6  — Config Layer BD        ⬜ Pendiente
  Fase 7  — Main                   ⬜ Pendiente
  Fase 8  — Scheduler              ⬜ Pendiente
  Fase 9  — API                    ⬜ Pendiente
  Fase 10 — Frontend               ⬜ Pendiente
  Fase 11 — End-to-end             ⬜ Pendiente