from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class SqlBlockCreate(BaseModel):
    name: str
    description: str = ""
    block_type: str  # base, campo, filtro
    entity_types: str  # CSV: "items", "items,customer,supplier", etc.
    select_fragment: str = ""
    join_fragment: str = ""
    group_by_fragment: str = ""
    where_fragment: str = ""
    variables: list = []
    requires_block_id: Optional[int] = None
    sort_order: int = 0


class SqlBlockUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    block_type: Optional[str] = None
    entity_types: Optional[str] = None
    select_fragment: Optional[str] = None
    join_fragment: Optional[str] = None
    group_by_fragment: Optional[str] = None
    where_fragment: Optional[str] = None
    variables: Optional[list] = None
    requires_block_id: Optional[int] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class SqlBlockResponse(BaseModel):
    id: int
    name: str
    description: str
    block_type: str
    entity_types: str
    select_fragment: str
    join_fragment: str
    group_by_fragment: str
    where_fragment: str
    variables: list
    requires_block_id: Optional[int] = None
    sort_order: int
    is_active: bool
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
