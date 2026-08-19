from fastapi import APIRouter, Depends, Query
from api.dependencies import get_db
from api.auth import require_role

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/status")
def get_status(
    db=Depends(get_db),
    current_user=Depends(require_role("superadmin", "admin", "viewer"))
):
    cursor = db.cursor()

    # Clientes activos vs total
    cursor.execute("SELECT COUNT(*) AS total, COUNT(*) FILTER (WHERE is_active) AS activos FROM clients")
    clients = cursor.fetchone()

    # Flows activos vs total
    cursor.execute("SELECT COUNT(*) AS total, COUNT(*) FILTER (WHERE is_active) AS activos FROM flows")
    flows = cursor.fetchone()

    # Ejecuciones de las últimas 24 horas
    cursor.execute("""
        SELECT
            COUNT(*) AS total,
            COUNT(*) FILTER (WHERE status = 'success') AS exitosas,
            COUNT(*) FILTER (WHERE status = 'partial') AS parciales,
            COUNT(*) FILTER (WHERE status = 'error') AS errores,
            COUNT(*) FILTER (WHERE status = 'running') AS en_curso
        FROM executions
        WHERE started_at >= NOW() - INTERVAL '24 hours'
    """)
    executions_24h = cursor.fetchone()

    # Últimas 10 ejecuciones
    cursor.execute("""
        SELECT e.id, e.status, e.started_at, e.finished_at, e.triggered_by,
            f.flow_name, f.flow_type, c.client_id AS client_slug, c.name AS client_name
        FROM executions e
        JOIN flows f ON e.flow_id = f.id
        JOIN clients c ON f.client_id = c.id
        ORDER BY e.started_at DESC
        LIMIT 10
    """)
    recent = cursor.fetchall()

    return {
        "code": 200,
        "result": {
            "clients": dict(clients),
            "flows": dict(flows),
            "executions_24h": dict(executions_24h),
            "recent_executions": recent,
        }
    }


@router.get("/errors")
def get_errors(
    limit: int = Query(default=20, le=100),
    db=Depends(get_db),
    current_user=Depends(require_role("superadmin", "admin", "viewer"))
):
    cursor = db.cursor()

    cursor.execute("""
        SELECT e.id, e.status, e.started_at, e.finished_at,
            e.error_message, e.result, e.triggered_by,
            f.flow_name, f.flow_type,
            c.client_id AS client_slug, c.name AS client_name
        FROM executions e
        JOIN flows f ON e.flow_id = f.id
        JOIN clients c ON f.client_id = c.id
        WHERE e.status IN ('error', 'partial')
        ORDER BY e.started_at DESC
        LIMIT %s
    """, (limit,))

    return {"code": 200, "result": cursor.fetchall()}