from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select, create_engine
from adapters.api import usuario, auth, condicionalmacenamiento, productofarmaceutico, formafarmaceutica, productomonitoreado, datomonitoreo, alerta, registro, dashboard, perfil, nodemcu
# uploadimage temporalmente deshabilitado - requiere cloudinary
from adapters.db.sqlmodel_database import init_db, get_session
from core.models.rol import Rol
from core.models.formafarmaceutica import FormaFarmaceutica

app = FastAPI()

# Configuración de CORS
# Leer allowed origins desde variable de entorno o usar defaults
import os
cors_origins = os.getenv("CORS_ORIGINS", "").split(",")

# Si no hay variable configurada, usar defaults para desarrollo
if not cors_origins or cors_origins == [""]:
    cors_origins = [
        "http://localhost:3000",    # React frontend
        "http://localhost:19006",   # Expo web default
        "http://localhost:8081",    # Expo web alternate
        "http://localhost:19000",   # Expo web production
        "http://192.168.0.155:19006",  # Expo web en red local
        "http://192.168.0.155:8081",   # Expo web alternate en red
        "exp://192.168.0.155:8081",    # Expo Go en móvil
        "http://localhost:8000",        # Backend itself
        "https://pharmamonitorapi.onrender.com",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Set-Cookie"],
)

def create_default_roles(session: Session):
    roles = ["Administrador", "Usuario"]
    for rol in roles:
        if not session.exec(select(Rol).where(Rol.descripcion == rol)).first():
            session.add(Rol(descripcion=rol))
    session.commit()

def create_default_formas(session: Session):
    formas = ["Vacunas", "Insulina", "Hormonas", "Antibióticos sensibles", 
             "Medicamentos para el corazón", "Productos químicos sensibles",
             "Kits de diagnóstico", "Productos de terapia génica", "Otro"]
    for forma in formas:
        if not session.exec(select(FormaFarmaceutica).where(FormaFarmaceutica.descripcion == forma)).first():
            session.add(FormaFarmaceutica(descripcion=forma))
    session.commit()

@app.on_event("startup")
async def on_startup():
    init_db()

    # Crear datos iniciales con sesión dedicada
    from adapters.db.sqlmodel_database import engine
    with Session(engine) as session:
        create_default_roles(session)
        create_default_formas(session)

    print("✅ Backend iniciado - Esperando datos del NodeMCU en POST /nodemcu/data")
# Incluir routers
app.include_router(nodemcu.router)
app.include_router(usuario.router)
app.include_router(dashboard.router)
app.include_router(alerta.router)
app.include_router(condicionalmacenamiento.router)
app.include_router(productofarmaceutico.router)
app.include_router(productomonitoreado.router)
app.include_router(datomonitoreo.router)
app.include_router(formafarmaceutica.router)
app.include_router(registro.router)
# app.include_router(uploadimage.router)  # Temporalmente deshabilitado - requiere cloudinary
app.include_router(auth.router)
app.include_router(perfil.router)