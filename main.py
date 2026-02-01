import asyncio
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select, create_engine
from adapters.api import usuario, auth, condicionalmacenamiento, productofarmaceutico, formafarmaceutica, productomonitoreado, datomonitoreo, alerta, registro, dashboard, perfil
# uploadimage temporalmente deshabilitado - requiere cloudinary
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
    allow_origins=[
        "http://localhost:3000",    # React frontend
        "http://localhost:19006",   # Expo web default
        "http://localhost:8081",    # Expo web alternate
        "http://localhost:19000",   # Expo web production
        "http://192.168.0.155:19006",  # Expo web en red local
        "http://192.168.0.155:8081",   # Expo web alternate en red
        "exp://192.168.0.155:8081",    # Expo Go en móvil
        "http://localhost:8000",        # Backend itself
    ],
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
    
    # Iniciar generación de datos de forma asíncrona
    asyncio.create_task(background_data_processing())
    # Iniciar monitoreo de LED en tiempo real
    asyncio.create_task(background_led_monitoring())

async def background_data_processing():
    """Procesamiento en background para guardar datos en BD - Cada 60 segundos"""
    from adapters.db.sqlmodel_database import engine
    from adapters.arduino_adapter import generar_datos_reales_definitivo
    print("Iniciando procesamiento de datos (cada 60 segundos)")

    while True:
        try:
            with Session(engine) as session:
                # Modo estricto: NO genera datos falsos cuando el sensor falla
                datos_generador = generar_datos_reales_definitivo(session, strict_mode=True)
                await procesar_datos(datos_generador, session)
            await asyncio.sleep(60)  # Procesar cada 60 segundos
        except Exception as e:
            print(f"Error en procesamiento background: {e}")
            await asyncio.sleep(30)

async def background_led_monitoring():
    """Procesamiento en background para actualizar LED - Cada 5 segundos"""
    from services.led_service import monitorear_y_actualizar_led
    from adapters.db.sqlmodel_database import engine

    print("Iniciando monitoreo de LED (cada 5 segundos)")

    while True:
        try:
            with Session(engine) as session:
                await monitorear_y_actualizar_led(session)
            await asyncio.sleep(5)  # Actualizar LED cada 5 segundos
        except Exception as e:
            print(f"Error en monitoreo de LED: {e}")
            await asyncio.sleep(5)

# Incluir routers
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