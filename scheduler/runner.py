"""
IntegradorScheduler — Scheduler del sistema
Responsabilidades:
  - __init__() — recibe config y run_fn del main
  - _arranque_ordenado() — ejecuta maestros primero
  - _register_flows() — registra flujos en APScheduler
  - _run_with_retry() — envuelve run() con backoff exponencial
  - start() — arranca el scheduler
Patrones: Observer · Template Method
Librería: APScheduler · ThreadPoolExecutor
Fase: 8 — Scheduler
"""