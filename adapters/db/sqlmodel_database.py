from sqlmodel import SQLModel, create_engine, Session
import os
from dotenv import load_dotenv

load_dotenv()

#DATABASE_URL = "postgresql://neondb_owner:npg_3ucRs2tijLMp@ep-autumn-morning-ad6m1upg-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require"

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:kleeders2002@localhost/PharmaMonitorDB"
)

# ✅ Configura el pool correctamente para peticiones concurrentes
engine = create_engine(
    DATABASE_URL,
    echo=False,  # Desactivado en producción
    pool_size=10,          # ⭐ Número de conexiones permanentes en el pool
    max_overflow=20,       # ⭐ Conexiones adicionales temporales
    pool_pre_ping=True,    # Verifica conexiones antes de usarlas
    pool_recycle=3600,     # Recicla conexiones cada hora (no cada 5 min)
    pool_timeout=30,       # ⭐ Timeout para obtener conexión del pool
)

def init_db():
    SQLModel.metadata.create_all(engine)

# ✅ Asegúrate que cada request tiene su propia sesión
def get_session():
    with Session(engine) as session:
        try:
            yield session
            session.commit()  # Commit automático si todo salió bien
        except Exception:
            session.rollback()  # Rollback en caso de error
            raise
        # El 'with' se encarga del close automáticamente