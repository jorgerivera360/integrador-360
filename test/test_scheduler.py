"""
test_scheduler.py — Pruebas de scheduler/runner.py
Casos de prueba:
  - Arranque ordenado ejecuta maestros en orden correcto
  - maestros_inicializados se marca correctamente en BD
  - Flujos registrados con triggers correctos
  - max_instances = 1 funciona correctamente
  - Retry funciona con backoff correcto
Fase: 8 — Scheduler
"""