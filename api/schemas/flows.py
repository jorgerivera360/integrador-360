from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class FlowCreate(BaseModel):
    flow_name: str
    flow_type: str
    flow_config: dict = {}
    schedule_cron: Optional[str] = None


class FlowUpdate(BaseModel):
    flow_name: Optional[str] = None
    flow_type: Optional[str] = None
    flow_config: Optional[dict] = None
    schedule_cron: Optional[str] = None
    is_active: Optional[bool] = None


class FlowResponse(BaseModel):
    id: int
    client_id: int
    flow_name: str
    flow_type: str
    flow_config: dict
    schedule_cron: Optional[str] = None
    is_active: bool
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True