from fastapi import APIRouter, Depends, Query
from api.dependencies import get_db
from api.auth import require_role

router = APIRouter(prefix="/changes", tags=["Changes"])


@router.get("/")
def get_changes(
    table_name: str = None,
    record_id: int = None,
    action: str = None,
    changed_by: int = None,
    limit: int = Query(default=50, le=500),
    offset: int = Query(default=0, ge=0),
    db=Depends(get_db),
    current_user=Depends(require_role("superadmin", "admin", "viewer"))
):
    cursor = db.cursor()

    query = """
        SELECT ch.*, u.name AS changed_by_name, u.email AS changed_by_email
        FROM change_history ch
        LEFT JOIN users u ON ch.changed_by = u.id
        WHERE 1=1
    """
    params = []

    if table_name is not None:
        query += " AND ch.table_name = %s"
        params.append(table_name)
    if record_id is not None:
        query += " AND ch.record_id = %s"
        params.append(record_id)
    if action is not None:
        query += " AND ch.action = %s"
        params.append(action)
    if changed_by is not None:
        query += " AND ch.changed_by = %s"
        params.append(changed_by)

    query += " ORDER BY ch.changed_at DESC LIMIT %s OFFSET %s"
    params.extend([limit, offset])

    cursor.execute(query, params)
    return {"code": 200, "result": cursor.fetchall()}


@router.get("/record/{table_name}/{record_id}")
def get_record_history(
    table_name: str,
    record_id: int,
    db=Depends(get_db),
    current_user=Depends(require_role("superadmin", "admin", "viewer"))
):
    cursor = db.cursor()

    cursor.execute("""
        SELECT ch.*, u.name AS changed_by_name, u.email AS changed_by_email
        FROM change_history ch
        LEFT JOIN users u ON ch.changed_by = u.id
        WHERE ch.table_name = %s AND ch.record_id = %s
        ORDER BY ch.changed_at DESC
    """, (table_name, record_id))

    changes = cursor.fetchall()

    if not changes:
        return {"code": 200, "result": [], "msg": "Sin historial de cambios"}

    return {"code": 200, "result": changes}