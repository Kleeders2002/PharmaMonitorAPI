import asyncio
import aiohttp
import os
from dotenv import load_dotenv
from sqlmodel import Session, select
from core.models.alerta import Alerta
from core.models.condicionalmacenamiento import CondicionAlmacenamiento
from core.models.productofarmaceutico import ProductoFarmaceutico
from core.models.productomonitoreado import ProductoMonitoreado

# Cargar variables de entorno
load_dotenv()

# Configuración del NodeMCU
NODEMCU_IP = os.getenv("NODEMCU_IP", "192.168.0.117")
NODEMCU_LED_URL = f"http://{NODEMCU_IP}/led"

# Umbrales para amarillo (porcentaje del rango máximo)
WARNING_THRESHOLD = 0.90  # 90% del rango máximo


async def enviar_instruccion_led(color: str) -> bool:
    """
    Envía instrucción al NodeMCU para cambiar el color del LED.

    Args:
        color: "verde", "amarillo", "rojo", "apagar", "test_rojo", "test_verde", "test_azul"

    Returns:
        True si se envió correctamente, False en caso contrario
    """
    try:
        async with aiohttp.ClientSession() as session:
            params = {"color": color}
            async with session.get(NODEMCU_LED_URL, params=params, timeout=5) as response:
                if response.status == 200:
                    print(f"LED cambiado a {color}")
                    return True
                else:
                    print(f"Error cambiando LED: status {response.status}")
                    return False
    except Exception as e:
        print(f"Error conectando al NodeMCU para LED: {e}")
        return False


# Variable global para recordar el último estado del LED
ultimo_color_led = "verde"
modo_alerta_activo = False  # Nuevo: Bloquea cambios si hay alerta activa

async def evaluar_alertas_y_actualizar_led(session: Session) -> str:
    """
    Evalúa el estado de las alertas y productos monitoreados para determinar
    el color del LED.

    PRIORIDAD ABSOLUTA (no hay excepciones):
    1. 🔴 ROJO - Si hay alertas PENDIENTES → Se mantiene ROJO hasta resolución MANUAL
    2. 🔴 ROJO - Sensores fallados (1 o más)
    3. 🟡 AMARILLO - Sensores en umbral de advertencia (SOLO si NO hay alertas NI fallos)
    4. 🟢 VERDE - Todo normal

    IMPORTANTE: Si hay alerta O sensores fallados → SIEMPRE ROJO, sin excepción.

    Returns:
        Color del LED: "verde", "amarillo", "rojo"
    """
    global ultimo_color_led, modo_alerta_activo

    # ============================================================
    # PRIORIDAD 1: VERIFICAR ALERTAS PENDIENTES (BLOQUEO TOTAL)
    # ============================================================
    stmt_alertas = select(Alerta).where(Alerta.estado == "PENDIENTE")
    alertas_pendientes = session.exec(stmt_alertas).all()

    if alertas_pendientes:
        # Hay alertas activas → ROJO ABSOLUTO (sin importar nada más)
        if not modo_alerta_activo:
            print(f"⚠️ ALERTA ACTIVA detectada - {len(alertas_pendientes)} alertas pendientes")
            print("🔴 LED BLOQUEADO en ROJO hasta resolución manual")
        modo_alerta_activo = True
        ultimo_color_led = "rojo"
        return "rojo"

    # Si llegamos aquí, NO hay alertas pendientes
    # Resetear estado de alerta
    if modo_alerta_activo:
        print("✅ ALERTA resuelta - Liberando bloqueo de LED")
        modo_alerta_activo = False
        # Resetear ultimo_color_led para evitar que la histéresis use "rojo"
        ultimo_color_led = "verde"

    # ============================================================
    # PRIORIDAD 2: VERIFICAR SENSORES FALLADOS (BLOQUEO TOTAL)
    # ============================================================
    from adapters.arduino_adapter import sensor_manager
    sensor_status = sensor_manager.get_sensor_status()
    sensores_fallados = sensor_status.get_failed_sensors()

    if sensores_fallados:
        # Hay sensores fallados → ROJO ABSOLUTO (sin importar umbrales)
        if ultimo_color_led != "rojo":
            print(f"⚠️ SENSORES FALLADOS detectados: {sensores_fallados}")
            print("🔴 LED en ROJO por fallo de sensores")
        ultimo_color_led = "rojo"
        return "rojo"

    # ============================================================
    # PRIORIDAD 3 y 4: SOLO SI NO HAY ALERTAS NI FALLOS
    # Aquí SI podemos evaluar amarillo o verde
    # ============================================================
    stmt = (
        select(ProductoMonitoreado, CondicionAlmacenamiento)
        .join(ProductoFarmaceutico, ProductoMonitoreado.id_producto == ProductoFarmaceutico.id)
        .join(CondicionAlmacenamiento, ProductoFarmaceutico.id_condicion == CondicionAlmacenamiento.id)
        .where(ProductoMonitoreado.fecha_finalizacion_monitoreo == None)
    )

    sensor_data = await sensor_manager.get_sensor_data()

    if sensor_data is None:
        # No hay datos del sensor → mantener verde por seguridad
        if ultimo_color_led != "verde":
            print("ℹ️ No hay datos de sensores - Manteniendo VERDE por seguridad")
        return "verde"

    productos = session.exec(stmt).all()

    # HISTÉRESIS: Umbrales diferentes para evitar parpadeo
    WARNING_THRESHOLD_ON = 0.90  # 90% - Para encender amarillo
    WARNING_THRESHOLD_OFF = 0.85  # 85% - Para apagar amarillo

    # Usar umbral diferente según el estado actual
    threshold = WARNING_THRESHOLD_OFF if ultimo_color_led == "amarillo" else WARNING_THRESHOLD_ON

    algun_sensor_en_umbral = False

    for pm, condicion in productos:
        # Verificar temperatura
        if sensor_status.temperatura_ok and sensor_data.get('temperatura') is not None:
            temp = sensor_data['temperatura']
            temp_range = condicion.temperatura_max - condicion.temperatura_min
            temp_max_warning = condicion.temperatura_min + temp_range * threshold
            temp_min_warning = condicion.temperatura_max - temp_range * threshold

            if temp >= temp_max_warning or temp <= temp_min_warning:
                algun_sensor_en_umbral = True

        # Verificar humedad
        if sensor_status.humedad_ok and sensor_data.get('humedad') is not None:
            hum = sensor_data['humedad']
            hum_range = condicion.humedad_max - condicion.humedad_min
            hum_max_warning = condicion.humedad_min + hum_range * threshold
            hum_min_warning = condicion.humedad_max - hum_range * threshold

            if hum >= hum_max_warning or hum <= hum_min_warning:
                algun_sensor_en_umbral = True

        # Verificar lux
        if sensor_status.lux_ok and sensor_data.get('lux') is not None:
            lux = sensor_data['lux']
            lux_range = condicion.lux_max - condicion.lux_min
            lux_max_warning = condicion.lux_min + lux_range * threshold
            lux_min_warning = condicion.lux_max - lux_range * threshold

            if lux >= lux_max_warning or lux <= lux_min_warning:
                algun_sensor_en_umbral = True

        # Verificar presión
        if sensor_status.presion_ok and sensor_data.get('presion') is not None:
            presion = sensor_data['presion']
            presion_range = condicion.presion_max - condicion.presion_min
            presion_max_warning = condicion.presion_min + presion_range * threshold
            presion_min_warning = condicion.presion_max - presion_range * threshold

            if presion >= presion_max_warning or presion <= presion_min_warning:
                algun_sensor_en_umbral = True

    # Decidir color final con histéresis
    if algun_sensor_en_umbral:
        # Sensores cerca de los límites → AMARILLO
        # (SOLO llegamos aquí si NO hay alertas NI fallos)
        if ultimo_color_led != "amarillo":
            print("⚠️ Sensor en umbral de advertencia - LED en AMARILLO")
        ultimo_color_led = "amarillo"
        return "amarillo"
    else:
        # Todo normal → VERDE
        # (SOLO llegamos aquí si NO hay alertas NI fallos NI umbrales)
        if ultimo_color_led != "verde":
            print("✅ Todos los sensores normales - LED en VERDE")
        ultimo_color_led = "verde"
        return "verde"


async def monitorear_y_actualizar_led(session: Session):
    """
    Función principal que evalúa el estado y actualiza el LED.

    Orden de evaluación (prioridad absoluta):
    1. 🔴 ROJO si hay alertas PENDIENTES (bloqueo total)
    2. 🔴 ROJO si hay sensores FALLADOS (bloqueo total)
    3. 🟡 AMARILLO si sensores en umbral (solo si 1 y 2 son falsos)
    4. 🟢 VERDE si todo normal (solo si 1, 2 y 3 son falsos)
    """
    # Evaluar estado actual según prioridades
    color = await evaluar_alertas_y_actualizar_led(session)

    # Log para debug
    print(f"🎨 Color LED decidido: {color.upper()} | modo_alerta_activo: {modo_alerta_activo}")

    # Para probar colores manualmente, comenta la línea de arriba
    # y descomenta una de estas:
    # color = "rojo"      # Forzar ROJO
    # color = "amarillo"  # Forzar AMARILLO
    # color = "verde"     # Forzar VERDE
    # color = "apagar"    # Forzar APAGAR

    await enviar_instruccion_led(color)


async def background_led_monitoring():
    """
    Proceso en background que actualiza el LED cada 1 segundo.
    Corre independientemente del procesamiento de datos.
    """
    from adapters.db.sqlmodel_database import engine

    print("Iniciando monitoreo de LED (cada 1 segundo)")

    while True:
        try:
            with Session(engine) as session:
                await monitorear_y_actualizar_led(session)
            await asyncio.sleep(1)  # Actualizar LED cada 1 segundo
        except Exception as e:
            print(f"Error en monitoreo de LED: {e}")
            await asyncio.sleep(1)
