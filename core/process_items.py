"""
ProcessItems — Carga productos en Odoo
Responsabilidades:
  - products() — carga productos en product.template
  - Anti-duplicado por default_code
  - Lookups: UOMs · categorías · rutas · impuestos
  - tracking solo en create — nunca en write
Hereda: ProcessBase
Fase: 4 — Core Layer
"""