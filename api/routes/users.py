from fastapi import APIRouter, Depends, HTTPException
from api.dependencies import get_db
from api.auth import require_role
from api.schemas.users import UserCreate, UserUpdate, UserResponse

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/", response_model=list[UserResponse])
def get_users(
    is_active: bool = None,
    db=Depends(get_db),
    current_user=Depends(require_role("superadmin"))
):
    cursor = db.cursor()
    if is_active is not None:
        cursor.execute("SELECT * FROM users WHERE is_active = %s ORDER BY id", (is_active,))
    else:
        cursor.execute("SELECT * FROM users ORDER BY id")
    return cursor.fetchall()


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db=Depends(get_db),
    current_user=Depends(require_role("superadmin"))
):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
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
        "INSERT INTO users (email, name, role) VALUES (%s, %s, %s) RETURNING *",
        (user.email, user.name, user.role)
    )
    new_user = cursor.fetchone()
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

    # Armar query dinámico
    set_clause = ", ".join(f"{key} = %s" for key in updates)
    values = list(updates.values()) + [user_id]
    cursor.execute(f"UPDATE users SET {set_clause} WHERE id = %s RETURNING *", values)
    updated_user = cursor.fetchone()
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

    cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
    db.commit()