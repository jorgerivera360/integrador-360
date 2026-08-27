from fastapi import APIRouter, Depends, HTTPException
from api.dependencies import get_db
from api.auth import require_role
from api.schemas.clients import ClientCreate, ClientUpdate, ClientResponse

router = APIRouter(prefix="/clients", tags=["Clients"])


@router.get("/", response_model=list[ClientResponse])
def get_clients(
    erp_type: str = None,
    is_active: bool = None,
    search: str = None,
    db=Depends(get_db),
    current_user=Depends(require_role("superadmin", "admin", "viewer"))
):
    cursor = db.cursor()
    query = """SELECT cl.*,
                c.name AS created_by_name,
                up.name AS updated_by_name
        FROM clients cl
        LEFT JOIN users c ON cl.created_by = c.id
        LEFT JOIN users up ON cl.updated_by = up.id
        WHERE 1=1"""
    params = []

    if erp_type is not None:
        query += " AND cl.erp_type = %s"
        params.append(erp_type)
    if is_active is not None:
        query += " AND cl.is_active = %s"
        params.append(is_active)
    if search is not None:
        query += " AND (cl.client_id ILIKE %s OR cl.name ILIKE %s)"
        params.extend([f"%{search}%", f"%{search}%"])

    query += " ORDER BY cl.name"
    cursor.execute(query, params)
    return cursor.fetchall()


@router.get("/{client_id}", response_model=ClientResponse)
def get_client(
    client_id: int,
    db=Depends(get_db),
    current_user=Depends(require_role("superadmin", "admin", "viewer"))
):
    cursor = db.cursor()
    cursor.execute("""SELECT cl.*,
            c.name AS created_by_name,
            up.name AS updated_by_name
        FROM clients cl
        LEFT JOIN users c ON cl.created_by = c.id
        LEFT JOIN users up ON cl.updated_by = up.id
        WHERE cl.id = %s""", (client_id,))
    client = cursor.fetchone()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return client


@router.post("/", response_model=ClientResponse, status_code=201)
def create_client(
    client: ClientCreate,
    db=Depends(get_db),
    current_user=Depends(require_role("superadmin", "admin"))
):
    cursor = db.cursor()

    # Verificar que el client_id no exista
    cursor.execute("SELECT id FROM clients WHERE client_id = %s", (client.client_id,))
    if cursor.fetchone():
        raise HTTPException(status_code=400, detail="Ya existe un cliente con ese client_id")

    # Verificar que el erp_type sea válido
    if client.erp_type not in ("ws", "connekta", "sap", "kubapp", "excel"):
        raise HTTPException(status_code=400, detail="erp_type inválido. Opciones: ws, connekta, sap, kubapp, excel")

    cursor.execute(
        """INSERT INTO clients (client_id, name, erp_type, created_by, updated_by)
        VALUES (%s, %s, %s, %s, %s) RETURNING *""",
        (client.client_id, client.name, client.erp_type, current_user["id"], current_user["id"])
    )
    new_client = cursor.fetchone()
    db.commit()
    return new_client


@router.put("/{client_id}", response_model=ClientResponse)
def update_client(
    client_id: int,
    client: ClientUpdate,
    db=Depends(get_db),
    current_user=Depends(require_role("superadmin", "admin"))
):
    cursor = db.cursor()

    cursor.execute("SELECT * FROM clients WHERE id = %s", (client_id,))
    existing = cursor.fetchone()
    if not existing:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    updates = {}
    if client.client_id is not None:
        cursor.execute("SELECT id FROM clients WHERE client_id = %s AND id != %s", (client.client_id, client_id))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Ya existe otro cliente con ese client_id")
        updates["client_id"] = client.client_id
    if client.name is not None:
        updates["name"] = client.name
    if client.erp_type is not None:
        if client.erp_type not in ("ws", "connekta", "sap", "kubapp", "excel"):
            raise HTTPException(status_code=400, detail="erp_type inválido. Opciones: ws, connekta, sap, kubapp, excel")
        updates["erp_type"] = client.erp_type
    if client.is_active is not None:
        updates["is_active"] = client.is_active

    if not updates:
        raise HTTPException(status_code=400, detail="No se enviaron campos para actualizar")

    updates["updated_by"] = current_user["id"]
    set_clause = ", ".join(f"{key} = %s" for key in updates)
    values = list(updates.values()) + [client_id]
    cursor.execute(f"UPDATE clients SET {set_clause} WHERE id = %s RETURNING *", values)
    updated_client = cursor.fetchone()
    db.commit()
    return updated_client


@router.delete("/{client_id}", status_code=204)
def delete_client(
    client_id: int,
    db=Depends(get_db),
    current_user=Depends(require_role("superadmin"))
):
    cursor = db.cursor()

    cursor.execute("SELECT id FROM clients WHERE id = %s", (client_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    # CASCADE elimina flows y executions automáticamente
    cursor.execute("DELETE FROM clients WHERE id = %s", (client_id,))
    db.commit()