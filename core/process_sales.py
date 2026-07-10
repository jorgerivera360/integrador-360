"""
ProcessSales — Carga ventas en Odoo
Responsabilidades:
  - sales_orders() — carga pedidos en sale.order
  - returns_sale() — carga devoluciones de venta
  - crucefacturas() — cruza remisiones con facturas
  - sales_stock_exit() — salidas de stock
  - process_stock_exit_consignment() — salidas consignación
  - stock_transfers_between() — traslados entre almacenes
  - sales_transfers_internal() — traslados internos
  - Anti-duplicado por name
Hereda: ProcessBase
Fase: 4 — Core Layer
"""