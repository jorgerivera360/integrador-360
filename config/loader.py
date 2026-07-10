"""
ConfigLoader — Único punto de acceso a la configuración
Responsabilidades:
  - __init__() — recibe client_id · detecta entorno desde ENV
  - _load_from_gcp() — lee credenciales desde GCP Secret Manager
  - _load_from_env() — fallback para desarrollo local
  - _load_from_db() — lee configuración UI desde la BD
  - load_config() — fusiona GCP + BD · Factory · retorna dict completo
  - get_sql() — trae SQL por nombre desde sql_templates
Patrones: Factory · Singleton implícito
"""