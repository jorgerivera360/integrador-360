from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ClientCreate(BaseModel):
    client_id: str
    name: str
    erp_type: str


class ClientUpdate(BaseModel):
    client_id: Optional[str] = None
    name: Optional[str] = None
    erp_type: Optional[str] = None
    is_active: Optional[bool] = None


class ClientResponse(BaseModel):
    id: int
    client_id: str
    name: str
    erp_type: str
    is_active: bool
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True