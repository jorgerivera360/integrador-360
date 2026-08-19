from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ExecutionResponse(BaseModel):
    id: int
    flow_id: int
    started_at: datetime
    finished_at: Optional[datetime] = None
    status: str
    result: Optional[dict] = None
    error_message: Optional[str] = None
    triggered_by: str
    triggered_user: Optional[int] = None

    class Config:
        from_attributes = True


class ExecuteRequest(BaseModel):
    triggered_by: str = "manual"