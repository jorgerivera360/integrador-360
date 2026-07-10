"""
ProcessPartners — Carga partners en Odoo
Responsabilidades:
  - partners_customer() — carga clientes en res.partner
  - partners_supplier() — carga proveedores en res.partner
  - Anti-duplicado por vat + sucursal
  - Lookups: departamentos · zonas · tipos de identificación
Hereda: ProcessBase
Fase: 4 — Core Layer
"""