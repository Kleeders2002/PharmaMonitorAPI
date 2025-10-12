import random
import asyncio
import aiohttp
from datetime import datetime
from typing import AsyncGenerator, Optional
from sqlmodel import select
from core.models.condicionalmacenamiento import CondicionAlmacenamiento
from core.models.productomonitoreado import ProductoMonitoreado
from core.models.datomonitoreo import DatoMonitoreo
from core.models.productofarmaceutico import ProductoFarmaceutico

class SensorDataManager:
    def __init__(self, nodemcu_ip: str = None, use_real_data: bool = True):
        self.nodemcu_ip = nodemcu_ip
        self.use_real_data = use_real_data
        self.last_sensor_data = None
        self.sensor_timeout = 30  # segundos
        
    async def get_sensor_data(self) -> Optional[dict]:
        """Obtiene datos del sensor NodeMCU via HTTP"""
        if not self.use_real_data or not self.nodemcu_ip:
            return None
            
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"http://{self.nodemcu_ip}/sensor", timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.last_sensor_data = {
                            'temperatura': data.get('temperatura'),
                            'humedad': data.get('humedad'),
                            'timestamp': datetime.now()
                        }
                        return self.last_sensor_data
        except Exception as e:
            print(f"Error al obtener datos del sensor: {e}")
            return None
    
    def is_sensor_data_fresh(self) -> bool:
        """Verifica si los datos del sensor son recientes"""
        if not self.last_sensor_data:
            return False
        
        time_diff = datetime.now() - self.last_sensor_data['timestamp']
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
sensor_manager = SensorDataManager(
    nodemcu_ip="192.168.0.117", 
    use_real_data=True
)

async def generar_datos_reales(session) -> AsyncGenerator[DatoMonitoreo, None]:
    """Versión actualizada que usa datos reales del NodeMCU"""
    while True:
        # Obtener datos del sensor
        sensor_data = await sensor_manager.get_sensor_data()
        
        # Filtrar solo productos con monitoreo activo
        stmt = (
            select(ProductoMonitoreado, CondicionAlmacenamiento)
            .join(ProductoFarmaceutico, ProductoMonitoreado.id_producto == ProductoFarmaceutico.id)
            .join(CondicionAlmacenamiento, ProductoFarmaceutico.id_condicion == CondicionAlmacenamiento.id)
            .where(ProductoMonitoreado.fecha_finalizacion_monitoreo == None)
        )
        
        result = session.exec(stmt)
        datos = result.all()
        
        for pm, condicion in datos:
            if sensor_data and sensor_manager.is_sensor_data_fresh():
                # Usar datos reales del sensor
                yield DatoMonitoreo(
                    id_producto_monitoreado=pm.id,
                    fecha=datetime.now(),
                    temperatura=sensor_data['temperatura'],
                    humedad=sensor_data['humedad'],
                    # Para lux y presión, usar valores por defecto o simulados
                    lux=random.uniform(condicion.lux_min, condicion.lux_max * 1.005),
                    presion=random.uniform(condicion.presion_min, condicion.presion_max)
                )
            else:
                # Usar datos de respaldo si el sensor no está disponible
                fallback_data = sensor_manager.generate_fallback_data(condicion)
                yield DatoMonitoreo(
                    id_producto_monitoreado=pm.id,
                    fecha=datetime.now(),
                    temperatura=fallback_data['temperatura'],
                    humedad=fallback_data['humedad'],
                    lux=fallback_data['lux'],
                    presion=fallback_data['presion']
                )
        
        await asyncio.sleep(5)

# Función híbrida que permite alternar entre simulado y real
async def generar_datos_hibridos(session, use_real_sensor: bool = True) -> AsyncGenerator[DatoMonitoreo, None]:
    """Función que permite usar datos reales o simulados según configuración"""
    if use_real_sensor:
        async for dato in generar_datos_reales(session):
            yield dato
    else:
        async for dato in generar_datos_simulados(session):
            yield dato

# Mantener la función original para compatibilidad
async def generar_datos_simulados(session) -> AsyncGenerator[DatoMonitoreo, None]:
    """Función original con datos simulados"""
    while True:
        stmt = (
            select(ProductoMonitoreado, CondicionAlmacenamiento)
            .join(ProductoFarmaceutico, ProductoMonitoreado.id_producto == ProductoFarmaceutico.id)
            .join(CondicionAlmacenamiento, ProductoFarmaceutico.id_condicion == CondicionAlmacenamiento.id)
            .where(ProductoMonitoreado.fecha_finalizacion_monitoreo == None)
        )
       
        result = session.exec(stmt)
        datos = result.all()
        
        for pm, condicion in datos:
            yield DatoMonitoreo(
                id_producto_monitoreado=pm.id,
                fecha=datetime.now(),
                temperatura=random.uniform(condicion.temperatura_min, condicion.temperatura_max * 1.005),
                humedad=random.uniform(condicion.humedad_min, condicion.humedad_max * 1.005),
                lux=random.uniform(condicion.lux_min, condicion.lux_max * 1.005),
                presion=random.uniform(condicion.presion_min, condicion.presion_max)
            )
       
        await asyncio.sleep(5)