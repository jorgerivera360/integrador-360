import json
from fastapi import APIRouter, Depends, HTTPException
from api.dependencies import get_db
from api.auth import require_role
from api.schemas.wms_fields import WmsFieldCreate, WmsFieldUpdate, WmsFieldResponse

router = APIRouter(prefix="/wms-fields", tags=["WMS Fields"])

VALID_UBICACIONES = ("cabecera", "linea")
VALID_TIPOS = ("texto", "entero", "decimal", "booleano")
VALID_MODELOS = ("sale.order", "purchase.order", "stock.picking")


@router.get("/", response_model=list[WmsFieldResponse])
def get_wms_fields(
    is_active: bool = None,
    modelo: str = None,
    db=Depends(get_db),
    current_user=Depends(require_role("superadmin", "admin", "viewer"))
):
    cursor = db.cursor()
    query = "SELECT * FROM wms_field_mappings WHERE 1=1"
    params = []

    if is_active is not None:
        query += " AND is_active = %s"
        params.append(is_active)
    if modelo is not None:
        query += " AND %s = ANY(modelos)"
        params.append(modelo)

    query += " ORDER BY ubicacion, campo_origen"
    cursor.execute(query, params)
    return cursor.fetchall()


@router.get("/{field_id}", response_model=WmsFieldResponse)
def get_wms_field(
    field_id: int,
    db=Depends(get_db),
    current_user=Depends(require_role("superadmin", "admin", "viewer"))
):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM wms_field_mappings WHERE id = %s", (field_id,))
    field = cursor.fetchone()
    if not field:
        raise HTTPException(status_code=404, detail="Campo WMS no encontrado")
    return field


@router.post("/", response_model=WmsFieldResponse, status_code=201)
def create_wms_field(
    field: WmsFieldCreate,
    db=Depends(get_db),
    current_user=Depends(require_role("superadmin", "admin"))
):
    cursor = db.cursor()

    if field.ubicacion not in VALID_UBICACIONES:
        raise HTTPException(
            status_code=400,
            detail=f"ubicacion invalida. Opciones: {', '.join(VALID_UBICACIONES)}"
        )
    if field.tipo_valor not in VALID_TIPOS:
        raise HTTPException(
            status_code=400,
            detail=f"tipo_valor invalido. Opciones: {', '.join(VALID_TIPOS)}"
        )
    for m in field.modelos:
        if m not in VALID_MODELOS:
            raise HTTPException(
                status_code=400,
                detail=f"modelo invalido '{m}'. Opciones: {', '.join(VALID_MODELOS)}"
            )

    # Verificar unicidad
    cursor.execute(
        """SELECT id FROM wms_field_mappings
           WHERE campo_origen = %s AND campo_destino = %s AND ubicacion = %s""",
        (field.campo_origen, field.campo_destino, field.ubicacion)
    )
    if cursor.fetchone():
        raise HTTPException(
            status_code=400,
            detail=f"Ya existe un mapeo '{field.campo_origen}' -> '{field.campo_destino}' en {field.ubicacion}"
        )

    cursor.execute(
        """INSERT INTO wms_field_mappings
           (campo_origen, campo_destino, ubicacion, modelos, tipo_valor,
            valor_default, descripcion, created_by, updated_by)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
           RETURNING *""",
        (
            field.campo_origen, field.campo_destino, field.ubicacion,
            field.modelos, field.tipo_valor, field.valor_default,
            field.descripcion,
            current_user["id"], current_user["id"],
        )
    )
    db.commit()
    return cursor.fetchone()


@router.put("/{field_id}", response_model=WmsFieldResponse)
def update_wms_field(
    field_id: int,
    field: WmsFieldUpdate,
    db=Depends(get_db),
    current_user=Depends(require_role("superadmin", "admin"))
):
    cursor = db.cursor()

    cursor.execute("SELECT * FROM wms_field_mappings WHERE id = %s", (field_id,))
    existente = cursor.fetchone()
    if not existente:
        raise HTTPException(status_code=404, detail="Campo WMS no encontrado")

    if field.ubicacion is not None and field.ubicacion not in VALID_UBICACIONES:
        raise HTTPException(status_code=400, detail=f"ubicacion invalida")
    if field.tipo_valor is not None and field.tipo_valor not in VALID_TIPOS:
        raise HTTPException(status_code=400, detail=f"tipo_valor invalido")
    if field.modelos is not None:
        for m in field.modelos:
            if m not in VALID_MODELOS:
                raise HTTPException(status_code=400, detail=f"modelo invalido '{m}'")

    # Construir SET dinámico
    updates = []
    params = []
    campos = field.model_dump(exclude_unset=True)
    for campo, valor in campos.items():
        if campo == "modelos":
            updates.append(f"{campo} = %s")
            params.append(valor)
        else:
            updates.append(f"{campo} = %s")
            params.append(valor)

    if not updates:
        return existente

    updates.append("updated_by = %s")
    params.append(current_user["id"])
    params.append(field_id)

    cursor.execute(
        f"UPDATE wms_field_mappings SET {', '.join(updates)} WHERE id = %s RETURNING *",
        params
    )
    db.commit()
    return cursor.fetchone()


@router.delete("/{field_id}", status_code=204)
def delete_wms_field(
    field_id: int,
    db=Depends(get_db),
    current_user=Depends(require_role("superadmin"))
):
    cursor = db.cursor()
    cursor.execute("SELECT id FROM wms_field_mappings WHERE id = %s", (field_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Campo WMS no encontrado")

    cursor.execute("DELETE FROM wms_field_mappings WHERE id = %s", (field_id,))
    db.commit()
