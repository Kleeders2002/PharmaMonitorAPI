import os
from dotenv import load_dotenv
from zoneinfo import ZoneInfo

# Cargar variables de entorno
load_dotenv()

class Config:
    """Configuración centralizada de la aplicación"""

    # Timezone Configuration
    TIMEZONE = ZoneInfo("America/Caracas")  # UTC-4

    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:kleeders2002@localhost/PharmaMonitorDB")

    # JWT
    JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
    JWT_ALGORITHM = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 30

    # NodeMCU Configuration
    NODEMCU_IP = os.getenv("NODEMCU_IP", "192.168.0.117")
    NODEMCU_PORT = int(os.getenv("NODEMCU_PORT", "80"))
    NODEMCU_LED_ENDPOINT = os.getenv("NODEMCU_LED_ENDPOINT", "/led")
    NODEMCU_DATA_ENDPOINT = os.getenv("NODEMCU_DATA_ENDPOINT", "/sensor")

    # Environment
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    IS_PRODUCTION = ENVIRONMENT == "production"

    # CORS
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "").split(",") if os.getenv("CORS_ORIGINS") else [
        "http://localhost:3000",
        "http://localhost:19006",
        "http://localhost:8081",
    ]

    # Sensor Configuration
    USE_REAL_SENSORS = os.getenv("USE_REAL_SENSORS", "true").lower() == "true"
    SENSOR_STRICT_MODE = os.getenv("SENSOR_STRICT_MODE", "true").lower() == "true"

    @classmethod
    def get_nodemcu_url(cls, endpoint: str) -> str:
        """Construye la URL completa para el NodeMCU"""
        return f"http://{cls.NODEMCU_IP}:{cls.NODEMCU_PORT}{endpoint}"
