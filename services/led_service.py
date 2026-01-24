import asyncio
import aiohttp
from sqlmodel import Session, select
from core.models.alerta import Alerta
from core.models.condicionalmacenamiento import CondicionAlmacenamiento
from core.models.productofarmaceutico import ProductoFarmaceutico
from core.models.productomonitoreado import ProductoMonitoreado

# Configuración del NodeMCU
NODEMCU_IP = "192.168.0.117"
NODEMCU_LED_URL = f"http://{NODEMCU_IP}/led"

# Umbrales para amarillo (porcentaje del rango máximo)
WARNING_THRESHOLD = 0.90  # 90% del rango máximo


async def enviar_instruccion_led(color: str) -> bool:
    """
    Envía instrucción al NodeMCU para cambiar el color del LED.

    Args:
        color: "verde", "amarillo", "rojo", "apagar"

    Returns:
        True si se envió correctamente, False en caso contrario
    """
    try:
        async with aiohttp.ClientSession() as session:
            params = {"color": color}
            async with session.get(NODEMCU_LED_URL, params=params, timeout=5) as response:
                if response.status == 200:
                    print(f"✅ LED cambiado a {color}")
                    return True
                else:
                    print(f"⚠️ Error cambiando LED: status {response.status}")
                    return False
    except Exception as e:
        print(f"⚠️ Error conectando al NodeMCU para LED: {e}")
        return False


async def evaluar_alertas_y_actualizar_led(session: Session) -> str:
    """
    Evalúa el estado de las alertas y productos monitoreados para determinar
    el color del LED.

    Returns:
        Color del LED: "verde", "amarillo", "rojo"
    """

    # 1. Verificar si hay alertas PENDIENTES (prioridad máxima)
    stmt_alertas = select(Alerta).where(Alerta.estado == "PENDIENTE")
    alertas_pendientes = session.exec(stmt_alertas).all()

    if alertas_pendientes:
        # Hay alertas activas → ROJO
        return "rojo"

    # 2. Si no hay alertas, verificar si algún sensor se acerca al umbral
    stmt = (
        select(ProductoMonitoreado, CondicionAlmacenamiento)
        .join(ProductoFarmaceutico, ProductoMonitoreado.id_producto == ProductoFarmaceutico.id)
        .join(CondicionAlmacenamiento, ProductoFarmaceutico.id_condicion == CondicionAlmacenamiento.id)
        .where(ProductoMonitoreado.fecha_finalizacion_monitoreo == None)
    )

    from adapters.arduino_adapter import sensor_manager
    sensor_data = await sensor_manager.get_sensor_data()
    sensor_status = sensor_manager.get_sensor_status()

    if sensor_data is None:
        # No hay datos del sensor → mantener verde o apagar
        return "verde"

    productos = session.exec(stmt).all()

    for pm, condicion in productos:
        # Verificar temperatura
        if sensor_status.temperatura_ok and sensor_data.get('temperatura') is not None:
            temp = sensor_data['temperatura']
            temp_range = condicion.temperatura_max - condicion.temperatura_min
            temp_max_warning = condicion.temperatura_min + temp_range * WARNING_THRESHOLD
            temp_min_warning = condicion.temperatura_max - temp_range * WARNING_THRESHOLD

            if temp >= temp_max_warning or temp <= temp_min_warning:
                return "amarillo"

        # Verificar humedad
        if sensor_status.humedad_ok and sensor_data.get('humedad') is not None:
            hum = sensor_data['humedad']
            hum_range = condicion.humedad_max - condicion.humedad_min
            hum_max_warning = condicion.humedad_min + hum_range * WARNING_THRESHOLD
            hum_min_warning = condicion.humedad_max - hum_range * WARNING_THRESHOLD

            if hum >= hum_max_warning or hum <= hum_min_warning:
                return "amarillo"

        # Verificar lux
        if sensor_status.lux_ok and sensor_data.get('lux') is not None:
            lux = sensor_data['lux']
            lux_range = condicion.lux_max - condicion.lux_min
            lux_max_warning = condicion.lux_min + lux_range * WARNING_THRESHOLD
            lux_min_warning = condicion.lux_max - lux_range * WARNING_THRESHOLD

            if lux >= lux_max_warning or lux <= lux_min_warning:
                return "amarillo"

        # Verificar presión
        if sensor_status.presion_ok and sensor_data.get('presion') is not None:
            presion = sensor_data['presion']
            presion_range = condicion.presion_max - condicion.presion_min
            presion_max_warning = condicion.presion_min + presion_range * WARNING_THRESHOLD
            presion_min_warning = condicion.presion_max - presion_range * WARNING_THRESHOLD

            if presion >= presion_max_warning or presion <= presion_min_warning:
                return "amarillo"

    # Todo está bien → VERDE
    return "verde"


async def monitorear_y_actualizar_led(session: Session):
    """
    Función principal que evalúa el estado y actualiza el LED.
    """
    color = await evaluar_alertas_y_actualizar_led(session)
    await enviar_instruccion_led(color)


async def background_led_monitoring():
    """
    Proceso en background que actualiza el LED cada 5 segundos.
    Corre independientemente del procesamiento de datos.
    """
    from adapters.db.sqlmodel_database import engine

    print("🚀 Iniciando monitoreo de LED (cada 5 segundos)")

    while True:
        try:
            with Session(engine) as session:
                await monitorear_y_actualizar_led(session)
            await asyncio.sleep(5)  # Actualizar LED cada 5 segundos
        except Exception as e:
            print(f"❌ Error en monitoreo de LED: {e}")
            await asyncio.sleep(5)
