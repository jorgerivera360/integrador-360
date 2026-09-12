"""
Schemas de credenciales — Pydantic models para onboarding de clientes
Responsabilidades:
- Validación de credenciales ERP por tipo (WS, Connekta, SAP)
- Validación de credenciales Odoo
- Request body para test de conexión con credenciales del formulario
- Request body para guardar credenciales en GCP
Fase: 9-10 — Frontend (Onboarding)
"""
from typing import Optional
from pydantic import BaseModel


# --- Credenciales Odoo (siempre iguales) ---

class OdooCredentials(BaseModel):
    url: str
    database: str
    usuario: str
    clave: str


# --- Credenciales ERP por tipo ---

class ErpCredentialsWS(BaseModel):
    url: str
    conexion: str
    compania: str
    usuario: str
    clave: str
    proveedor: str
    proxy_host: Optional[str] = None
    proxy_port: Optional[str] = None


class ErpCredentialsConnekta(BaseModel):
    url: str
    urlqa: Optional[str] = ""
    idcompania: str
    connikey: str
    connitoken: str


class ErpCredentialsSAP(BaseModel):
    url: str
    compania: str
    usuario: str
    clave: str


class SshTunnelConfig(BaseModel):
    ssh_enabled: bool = False
    ssh_host: Optional[str] = None
    ssh_port: int = 22
    ssh_user: Optional[str] = None
    ssh_key_path: Optional[str] = None
    ssh_password: Optional[str] = None

# --- Mapeo tipo → schema para validación dinámica ---

ERP_CREDENTIAL_SCHEMAS = {
    "ws": ErpCredentialsWS,
    "connekta": ErpCredentialsConnekta,
    "sap": ErpCredentialsSAP,
}


# --- Request: guardar credenciales ---

class CredentialsSaveRequest(BaseModel):
    erp: dict
    odoo: OdooCredentials


# --- Request: test de conexión con credenciales del formulario ---

class TestConnectionRequest(BaseModel):
    erp: Optional[dict] = None
    odoo: Optional[OdooCredentials] = None