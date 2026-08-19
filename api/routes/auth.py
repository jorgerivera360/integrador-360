from fastapi import APIRouter, Depends, HTTPException
from api.dependencies import get_db
from api.auth import verify_google_token, create_jwt, get_current_user
from api.schemas.auth import LoginRequest, LoginResponse

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, db=Depends(get_db)):
    # 1. Verificar el token de Google
    google_info = verify_google_token(request.google_token)
    email = google_info.get("email", "")

    # 2. Verificar que sea @360software.com.co
    if not email.endswith("@360software.com.co"):
        raise HTTPException(status_code=403, detail="Solo cuentas @360software.com.co")

    # 3. Buscar el usuario en la BD
    cursor = db.cursor()
    cursor.execute(
        "SELECT id, email, name, role, is_active FROM users WHERE email = %s",
        (email,)
    )
    user = cursor.fetchone()

    if not user:
        raise HTTPException(status_code=403, detail="Usuario no registrado en el sistema")

    if not user["is_active"]:
        raise HTTPException(status_code=403, detail="Usuario desactivado")

    # 4. Actualizar last_login
    cursor.execute(
        "UPDATE users SET last_login = NOW() WHERE id = %s",
        (user["id"],)
    )
    db.commit()

    # 5. Generar JWT propio
    access_token = create_jwt(user)

    return LoginResponse(
        access_token=access_token,
        user=dict(user)
    )


@router.get("/me")
def me(current_user: dict = Depends(get_current_user)):
    return current_user