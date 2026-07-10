"""
ProcessBase — Clase base del core
Responsabilidades:
  - Lookups en lote comunes a todos los procesos
  - _lookup_uoms() — busca UOMs en Odoo
  - _lookup_taxes() — busca impuestos en Odoo
  - _lookup_departments() — busca departamentos en Odoo
  - _lookup_countries() — busca países en Odoo
Hereda: JsonRPC
Nota: No es abstracta — agrupa utilidades compartidas
Fase: 4 — Core Layer
"""