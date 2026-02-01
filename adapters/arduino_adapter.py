"""
Adapter para manejo de sensores del NodeMCU.

Arquitectura actual:
- NodeMCU envía datos al backend vía POST /nodemcu/data
- Backend recibe datos y actualiza estado de sensores
- No se hacen peticiones HTTP salientes desde el backend
"""
import random
import asyncio
import aiohttp
from datetime import datetime
from typing import Optional
from sqlmodel import select
from core.models.condicionalmacenamiento import CondicionAlmacenamiento
from core.models.productomonitoreado import ProductoMonitoreado
from core.models.datomonitoreo import DatoMonitoreo
from core.models.productofarmaceutico import ProductoFarmaceutico
from core.utils.datetime_utils import get_caracas_now


class SensorStatus:
    """Rastrea el estado de cada sensor individualmente"""
    def __init__(self):
        self.temperatura_ok = True
        self.humedad_ok = True
        self.lux_ok = True
        self.presion_ok = True

    def get_failed_sensors(self) -> list[str]:
        """Retorna lista de sensores que fallaron"""
        failed = []
        if not self.temperatura_ok:
            failed.append("temperatura")
        if not self.humedad_ok:
            failed.append("humedad")
        if not self.lux_ok:
            failed.append("lux")
        if not self.presion_ok:
            failed.append("presion")
        return failed


class SensorDataManager:
    def __init__(self, nodemcu_ip: str = None, use_real_data: bool = True):
        self.nodemcu_ip = nodemcu_ip
        self.use_real_data = use_real_data
        self.last_sensor_data = None
        self.sensor_timeout = 30  # segundos
        self.sensor_status = SensorStatus()  # Rastrear estado individual

    async def get_sensor_data(self) -> Optional[dict]:
        """
        Obtiene datos del sensor NodeMCU via HTTP.

        NOTA: Esta función ya NO se usa en la nueva arquitectura.
        Se mantiene por compatibilidad pero podría eliminarse en el futuro.
        """
        if not self.use_real_data or not self.nodemcu_ip:
            self.sensor_status.temperatura_ok = False
            self.sensor_status.humedad_ok = False
            self.sensor_status.lux_ok = False
            self.sensor_status.presion_ok = False
            return None

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"http://{self.nodemcu_ip}/sensor", timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()

                        # Verificar cada sensor independientemente
                        temp = data.get('temperatura')
                        hum = data.get('humedad')
                        lux = data.get('lux')
                        presion = data.get('presion')

                        # Marcar estado de cada sensor
                        self.sensor_status.temperatura_ok = temp is not None
                        self.sensor_status.humedad_ok = hum is not None
                        self.sensor_status.lux_ok = lux is not None
                        self.sensor_status.presion_ok = presion is not None

                        self.last_sensor_data = {
                            'temperatura': temp,
                            'humedad': hum,
                            'lux': lux,
                            'presion': presion,
                            'timestamp': get_caracas_now()
                        }
                        return self.last_sensor_data
                    else:
                        # NodeMCU respondió pero con error
                        print(f"⚠️ NodeMCU respondió con status {response.status}")
                        self.sensor_status.temperatura_ok = False
                        self.sensor_status.humedad_ok = False
                        self.sensor_status.lux_ok = False
                        self.sensor_status.presion_ok = False
                        return None
        except Exception as e:
            print(f"⚠️ Error conectando al NodeMCU: {e}")
            self.sensor_status.temperatura_ok = False
            self.sensor_status.humedad_ok = False
            self.sensor_status.lux_ok = False
            self.sensor_status.presion_ok = False
            return None

    def get_sensor_status(self) -> SensorStatus:
        """Retorna el estado actual de todos los sensores"""
        return self.sensor_status

    def is_sensor_data_fresh(self) -> bool:
        """Verifica si los datos del sensor son recientes"""
        if not self.last_sensor_data:
            return False

        time_diff = get_caracas_now() - self.last_sensor_data['timestamp']
        return time_diff.total_seconds() < self.sensor_timeout

    def generate_fallback_data(self, condicion: CondicionAlmacenamiento) -> dict:
        """Genera datos de respaldo cuando el sensor no está disponible"""
        return {
            'temperatura': random.uniform(condicion.temperatura_min, condicion.temperatura_max * 1.005),
            'humedad': random.uniform(condicion.humedad_min, condicion.humedad_max * 1.005),
            'lux': random.uniform(condicion.lux_min, condicion.lux_max * 1.005),
            'presion': random.uniform(condicion.presion_min, condicion.presion_max)
        }


# Instancia global del gestor de sensores
import os
from dotenv import load_dotenv

load_dotenv()

sensor_manager = SensorDataManager(
    nodemcu_ip=os.getenv("NODEMCU_IP", "192.168.0.117"),
    use_real_data=os.getenv("USE_REAL_SENSORS", "true").lower() == "true"
)
