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
        self.sensor_status = SensorStatus()  # Nuevo: rastrear estado individual

    async def get_sensor_data(self) -> Optional[dict]:
        """
        Obtiene datos del sensor NodeMCU via HTTP.
        Retorna diccionario con los valores disponibles.
        Marca como fallados solo los sensores específicos que no respondan.
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
                            'timestamp': datetime.now()
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
import os
from dotenv import load_dotenv

load_dotenv()

sensor_manager = SensorDataManager(
    nodemcu_ip=os.getenv("NODEMCU_IP", "192.168.0.117"),
    use_real_data=os.getenv("USE_REAL_SENSORS", "true").lower() == "true"
)

async def generar_datos_reales(session, strict_mode: bool = True) -> AsyncGenerator[Optional[DatoMonitoreo], None]:
    """
    Genera datos usando el sensor NodeMCU real con manejo independiente de sensores.

    - Si el NodeMCU completo falla → No genera datos
    - Si solo falla un sensor (ej: humedad) → Genera datos con los sensores que funcionan
    - Cada sensor se monitorea independientemente

    Args:
        session: Sesión de base de datos
        strict_mode: Si es True, no genera datos falsos

    Yields:
        DatoMonitoreo con datos de sensores disponibles, o None si NodeMCU completo falla
    """
    nodemcu_fallado_completamente = False

    while True:
        # Obtener datos del sensor
        sensor_data = await sensor_manager.get_sensor_data()
        sensor_status = sensor_manager.get_sensor_status()

        # Verificar si el NodeMCU completo falló
        if sensor_data is None:
            nodemcu_fallado_completamente = True
            yield None  # NodeMCU no responde en absoluto
            await asyncio.sleep(5)
            continue

        # NodeMCU responde, pero algunos sensores pueden fallar
        nodemcu_fallado_completamente = False

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
            # Crear dato de monitoreo solo con sensores que funcionan
            dato = DatoMonitoreo(
                id_producto_monitoreado=pm.id,
                fecha=datetime.now()
            )

            # Temperatura: solo si el sensor funciona
            if sensor_status.temperatura_ok and sensor_data['temperatura'] is not None:
                dato.temperatura = sensor_data['temperatura']
            elif not strict_mode:
                dato.temperatura = random.uniform(condicion.temperatura_min, condicion.temperatura_max * 1.005)
            else:
                dato.temperatura = condicion.temperatura_min  # Valor mínimo como indicador

            # Humedad: solo si el sensor funciona
            if sensor_status.humedad_ok and sensor_data['humedad'] is not None:
                dato.humedad = sensor_data['humedad']
            elif not strict_mode:
                dato.humedad = random.uniform(condicion.humedad_min, condicion.humedad_max * 1.005)
            else:
                dato.humedad = condicion.humedad_min  # Valor mínimo como indicador

            # Lux: sensor real, solo si funciona
            if sensor_status.lux_ok and sensor_data.get('lux') is not None:
                dato.lux = sensor_data['lux']
            elif not strict_mode:
                dato.lux = random.uniform(condicion.lux_min, condicion.lux_max * 1.005)
            else:
                dato.lux = condicion.lux_min  # Valor mínimo como indicador

            # Presión: sensor real, solo si funciona
            if sensor_status.presion_ok and sensor_data.get('presion') is not None:
                dato.presion = sensor_data['presion']
            elif not strict_mode:
                dato.presion = random.uniform(condicion.presion_min, condicion.presion_max)
            else:
                dato.presion = condicion.presion_min  # Valor mínimo como indicador

            yield dato

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

async def generar_datos_reales_definitivo(session, strict_mode: bool = True) -> AsyncGenerator[Optional[DatoMonitoreo], None]:
    """
    Genera datos usando los 4 sensores NodeMCU reales con manejo independiente de sensores.

    Los 4 sensores son reales:
    - Temperatura (DHT22)
    - Humedad (DHT22)
    - Lux (Sensor de luz real)
    - Presión (Sensor de presión real)

    - Si el NodeMCU completo falla → No genera datos
    - Si solo falla un sensor (ej: humedad) → Genera datos con los sensores que funcionan
    - Cada sensor se monitorea independientemente

    Args:
        session: Sesión de base de datos
        strict_mode: Si es True, no genera datos falsos cuando un sensor falla

    Yields:
        DatoMonitoreo con datos de sensores disponibles, o None si NodeMCU completo falla
    """
    nodemcu_fallado_completamente = False

    while True:
        # Obtener datos del sensor
        sensor_data = await sensor_manager.get_sensor_data()
        sensor_status = sensor_manager.get_sensor_status()

        # Verificar si el NodeMCU completo falló
        if sensor_data is None:
            nodemcu_fallado_completamente = True
            yield None  # NodeMCU no responde en absoluto
            await asyncio.sleep(5)
            continue

        # NodeMCU responde, pero algunos sensores pueden fallar
        nodemcu_fallado_completamente = False

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
            # Crear dato de monitoreo solo con sensores que funcionan
            dato = DatoMonitoreo(
                id_producto_monitoreado=pm.id,
                fecha=datetime.now()
            )

            # Temperatura: solo si el sensor funciona
            if sensor_status.temperatura_ok and sensor_data.get('temperatura') is not None:
                dato.temperatura = sensor_data['temperatura']
            elif not strict_mode:
                dato.temperatura = random.uniform(condicion.temperatura_min, condicion.temperatura_max * 1.005)
            else:
                dato.temperatura = condicion.temperatura_min  # Valor mínimo como indicador

            # Humedad: solo si el sensor funciona
            if sensor_status.humedad_ok and sensor_data.get('humedad') is not None:
                dato.humedad = sensor_data['humedad']
            elif not strict_mode:
                dato.humedad = random.uniform(condicion.humedad_min, condicion.humedad_max * 1.005)
            else:
                dato.humedad = condicion.humedad_min  # Valor mínimo como indicador

            # Lux: sensor real, solo si funciona
            if sensor_status.lux_ok and sensor_data.get('lux') is not None:
                dato.lux = sensor_data['lux']
            elif not strict_mode:
                dato.lux = random.uniform(condicion.lux_min, condicion.lux_max * 1.005)
            else:
                dato.lux = condicion.lux_min  # Valor mínimo como indicador

            # Presión: sensor real, solo si funciona
            if sensor_status.presion_ok and sensor_data.get('presion') is not None:
                dato.presion = sensor_data['presion']
            elif not strict_mode:
                dato.presion = random.uniform(condicion.presion_min, condicion.presion_max)
            else:
                dato.presion = condicion.presion_min  # Valor mínimo como indicador

            yield dato

        await asyncio.sleep(5)