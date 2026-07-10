"""
main.py — Orquestador del sistema
Responsabilidades:
  - build_connector() — Factory — instancia el conector correcto
  - build_transform() — Factory — instancia el transform correcto
  - connection_data() — autentica en Odoo
  - _dispatch_flow() — decide qué core ejecutar
  - run() — orquesta todo en orden
  - Bloque ENV — decide el modo de operación
Patrones: Factory · Strategy
Fase: 7 — Main
"""