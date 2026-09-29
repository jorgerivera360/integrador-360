import json
from fastapi import APIRouter, Depends, HTTPException
from api.dependencies import get_db
from api.auth import require_role
from api.schemas.sql_blocks import SqlBlockCreate, SqlBlockUpdate, SqlBlockResponse
from api.utils.sql_assembler import assemble_sql

router = APIRouter(prefix="/sql-blocks", tags=["SQL Blocks"])

VALID_BLOCK_TYPES = ("base", "campo", "filtro")


@router.get("/", response_model=list[SqlBlockResponse])
def get_sql_blocks(
    block_type: str = None,
    entity_type: str = None,
    is_active: bool = None,
    db=Depends(get_db),
    current_user=Depends(require_role("superadmin", "admin", "viewer"))
):
    cursor = db.cursor()
    query = "SELECT * FROM sql_blocks WHERE 1=1"
    params = []

    if block_type is not None:
        query += " AND block_type = %s"
        params.append(block_type)
    if entity_type is not None:
        query += " AND entity_types LIKE %s"
        params.append(f"%{entity_type}%")
    if is_active is not None:
        query += " AND is_active = %s"
        params.append(is_active)

    query += " ORDER BY block_type, sort_order, name"
    cursor.execute(query, params)
    return cursor.fetchall()


@router.get("/{block_id}", response_model=SqlBlockResponse)
def get_sql_block(
    block_id: int,
    db=Depends(get_db),
    current_user=Depends(require_role("superadmin", "admin", "viewer"))
):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM sql_blocks WHERE id = %s", (block_id,))
    block = cursor.fetchone()
    if not block:
        raise HTTPException(status_code=404, detail="Bloque SQL no encontrado")
    return block


@router.post("/", response_model=SqlBlockResponse, status_code=201)
def create_sql_block(
    block: SqlBlockCreate,
    db=Depends(get_db),
    current_user=Depends(require_role("superadmin", "admin"))
):
    cursor = db.cursor()

    if block.block_type not in VALID_BLOCK_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"block_type invalido. Opciones: {', '.join(VALID_BLOCK_TYPES)}"
        )

    cursor.execute(
        "SELECT id FROM sql_blocks WHERE name = %s AND block_type = %s",
        (block.name, block.block_type)
    )
    if cursor.fetchone():
        raise HTTPException(
            status_code=400,
            detail=f"Ya existe un bloque '{block.name}' de tipo '{block.block_type}'"
        )

    cursor.execute(
        """INSERT INTO sql_blocks
        (name, description, block_type, entity_types,
         select_fragment, join_fragment, group_by_fragment, where_fragment,
         variables, requires_block_id, sort_order, created_by, updated_by)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING *""",
        (
            block.name, block.description, block.block_type, block.entity_types,
            block.select_fragment, block.join_fragment,
            block.group_by_fragment, block.where_fragment,
            json.dumps(block.variables), block.requires_block_id, block.sort_order,
            current_user["id"], current_user["id"]
        )
    )
    new_block = cursor.fetchone()
    db.commit()
    return new_block


@router.put("/{block_id}", response_model=SqlBlockResponse)
def update_sql_block(
    block_id: int,
    block: SqlBlockUpdate,
    db=Depends(get_db),
    current_user=Depends(require_role("superadmin", "admin"))
):
    cursor = db.cursor()

    cursor.execute("SELECT * FROM sql_blocks WHERE id = %s", (block_id,))
    existing = cursor.fetchone()
    if not existing:
        raise HTTPException(status_code=404, detail="Bloque SQL no encontrado")

    updates = {}

    if block.name is not None:
        updates["name"] = block.name
    if block.description is not None:
        updates["description"] = block.description
    if block.block_type is not None:
        if block.block_type not in VALID_BLOCK_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"block_type invalido. Opciones: {', '.join(VALID_BLOCK_TYPES)}"
            )
        updates["block_type"] = block.block_type
    if block.entity_types is not None:
        updates["entity_types"] = block.entity_types
    if block.select_fragment is not None:
        updates["select_fragment"] = block.select_fragment
    if block.join_fragment is not None:
        updates["join_fragment"] = block.join_fragment
    if block.group_by_fragment is not None:
        updates["group_by_fragment"] = block.group_by_fragment
    if block.where_fragment is not None:
        updates["where_fragment"] = block.where_fragment
    if block.variables is not None:
        updates["variables"] = json.dumps(block.variables)
    if block.requires_block_id is not None:
        updates["requires_block_id"] = block.requires_block_id
    if block.sort_order is not None:
        updates["sort_order"] = block.sort_order
    if block.is_active is not None:
        updates["is_active"] = block.is_active

    if not updates:
        raise HTTPException(status_code=400, detail="No se enviaron campos para actualizar")

    check_name = updates.get("name", existing["name"])
    check_type = updates.get("block_type", existing["block_type"])
    cursor.execute(
        "SELECT id FROM sql_blocks WHERE name = %s AND block_type = %s AND id != %s",
        (check_name, check_type, block_id)
    )
    if cursor.fetchone():
        raise HTTPException(
            status_code=400,
            detail=f"Ya existe otro bloque '{check_name}' de tipo '{check_type}'"
        )

    updates["updated_by"] = current_user["id"]
    set_clause = ", ".join(f"{key} = %s" for key in updates)
    values = list(updates.values()) + [block_id]
    cursor.execute(f"UPDATE sql_blocks SET {set_clause} WHERE id = %s RETURNING *", values)
    updated_block = cursor.fetchone()

    db.commit()
    return updated_block


@router.delete("/{block_id}", status_code=200)
def delete_sql_block(
    block_id: int,
    db=Depends(get_db),
    current_user=Depends(require_role("superadmin"))
):
    cursor = db.cursor()

    cursor.execute("SELECT * FROM sql_blocks WHERE id = %s", (block_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Bloque SQL no encontrado")

    cursor.execute(
        "SELECT id, name FROM sql_blocks WHERE requires_block_id = %s",
        (block_id,)
    )
    dependientes = cursor.fetchall()
    if dependientes:
        nombres = ", ".join(d["name"] for d in dependientes)
        raise HTTPException(
            status_code=400,
            detail=f"No se puede eliminar: los siguientes bloques dependen de este: {nombres}"
        )

    cursor.execute("DELETE FROM sql_blocks WHERE id = %s", (block_id,))
    db.commit()
    return {"msg": "Bloque eliminado"}


@router.post("/preview")
def preview_sql(
    payload: dict,
    db=Depends(get_db),
    current_user=Depends(require_role("superadmin", "admin"))
):
    """
    Ensambla y retorna el SQL sin guardar. Para vista previa en el editor.

    Payload esperado:
    {
        "sql_base_id": 1,
        "sql_base_variables": {"compania": "1"},
        "sql_campos": [
            {"block_id": 5, "variables": {"valor": "19"}}
        ],
        "sql_filtros": [
            {"block_id": 10, "variables": {"dias": "1"}}
        ]
    }
    """
    base_id = payload.get("sql_base_id")
    if not base_id:
        raise HTTPException(status_code=400, detail="sql_base_id es obligatorio")

    block_ids = [base_id]
    campos_config = payload.get("sql_campos", [])
    filtros_config = payload.get("sql_filtros", [])

    for c in campos_config:
        if c.get("block_id"):
            block_ids.append(c["block_id"])
    for f in filtros_config:
        if f.get("block_id"):
            block_ids.append(f["block_id"])

    cursor = db.cursor()
    cursor.execute(
        "SELECT * FROM sql_blocks WHERE id = ANY(%s) AND is_active = true",
        (block_ids,)
    )
    blocks_by_id = {row["id"]: row for row in cursor.fetchall()}

    base_block = blocks_by_id.get(base_id)
    if not base_block:
        raise HTTPException(status_code=404, detail="Bloque base no encontrado o inactivo")

    base_block["variables_values"] = payload.get("sql_base_variables", {})

    campo_blocks = []
    for c in campos_config:
        block = blocks_by_id.get(c.get("block_id"))
        if block:
            campo_blocks.append({**block, "variables_values": c.get("variables", {})})

    filtro_blocks = []
    for f in filtros_config:
        block = blocks_by_id.get(f.get("block_id"))
        if block:
            filtro_blocks.append({**block, "variables_values": f.get("variables", {})})

    sql = assemble_sql(base_block, campo_blocks, filtro_blocks)
    return {"sql": sql}
