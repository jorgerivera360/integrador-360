"""
DBLogger — Manejo de logs en la BD
Responsabilidades:
  - log_flow_execution() — escribe en flow_execution_logs
  - log_record_error()   — escribe en flow_record_errors
  - get_scheduler_state() — lee desde scheduler_state
  - set_scheduler_state() — actualiza scheduler_state
Nota: Clase separada de ConfigLoader — responsabilidad única
Fase: 6 — Config Layer BD
"""