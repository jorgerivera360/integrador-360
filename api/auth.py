import os
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from api.dependencies import get_db


SECRET_KEY = os.getenv("JWT_SECRET_KEY", "integrador-360-secret-key-cambiar-en-produccion")
ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 24
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")

security = HTTPBearer()


def verify_google_token(token: str) -> dict:
    try:
        info = id_token.verify_oauth2_token(
            token,
            google_requests.Request(),
            GOOGLE_CLIENT_ID
        )
        return info
    except ValueError:
        raise HTTPException(status_code=401, detail="Token de Google inválido")


def create_jwt(user: dict) -> str:
    payload = {
        "sub": str(user["id"]),
        "email": user["email"],
        "role": user["role"],
        "exp": datetime.now(timezone.utc) + timedelta(hours=TOKEN_EXPIRE_HOURS),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db=Depends(get_db)
):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Token inválido")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")

    cursor = db.cursor()
    cursor.execute(
        "SELECT id, email, name, role, is_active FROM users WHERE id = %s",
        (user_id,)
    )
    user = cursor.fetchone()

    if not user or not user["is_active"]:
        raise HTTPException(status_code=401, detail="Usuario no encontrado o desactivado")

    return user


def require_role(*roles):
    def role_checker(current_user: dict = Depends(get_current_user)):
        if current_user["role"] not in roles:
            raise HTTPException(
                status_code=403,
                detail=f"Se requiere rol: {', '.join(roles)}"
            )
        return current_user
    return role_checker