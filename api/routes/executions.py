import os
import threading
from fastapi import APIRouter, Depends, HTTPException, Query
from api.dependencies import get_db
from api.auth import require_role
from api.schemas.executions import ExecutionResponse

router = APIRouter(tags=["Executions"])


@router.get("/flows/{flow_id}/executions", response_model=list[ExecutionResponse])
def get_executions(
    flow_id: int,
    status: str = None,
    triggered_by: str = None,
    limit: int = Query(default=50, le=500),
    offset: int = Query(default=0, ge=0),
    db=Depends(get_db),
    current_user=Depends(require_role("superadmin", "admin", "viewer"))
):
    cursor = db.cursor()

    cursor.execute("SELECT id FROM flows WHERE id = %s", (flow_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Flow no encontrado")

    query = "SELECT * FROM executions WHERE flow_id = %s"
    params = [flow_id]

    if status is not None:
        query += " AND status = %s"
        params.append(status)
    if triggered_by is not None:
        query += " AND triggered_by = %s"
        params.append(triggered_by)

    query += " ORDER BY started_at DESC LIMIT %s OFFSET %s"
    params.extend([limit, offset])

    cursor.execute(query, params)
    return cursor.fetchall()


@router.get("/executions/recent", response_model=list[ExecutionResponse])
def get_recent_executions(
    status: str = None,
    limit: int = Query(default=20, le=100),
    db=Depends(get_db),
    current_user=Depends(require_role("superadmin", "admin", "viewer"))
):
    cursor = db.cursor()

    query = "SELECT * FROM executions WHERE 1=1"
    params = []

    if status is not None:
        query += " AND status = %s"
        params.append(status)

    query += " ORDER BY started_at DESC LIMIT %s"
    params.append(limit)

    cursor.execute(query, params)
    return cursor.fetchall()


@router.get("/executions/errors", response_model=list[ExecutionResponse])
def get_error_executions(
    limit: int = Query(default=20, le=100),
    db=Depends(get_db),
    current_user=Depends(require_role("superadmin", "admin", "viewer"))
):
    cursor = db.cursor()
    cursor.execute(
        """SELECT e.*, f.flow_name, c.client_id AS client_slug, c.name AS client_name
        FROM executions e
        JOIN flows f ON e.flow_id = f.id
        JOIN clients c ON f.client_id = c.id
        WHERE e.status IN ('error', 'partial')
        ORDER BY e.started_at DESC
        LIMIT %s""",
        (limit,)
    )
    return cursor.fetchall()


@router.post("/flows/{flow_id}/execute", status_code=202)
def execute_flow(
    flow_id: int,
    db=Depends(get_db),
    current_user=Depends(require_role("superadmin", "admin"))
):
    cursor = db.cursor()

    cursor.execute(
        """SELECT f.id, f.flow_name, f.flow_type, f.flow_config, f.is_active,
        c.client_id AS client_slug, c.is_active AS client_active
        FROM flows f
        JOIN clients c ON f.client_id = c.id
        WHERE f.id = %s""",
        (flow_id,)
    )
    flow = cursor.fetchone()

    if not flow:
        raise HTTPException(status_code=404, detail="Flow no encontrado")
    if not flow["is_active"]:
        raise HTTPException(status_code=400, detail="El flow está desactivado")
    if not flow["client_active"]:
        raise HTTPException(status_code=400, detail="El cliente está desactivado")

    cursor.execute(
        "SELECT id FROM executions WHERE flow_id = %s AND status = 'running'",
        (flow_id,)
    )
    if cursor.fetchone():
        raise HTTPException(status_code=409, detail="Ya hay una ejecución en curso para este flow")

    thread = threading.Thread(
        target=_execute_flow_background,
        args=(flow["client_slug"], flow_id, current_user["id"])
    )
    thread.start()

    return {
        "msg": "Ejecución iniciada",
        "flow_name": flow["flow_name"],
        "client": flow["client_slug"],
    }


def _execute_flow_background(client_slug, flow_id, user_id):
    from config.loader import ConfigLoader
    from config.logger import IntegradorLogger
    from db.writer import DBWriter
    import main as main_module

    logger = IntegradorLogger(client_id=client_slug)
    db_writer = DBWriter(database_url=os.getenv("DATABASE_URL"), logger=logger)

    try:
        loader = ConfigLoader(client_id=client_slug)
        config = loader.load_config()
        db_config = loader.load_db_config()
        erp_type = db_config["erp_type"]

        flow = None
        for f in db_config["flows"]:
            if f["flow_id"] == flow_id:
                flow = f
                break

        if not flow:
            logger.error(f"Flow {flow_id} no encontrado en db_config")
            return

        flow_configs = {}
        for f in db_config["flows"]:
            if f["flow_type"] in ("items", "customer", "supplier"):
                flow_configs[f["flow_type"]] = f["flow_config"]

        main_module.run(
            flow=flow,
            config=config,
            erp_type=erp_type,
            flow_configs=flow_configs,
            db_writer=db_writer,
            triggered_by="manual",
            triggered_user=user_id
        )

    except Exception as e:
        logger.error(f"Error en ejecución manual flow_id={flow_id}: {e}")