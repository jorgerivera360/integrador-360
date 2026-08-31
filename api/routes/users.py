import json
from fastapi import APIRouter, Depends, HTTPException
from api.dependencies import get_db
from api.auth import require_role
from api.schemas.users import UserCreate, UserUpdate, UserResponse

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/", response_model=list[UserResponse])
def get_users(
    search: str = None,
    role: str = None,
    is_active: bool = None,
    db=Depends(get_db),
    current_user=Depends(require_role("superadmin"))
):
    cursor = db.cursor()
    query = """SELECT u.*,
                c.name AS created_by_name,
                up.name AS updated_by_name
        FROM users u
        LEFT JOIN users c ON u.created_by = c.id
        LEFT JOIN users up ON u.updated_by = up.id
        WHERE 1=1"""
    params = []

    if search:
          query += " AND (u.name ILIKE %s OR u.email ILIKE %s)"
          params.extend([f"%{search}%", f"%{search}%"])

    if role:
        if role not in ("superadmin", "admin", "viewer"):
            raise HTTPException(status_code=400, detail="Rol inválido. Opciones: superadmin, admin, viewer")
        query += " AND u.role = %s"
        params.append(role)

    if is_active is not None:
        query += " AND u.is_active = %s"
        params.append(is_active)

    query += " ORDER BY u.id"
    cursor.execute(query, params)
    return cursor.fetchall()


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db=Depends(get_db),
    current_user=Depends(require_role("superadmin"))
):
    cursor = db.cursor()
    cursor.execute("""SELECT u.*,
            c.name AS created_by_name,
            up.name AS updated_by_name
        FROM users u
        LEFT JOIN users c ON u.created_by = c.id
        LEFT JOIN users up ON u.updated_by = up.id
        WHERE u.id = %s""", (user_id,))
    user = cursor.fetchone()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user


@router.post("/", response_model=UserResponse, status_code=201)
def create_user(
    user: UserCreate,
    db=Depends(get_db),
    current_user=Depends(require_role("superadmin"))
):
    cursor = db.cursor()

    # Verificar que el email no exista
    cursor.execute("SELECT id FROM users WHERE email = %s", (user.email,))
    if cursor.fetchone():
        raise HTTPException(status_code=400, detail="Ya existe un usuario con ese email")

    # Verificar que el rol sea válido
    if user.role not in ("superadmin", "admin", "viewer"):
        raise HTTPException(status_code=400, detail="Rol inválido. Opciones: superadmin, admin, viewer")

    cursor.execute(
        "INSERT INTO users (email, name, role, created_by) VALUES (%s, %s, %s, %s) RETURNING *",
        (user.email, user.name, user.role, current_user["id"])
    )
    new_user = cursor.fetchone()
    cursor.execute(
        """INSERT INTO change_history
        (table_name, record_id, action, changed_fields, changed_by)
        VALUES ('users', %s, 'create', %s, %s)""",
        (new_user["id"], json.dumps({"email": user.email, "name": user.name, "role": user.role}), current_user["id"])
    )
    db.commit()
    return new_user


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user: UserUpdate,
    db=Depends(get_db),
    current_user=Depends(require_role("superadmin"))
):
    cursor = db.cursor()

    # Verificar que el usuario exista
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    existing = cursor.fetchone()
    if not existing:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # Construir SET dinámico solo con los campos que vienen
    updates = {}
    if user.email is not None:
        # Verificar que el nuevo email no lo tenga otro usuario
        cursor.execute("SELECT id FROM users WHERE email = %s AND id != %s", (user.email, user_id))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Ya existe otro usuario con ese email")
        updates["email"] = user.email
    if user.name is not None:
        updates["name"] = user.name
    if user.role is not None:
        if user.role not in ("superadmin", "admin", "viewer"):
            raise HTTPException(status_code=400, detail="Rol inválido. Opciones: superadmin, admin, viewer")
        updates["role"] = user.role
    if user.is_active is not None:
        updates["is_active"] = user.is_active

    if not updates:
        raise HTTPException(status_code=400, detail="No se enviaron campos para actualizar")
    
    updates["updated_by"] = current_user["id"]
    # Armar query dinámico
    set_clause = ", ".join(f"{key} = %s" for key in updates)
    values = list(updates.values()) + [user_id]
    cursor.execute(f"UPDATE users SET {set_clause} WHERE id = %s RETURNING *", values)
    updated_user = cursor.fetchone()
    previous_values = {k: str(existing[k]) for k in updates if k != "updated_by"}
    cursor.execute(
        """INSERT INTO change_history
        (table_name, record_id, action, changed_fields, previous_values, changed_by)
        VALUES ('users', %s, 'update', %s, %s, %s)""",
        (user_id, json.dumps({k: v for k, v in updates.items() if k != "updated_by"}),
        json.dumps(previous_values), current_user["id"])
    )
    db.commit()
    return updated_user


@router.delete("/{user_id}", status_code=204)
def delete_user(
    user_id: int,
    db=Depends(get_db),
    current_user=Depends(require_role("superadmin"))
):
    cursor = db.cursor()

    # No puede eliminarse a sí mismo
    if current_user["id"] == user_id:
        raise HTTPException(status_code=400, detail="No puedes eliminarte a ti mismo")

    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    existing = cursor.fetchone()
    if not existing:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    cursor.execute(
        """INSERT INTO change_history
        (table_name, record_id, action, previous_values, changed_by)
        VALUES ('users', %s, 'delete', %s, %s)""",
        (user_id, json.dumps({"email": existing["email"], "name": existing["name"], "role": existing["role"]}), current_user["id"])
    )

    cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
    db.commit()