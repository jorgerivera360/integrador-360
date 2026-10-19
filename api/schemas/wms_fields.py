from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class WmsFieldCreate(BaseModel):
    campo_origen: str
    campo_destino: str
    ubicacion: str  # 'cabecera' o 'linea'
    modelos: list[str]  # ['sale.order', 'stock.picking']
    tipo_valor: str = 'texto'  # 'texto', 'entero', 'decimal', 'booleano'
    valor_default: Optional[str] = None
    descripcion: str = ''


class WmsFieldUpdate(BaseModel):
    campo_origen: Optional[str] = None
    campo_destino: Optional[str] = None
    ubicacion: Optional[str] = None
    modelos: Optional[list[str]] = None
    tipo_valor: Optional[str] = None
    valor_default: Optional[str] = None
    descripcion: Optional[str] = None
    is_active: Optional[bool] = None


class WmsFieldResponse(BaseModel):
    id: int
    campo_origen: str
    campo_destino: str
    ubicacion: str
    modelos: list[str]
    tipo_valor: str
    valor_default: Optional[str]
    descripcion: str
    is_active: bool
    created_by: Optional[int]
    updated_by: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
