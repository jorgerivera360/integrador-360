import json
from fastapi import APIRouter, Depends, HTTPException
from api.dependencies import get_db
from api.auth import require_role
from api.schemas.flows import FlowCreate, FlowUpdate, FlowResponse

router = APIRouter(prefix="/clients/{client_id}/flows", tags=["Flows"])

VALID_FLOW_TYPES = ("items", "customer", "supplier", "purchases", "sales")


@router.get("/", response_model=list[FlowResponse])
def get_flows(
    client_id: int,
    flow_type: str = None,
    is_active: bool = None,
    db=Depends(get_db),
    current_user=Depends(require_role("superadmin", "admin", "viewer"))
):
    cursor = db.cursor()

    cursor.execute("SELECT id FROM clients WHERE id = %s", (client_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    query = "SELECT * FROM flows WHERE client_id = %s"
    params = [client_id]

    if flow_type is not None:
        query += " AND flow_type = %s"
        params.append(flow_type)
    if is_active is not None:
        query += " AND is_active = %s"
        params.append(is_active)

    query += " ORDER BY flow_name"
    cursor.execute(query, params)
    return cursor.fetchall()

@router.get("/summary")
def get_flows_summary(
    client_id: int,
    flow_type: str = None,
    is_active: bool = None,
    db=Depends(get_db),
    current_user=Depends(require_role("superadmin", "admin", "viewer"))
):
    cursor = db.cursor()

    # Verificar que el cliente existe
    cursor.execute("SELECT id FROM clients WHERE id = %s", (client_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    query = """SELECT f.id, f.flow_name, f.flow_type, f.is_active, f.schedule_cron,
                (SELECT MAX(e.started_at) FROM executions e WHERE e.flow_id = f.id) AS last_execution
        FROM flows f
        WHERE f.client_id = %s"""
    params = [client_id]

    if flow_type is not None:
        query += " AND f.flow_type = %s"
        params.append(flow_type)
    if is_active is not None:
        query += " AND f.is_active = %s"
        params.append(is_active)

    query += " ORDER BY f.flow_name"
    cursor.execute(query, params)
    return cursor.fetchall()


@router.get("/{flow_id}", response_model=FlowResponse)
def get_flow(
    client_id: int,
    flow_id: int,
    db=Depends(get_db),
    current_user=Depends(require_role("superadmin", "admin", "viewer"))
):
    cursor = db.cursor()
    cursor.execute(
        "SELECT * FROM flows WHERE id = %s AND client_id = %s",
        (flow_id, client_id)
    )
    flow = cursor.fetchone()
    if not flow:
        raise HTTPException(status_code=404, detail="Flow no encontrado")
    return flow


@router.post("/", response_model=FlowResponse, status_code=201)
def create_flow(
    client_id: int,
    flow: FlowCreate,
    db=Depends(get_db),
    current_user=Depends(require_role("superadmin", "admin"))
):
    cursor = db.cursor()

    cursor.execute("SELECT id FROM clients WHERE id = %s", (client_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    if flow.flow_type not in VALID_FLOW_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"flow_type inválido. Opciones: {', '.join(VALID_FLOW_TYPES)}"
        )

    cursor.execute(
        "SELECT id FROM flows WHERE client_id = %s AND flow_name = %s AND flow_type = %s",
        (client_id, flow.flow_name, flow.flow_type)
    )
    if cursor.fetchone():
        raise HTTPException(
            status_code=400,
            detail=f"Ya existe un flow '{flow.flow_name}' con tipo '{flow.flow_type}' para este cliente"
        )

    cursor.execute(
        """INSERT INTO flows
        (client_id, flow_name, flow_type, flow_config, schedule_cron, created_by, updated_by)
        VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING *""",
        (
            client_id, flow.flow_name, flow.flow_type,
            json.dumps(flow.flow_config), flow.schedule_cron, 
            current_user["id"], current_user["id"]
        )
    )
    new_flow = cursor.fetchone()

    cursor.execute(
        """INSERT INTO change_history
        (table_name, record_id, action, changed_fields, changed_by)
        VALUES ('flows', %s, 'create', %s, %s)""",
        (new_flow["id"], json.dumps({"flow_name": flow.flow_name, "flow_type": flow.flow_type}), current_user["id"])
    )

    db.commit()
    return new_flow


@router.put("/{flow_id}", response_model=FlowResponse)
def update_flow(
    client_id: int,
    flow_id: int,
    flow: FlowUpdate,
    db=Depends(get_db),
    current_user=Depends(require_role("superadmin", "admin"))
):
    cursor = db.cursor()

    cursor.execute(
        "SELECT * FROM flows WHERE id = %s AND client_id = %s",
        (flow_id, client_id)
    )
    existing = cursor.fetchone()
    if not existing:
        raise HTTPException(status_code=404, detail="Flow no encontrado")

    previous_values = {}
    updates = {}

    if flow.flow_name is not None:
        previous_values["flow_name"] = existing["flow_name"]
        updates["flow_name"] = flow.flow_name
    if flow.flow_type is not None:
        if flow.flow_type not in VALID_FLOW_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"flow_type inválido. Opciones: {', '.join(VALID_FLOW_TYPES)}"
            )
        previous_values["flow_type"] = existing["flow_type"]
        updates["flow_type"] = flow.flow_type
    if flow.flow_config is not None:
        previous_values["flow_config"] = existing["flow_config"]
        updates["flow_config"] = json.dumps(flow.flow_config)
    if flow.schedule_cron is not None:
        previous_values["schedule_cron"] = existing["schedule_cron"]
        updates["schedule_cron"] = flow.schedule_cron
    if flow.is_active is not None:
        previous_values["is_active"] = existing["is_active"]
        updates["is_active"] = flow.is_active

    if not updates:
        raise HTTPException(status_code=400, detail="No se enviaron campos para actualizar")

    check_name = updates.get("flow_name", existing["flow_name"])
    check_type = updates.get("flow_type", existing["flow_type"])
    cursor.execute(
        "SELECT id FROM flows WHERE client_id = %s AND flow_name = %s AND flow_type = %s AND id != %s",
        (client_id, check_name, check_type, flow_id)
    )
    if cursor.fetchone():
        raise HTTPException(
            status_code=400,
            detail=f"Ya existe otro flow '{check_name}' con tipo '{check_type}' para este cliente"
        )

    updates["updated_by"] = current_user["id"]
    set_clause = ", ".join(f"{key} = %s" for key in updates)
    values = list(updates.values()) + [flow_id]
    cursor.execute(f"UPDATE flows SET {set_clause} WHERE id = %s RETURNING *", values)
    updated_flow = cursor.fetchone()

    cursor.execute(
        """INSERT INTO change_history
        (table_name, record_id, action, changed_fields, previous_values, changed_by)
        VALUES ('flows', %s, 'update', %s, %s, %s)""",
        (flow_id, json.dumps({k: v for k, v in updates.items() if k != "updated_by"}),
        json.dumps(previous_values, default=str), current_user["id"])
    )

    db.commit()
    return updated_flow


@router.delete("/{flow_id}", status_code=204)
def delete_flow(
    client_id: int,
    flow_id: int,
    db=Depends(get_db),
    current_user=Depends(require_role("superadmin"))
):
    cursor = db.cursor()

    cursor.execute(
        "SELECT * FROM flows WHERE id = %s AND client_id = %s",
        (flow_id, client_id)
    )
    existing = cursor.fetchone()
    if not existing:
        raise HTTPException(status_code=404, detail="Flow no encontrado")

    cursor.execute(
        """INSERT INTO change_history
        (table_name, record_id, action, previous_values, changed_by)
        VALUES ('flows', %s, 'delete', %s, %s)""",
        (flow_id, json.dumps({
            "flow_name": existing["flow_name"],
            "flow_type": existing["flow_type"],
            "flow_config": existing["flow_config"],
            "schedule_cron": existing["schedule_cron"],
        }, default=str), current_user["id"])
    )

    cursor.execute("DELETE FROM flows WHERE id = %s", (flow_id,))
    db.commit()