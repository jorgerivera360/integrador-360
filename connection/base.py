"""
ERPConnector — Clase base abstracta
Responsabilidades:
  - Define el contrato que todos los conectores deben cumplir
  - get() — método abstracto — trae datos del ERP
  - test_connection() — método abstracto — prueba la conexión
  - _paginate() — Template Method — lógica de paginación compartida
Patrones: Strategy · Template Method
Fase: 2 — Connection Layer
"""