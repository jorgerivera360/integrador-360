import os
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from api.dependencies import get_db
from api.auth import require_role

router = APIRouter(tags=["Excel"])

EXCEL_BASE_PATH = "/etc/integrador/excel"
TIPOS_VALIDOS = ("productos", "clientes", "proveedores", "entradas", "salidas")


@router.post("/clients/{client_id}/upload-excel")
def upload_excel(
    client_id: int,
    tipo: str = Form(...),
    archivo: UploadFile = File(...),
    db=Depends(get_db),
    current_user=Depends(require_role("superadmin", "admin"))
):
    if tipo not in TIPOS_VALIDOS:
        raise HTTPException(status_code=400, detail=f"Tipo no válido. Válidos: {list(TIPOS_VALIDOS)}")

    if not archivo.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="El archivo debe ser .xlsx o .xls")

    cursor = db.cursor()
    cursor.execute("SELECT client_id FROM clients WHERE id = %s", (client_id,))
    cliente = cursor.fetchone()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    slug = cliente["client_id"]
    carpeta = os.path.join(EXCEL_BASE_PATH, slug)
    os.makedirs(carpeta, exist_ok=True)

    nombre_archivo = f"{slug}-{tipo}.xlsx"
    ruta = os.path.join(carpeta, nombre_archivo)

    contenido = archivo.file.read()
    with open(ruta, "wb") as f:
        f.write(contenido)

    tamano = len(contenido)

    return {
        "msg": "Archivo cargado",
        "archivo": nombre_archivo,
        "tamano": tamano,
        "ruta": ruta,
    }


@router.get("/clients/{client_id}/excel-files")
def get_excel_files(
    client_id: int,
    db=Depends(get_db),
    current_user=Depends(require_role("superadmin", "admin", "viewer"))
):
    cursor = db.cursor()
    cursor.execute("SELECT client_id FROM clients WHERE id = %s", (client_id,))
    cliente = cursor.fetchone()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    slug = cliente["client_id"]
    carpeta = os.path.join(EXCEL_BASE_PATH, slug)

    archivos = []
    for tipo in TIPOS_VALIDOS:
        nombre = f"{slug}-{tipo}.xlsx"
        ruta = os.path.join(carpeta, nombre)
        if os.path.exists(ruta):
            stat = os.stat(ruta)
            archivos.append({
                "tipo": tipo,
                "archivo": nombre,
                "tamano": stat.st_size,
                "fecha": stat.st_mtime,
            })

    return archivos