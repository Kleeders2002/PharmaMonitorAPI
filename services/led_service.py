"""
Servicio de control de LED para PharmaMonitor.

Arquitectura actual:
- NodeMCU envía datos al backend vía POST /nodemcu/data
- Backend determina color del LED y lo retorna en la respuesta
- NodeMCU actualiza el LED según el color recibido
"""
from sqlmodel import Session, select
from core.models.alerta import Alerta
from core.models.condicionalmacenamiento import CondicionAlmacenamiento
from core.models.productofarmaceutico import ProductoFarmaceutico
from core.models.productomonitoreado import ProductoMonitoreado


# Variable global para recordar el último estado del LED
ultimo_color_led = "verde"
modo_alerta_activo = False  # Bloquea cambios si hay alerta activa


def determinar_color_led_solo(session: Session, sensor_data: dict = None) -> str:
    """
    Determina el color del LED SIN enviar instrucciones HTTP.

    Esta función extrae solo la lógica de decisión para ser usada
    en el endpoint POST /nodemcu/data.

    PRIORIDAD ABSOLUTA (no hay excepciones):
    1. 🔴 ROJO - Si hay alertas PENDIENTES → Se mantiene ROJO hasta resolución MANUAL
    2. 🔴 ROJO - Sensores fallados (1 o más)
    3. 🟡 AMARILLO - Sensores en umbral de advertencia (SOLO si NO hay alertas NI fallos)
    4. 🟢 VERDE - Todo normal

    Args:
        session: Sesión de base de datos
        sensor_data: Diccionario opcional con datos de sensores {temperatura, humedad, lux, presion}
                    IMPORTANTE: En la nueva arquitectura, este parámetro SIEMPRE debe ser proporcionado
                    desde el endpoint POST /nodemcu/data

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

    # NOTA: En la nueva arquitectura bidireccional, sensor_data SIEMPRE
    # debe ser proporcionado desde el endpoint POST /nodemcu/data
    # Si es None, usar last_sensor_data del sensor_manager (fallback)
    if sensor_data is None:
        sensor_data = sensor_manager.last_sensor_data

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
