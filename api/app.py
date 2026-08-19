import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from api.routes.auth import router as auth_router
from api.routes.users import router as users_router
from api.routes.clients import router as clients_router

load_dotenv()

app = FastAPI(
    title="Integrador 360 API",
    description="API para administrar usuarios, clientes, flows y ejecuciones del integrador ERP → Odoo WMS",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "integrador-360-api"}

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(clients_router)