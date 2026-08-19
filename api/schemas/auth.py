from pydantic import BaseModel

class LoginRequest(BaseModel):
    google_token: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict