from sqlmodel import Session, select
from core.repositories import dato_monitoreo_repository, alerta_repository
from typing import AsyncGenerator, Optional
from core.models.datomonitoreo import DatoMonitoreo
from adapters.arduino_adapter import sensor_manager
from datetime import datetime
from core.models.productofarmaceutico import ProductoFarmaceutico
from core.models.productomonitoreado import ProductoMonitoreado
from core.models.condicionalmacenamiento import CondicionAlmacenamiento
from core.utils.datetime_utils import get_caracas_now


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
        'timestamp': get_caracas_now()
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

    # Obtener el producto con monitoreo activo (solo puede existir uno)
    stmt = (
        select(ProductoMonitoreado, CondicionAlmacenamiento)
        .join(ProductoFarmaceutico, ProductoMonitoreado.id_producto == ProductoFarmaceutico.id)
        .join(CondicionAlmacenamiento, ProductoFarmaceutico.id_condicion == CondicionAlmacenamiento.id)
        .where(ProductoMonitoreado.fecha_finalizacion_monitoreo == None)
    )

    producto_activo = session.exec(stmt).first()

    # Si no hay producto activo, no procesar los datos (pero no es un error)
    if not producto_activo:
        logger.warning("⚠️ No hay producto con monitoreo activo. Los datos del NodeMCU no serán guardados.")
        return [], sensores_fallados

    pm, condicion = producto_activo

    # Solo guardar si hay al menos un sensor con datos
    if temperatura is not None or humedad is not None or lux is not None or presion is not None:
        dato = DatoMonitoreo(
            id_producto_monitoreado=pm.id,
            fecha=get_caracas_now(),
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
