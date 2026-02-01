from sqlmodel import Session, select
from core.repositories import dato_monitoreo_repository, alerta_repository
from typing import AsyncGenerator, Optional
from core.models.datomonitoreo import DatoMonitoreo
from adapters.arduino_adapter import sensor_manager
from datetime import datetime

async def procesar_datos(datos: AsyncGenerator[Optional[DatoMonitoreo], None], session: Session):
    """
    Procesa datos de monitoreo y maneja alertas de sistema con detección por sensor.

    Args:
        datos: Generador async que yield DatoMonitoreo o None
        session: Sesión de base de datos
    """
    nodemcu_fallado_completamente = False
    sensores_fallados_anteriormente = set()

    async for dato in datos:
        try:
            if dato is None:
                # NodeMCU completo no responde
                if not nodemcu_fallado_completamente:
                    print("⚠️ NodeMCU no detectado - Creando alertas críticas...")
                    alerta_repository.crear_alerta_sensor_no_disponible(session, sensores_fallidos=['temperatura', 'humedad'])
                    nodemcu_fallado_completamente = True
                else:
                    print("⚠️ NodeMCU sigue sin responder - Esperando recuperación...")
                continue

            # NodeMCU responde, verificar sensores individuales
            if nodemcu_fallado_completamente:
                # NodeMCU se restauró
                print("✅ NodeMCU restaurado - Cerrando alertas de sistema...")
                alertas_cerradas = alerta_repository.cerrar_alerta_sensor_no_disponible(session)
                print(f"✅ {alertas_cerradas} alerta(s) cerrada(s)")
                nodemcu_fallado_completamente = False
                sensores_fallados_anteriormente.clear()

            # Verificar estado de sensores individuales
            sensor_status = sensor_manager.get_sensor_status()
            sensores_fallados = sensor_status.get_failed_sensors()

            if sensores_fallados:
                # Hay sensores específicos fallidos
                if sensores_fallados != sensores_fallados_anteriormente:
                    print(f"⚠️ Sensores fallidos detectados: {sensores_fallados}")
                    alerta_repository.crear_alerta_sensor_no_disponible(session, sensores_fallidos=sensores_fallidos)
                    sensores_fallados_anteriormente = set(sensores_fallados)
            elif sensores_fallados_anteriormente:
                # Sensores se restauraron
                print(f"✅ Sensores restaurados: {sensores_fallados_anteriormente}")
                alertas_cerradas = alerta_repository.cerrar_alerta_sensor_no_disponible(session)
                print(f"✅ {alertas_cerradas} alerta(s) de sensor cerrada(s)")
                sensores_fallados_anteriormente.clear()

            # Guardar dato en DB (solo si hay datos válidos)
            if dato.temperatura is not None or dato.humedad is not None:
                db_dato = dato_monitoreo_repository.create_dato_monitoreo(session, dato)

                # Generar alertas si valores están fuera de rango
                alerta_repository.crear_alerta(session, db_dato)

        except Exception as e:
            print(f"Error procesando dato: {str(e)}")


def procesar_datos_entrantes(
    temperatura: float = None,
    humedad: float = None,
    lux: float = None,
    presion: float = None,
    session: Session = None
) -> tuple[list[DatoMonitoreo], list[str]]:
    """
    Procesa datos recibidos del NodeMCU y genera alertas.

    Nueva función para la arquitectura bidireccional donde el NodeMCU
    envía datos al backend en lugar de que el backend los solicite.

    Args:
        temperatura: Valor de temperatura del sensor
        humedad: Valor de humedad del sensor
        lux: Valor de lux del sensor
        presion: Valor de presión del sensor
        session: Sesión de base de datos

    Returns:
        Tuple con:
        - Lista de DatoMonitoreo guardados en BD
        - Lista de sensores fallados (para actualizar estado global)
    """
    from core.models.productofarmaceutico import ProductoFarmaceutico
    from core.models.productomonitoreado import ProductoMonitoreado
    from core.models.condicionalmacenamiento import CondicionAlmacenamiento

    sensores_fallados = []
    datos_guardados = []

    # Actualizar estado de sensores individuales
    if temperatura is not None:
        sensor_manager.sensor_status.temperatura_ok = True
    else:
        sensor_manager.sensor_status.temperatura_ok = False
        sensores_fallados.append("temperatura")

    if humedad is not None:
        sensor_manager.sensor_status.humedad_ok = True
    else:
        sensor_manager.sensor_status.humedad_ok = False
        sensores_fallados.append("humedad")

    if lux is not None:
        sensor_manager.sensor_status.lux_ok = True
    else:
        sensor_manager.sensor_status.lux_ok = False
        sensores_fallados.append("lux")

    if presion is not None:
        sensor_manager.sensor_status.presion_ok = True
    else:
        sensor_manager.sensor_status.presion_ok = False
        sensores_fallados.append("presion")

    # Actualizar último dato de sensor en el manager
    sensor_manager.last_sensor_data = {
        'temperatura': temperatura,
        'humedad': humedad,
        'lux': lux,
        'presion': presion,
        'timestamp': datetime.now()
    }

    # Verificar si NodeMCU está completamente fallado
    nodemcu_fallado_completamente = len(sensores_fallados) == 4

    if nodemcu_fallado_completamente:
        print("⚠️ NodeMCU no detectado - Creando alertas críticas...")
        alerta_repository.crear_alerta_sensor_no_disponible(session, sensores_fallidos=['temperatura', 'humedad'])
        return [], sensores_fallados

    # Manejar alertas de sensores individuales
    if sensores_fallados:
        print(f"⚠️ Sensores fallados detectados: {sensores_fallados}")
        alerta_repository.crear_alerta_sensor_no_disponible(session, sensores_fallidos=sensores_fallados)

    # Obtener productos con monitoreo activo
    stmt = (
        select(ProductoMonitoreado, CondicionAlmacenamiento)
        .join(ProductoFarmaceutico, ProductoMonitoreado.id_producto == ProductoFarmaceutico.id)
        .join(CondicionAlmacenamiento, ProductoFarmaceutico.id_condicion == CondicionAlmacenamiento.id)
        .where(ProductoMonitoreado.fecha_finalizacion_monitoreo == None)
    )

    productos = session.exec(stmt).all()

    # Crear datos de monitoreo para cada producto activo
    for pm, condicion in productos:
        # Solo guardar si hay al menos un sensor con datos
        if temperatura is not None or humedad is not None or lux is not None or presion is not None:
            dato = DatoMonitoreo(
                id_producto_monitoreado=pm.id,
                fecha=datetime.now(),
                temperatura=temperatura,
                humedad=humedad,
                lux=lux,
                presion=presion
            )

            # Guardar en BD
            db_dato = dato_monitoreo_repository.create_dato_monitoreo(session, dato)
            datos_guardados.append(db_dato)

            # Generar alertas si valores están fuera de rango
            alerta_repository.crear_alerta(session, db_dato)

    return datos_guardados, sensores_fallados