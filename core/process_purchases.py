"""
ProcessPurchases — Carga compras en Odoo
Responsabilidades:
  - purchase_orders() — carga OCs en purchase.order
  - purchase_returns() — carga devoluciones
  - entrada_traslado() — carga traslados de entrada
  - Anti-duplicado por name
  - Agrupa líneas por documento
Hereda: ProcessBase
Fase: 4 — Core Layer
"""