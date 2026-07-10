"""
JsonRPC — Base de conexión con Odoo
Responsabilidades:
  - authenticate() — obtiene token de sesión
  - search_read() — consulta registros en Odoo
  - create() — crea registros en Odoo
  - write() — actualiza registros en Odoo
Nota: No hereda ERPConnector — es la base del core
Fase: 2 — Connection Layer
"""