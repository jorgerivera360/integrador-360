"""
TransformBase — Clase base abstracta
Responsabilidades:
  - _apply_field_mapping() — renombra campos del ERP
  - _clean_string() — elimina caracteres de control
  - _parse_date() — convierte fechas al formato Odoo
  - _normalize_uom() — normaliza unidades de medida
  - _validate_producto/compra/venta() — valida campos mínimos
  - _apply_filters() — aplica filtros de client_config
  - get_flow() — método abstracto — cada transform lo implementa
Patrones: Template Method · Strategy
Fase: 3 — Transform Layer
"""