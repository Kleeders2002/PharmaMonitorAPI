import asyncio
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select
from adapters.api import usuario, auth, condicionalmacenamiento, uploadimage, productofarmaceutico, formafarmaceutica, productomonitoreado, datomonitoreo, alerta, registro, dashboard, perfil
from adapters.db.sqlmodel_database import init_db, get_session
from adapters.simulated_adapter import generar_datos_simulados
from adapters.arduino_adapter import generar_datos_hibridos
from services.data_service import procesar_datos
from core.models.rol import Rol
from core.models.formafarmaceutica import FormaFarmaceutica

app = FastAPI()

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
    
    # Crear datos iniciales
    with next(get_session()) as session:
        create_default_roles(session)
        create_default_formas(session)
    
    # Iniciar generación de datos
    session = next(get_session())
    datos_generador = generar_datos_hibridos(session)
    asyncio.create_task(procesar_datos(datos_generador, session))

# Incluir routers
app.include_router(usuario.router)
app.include_router(alerta.router)
app.include_router(condicionalmacenamiento.router)
app.include_router(productofarmaceutico.router)
app.include_router(productomonitoreado.router)
app.include_router(datomonitoreo.router)
app.include_router(formafarmaceutica.router)
app.include_router(registro.router)
app.include_router(uploadimage.router)
app.include_router(dashboard.router)
app.include_router(auth.router)
app.include_router(perfil.router)