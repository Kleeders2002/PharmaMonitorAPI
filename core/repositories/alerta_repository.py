from sqlmodel import Session, select
from datetime import datetime
from typing import List, Optional
from core.models.alerta import Alerta, EstadoAlerta
from core.models.datomonitoreo import DatoMonitoreo
from core.models.condicionalmacenamiento import CondicionAlmacenamiento
from core.models.productomonitoreado import ProductoMonitoreado
from core.utils.datetime_utils import get_caracas_now

def get_alertas(session: Session):
    return session.exec(select(Alerta)).all()

def crear_alerta(session: Session, dato: DatoMonitoreo) -> List[Alerta]:
    # 1. Obtener relaciones necesarias
    producto_monitoreado = dato.productomonitoreado
    condicion = producto_monitoreado.producto.condicion

    # 2. Verificar TODOS los parámetros fuera de rango
    parametros_problematicos = verificar_parametros(dato, condicion)

    # 3. Cerrar alertas de parámetros que volvieron a la normalidad
    cerrar_alertas_resueltas(session, producto_monitoreado.id, parametros_problematicos)

    alertas_generadas = []
    
    # 4. Procesar cada parámetro problemático
    for parametro in parametros_problematicos:
        # Buscar alerta existente para este parámetro
        alerta_existente = session.exec(
            select(Alerta)
            .where(Alerta.id_producto_monitoreado == producto_monitoreado.id)
            .where(Alerta.parametro_afectado == parametro)
            .where(Alerta.estado == EstadoAlerta.PENDIENTE)
        ).first()
        
        if alerta_existente:
            # Actualizar duración de alerta existente
            alerta_existente.duracion_minutos = (
                get_caracas_now() - alerta_existente.fecha_generacion
            ).total_seconds() / 60
            session.commit()
            alertas_generadas.append(alerta_existente)
        else:
            # Crear nueva alerta
            nueva_alerta = Alerta(
                id_producto_monitoreado=producto_monitoreado.id,
                id_dato_monitoreo=dato.id,
                id_condicion=condicion.id,
                parametro_afectado=parametro,
                valor_medido=getattr(dato, parametro),
                limite_min=getattr(condicion, f"{parametro}_min"),
                limite_max=getattr(condicion, f"{parametro}_max"),
                mensaje=f"¡Alerta! {parametro.capitalize()} fuera de rango",
                fecha_generacion=get_caracas_now(),
                estado=EstadoAlerta.PENDIENTE
            )
            session.add(nueva_alerta)
            session.commit()
            session.refresh(nueva_alerta)
            alertas_generadas.append(nueva_alerta)
    
    return alertas_generadas

def cerrar_alertas_resueltas(
    session: Session,
    producto_id: int,
    parametros_activos: List[str]
):
    # Cerrar alertas de parámetros que no están en la lista de activos
    alertas_a_cerrar = session.exec(
        select(Alerta)
        .where(Alerta.id_producto_monitoreado == producto_id)
        .where(Alerta.estado == EstadoAlerta.PENDIENTE)
        .where(Alerta.parametro_afectado.not_in(parametros_activos))
    ).all()
    
    for alerta in alertas_a_cerrar:
        alerta.estado = EstadoAlerta.RESUELTA
        alerta.fecha_resolucion = get_caracas_now()
        alerta.duracion_minutos = (
            get_caracas_now() - alerta.fecha_generacion
        ).total_seconds() / 60
    
    session.commit()

def verificar_parametros(
    dato: DatoMonitoreo,
    condicion: CondicionAlmacenamiento
) -> List[str]:
    parametros_fuera_rango = []

    for param in ["temperatura", "humedad", "lux", "presion"]:
        valor = getattr(dato, param)
        min_val = getattr(condicion, f"{param}_min")
        max_val = getattr(condicion, f"{param}_max")

        if valor < min_val or valor > max_val:
            parametros_fuera_rango.append(param)

    return parametros_fuera_rango

def crear_alerta_sensor_no_disponible(session: Session, sensores_fallidos: list[str] = None, mensaje_error: str = None) -> List[Alerta]:
    """
    Crea alertas críticas para sensores específicos que no están disponibles.

    Args:
        session: Sesión de base de datos
        sensores_fallidos: Lista de sensores que fallaron (ej: ['humedad', 'temperatura'])
        mensaje_error: Mensaje de error adicional

    Ejemplo:
        Si falla solo el sensor de humedad → Alerta "Sensor de humedad no disponible"
        Si fallan todos → Alerta "NodeMCU no disponible"
    """
    from core.models.productomonitoreado import ProductoMonitoreado
    from core.models.productofarmaceutico import ProductoFarmaceutico

    # Si todos los sensores críticos fallaron (NodeMCU completo caído)
    sensores_criticos = ['temperatura', 'humedad']
    nodemcu_completo_fallado = sensores_fallidos is None or all(s in sensores_fallidos for s in sensores_criticos)

    # Obtener todos los productos con monitoreo activo
    stmt = (
        select(ProductoMonitoreado, ProductoFarmaceutico, CondicionAlmacenamiento)
        .join(ProductoFarmaceutico, ProductoMonitoreado.id_producto == ProductoFarmaceutico.id)
        .join(CondicionAlmacenamiento, ProductoFarmaceutico.id_condicion == CondicionAlmacenamiento.id)
        .where(ProductoMonitoreado.fecha_finalizacion_monitoreo == None)
    )

    resultados = session.exec(stmt).all()
    alertas_creadas = []

    for pm, pf, cond in resultados:
        # Determinar qué alertas crear según los sensores fallidos
        if nodemcu_completo_fallado:
            # NodeMCU completo caído
            parametro = "NODEMCU_NO_DISPONIBLE"
            mensaje = f"🚨 NodeMCU no disponible - Verificar hardware" + (f": {mensaje_error}" if mensaje_error else "")

            # Verificar si ya existe esta alerta
            alerta_existente = session.exec(
                select(Alerta)
                .where(Alerta.id_producto_monitoreado == pm.id)
                .where(Alerta.parametro_afectado == parametro)
                .where(Alerta.estado == EstadoAlerta.PENDIENTE)
            ).first()

            if not alerta_existente:
                nueva_alerta = Alerta(
                    id_producto_monitoreado=pm.id,
                    id_dato_monitoreo=None,
                    id_condicion=cond.id,
                    parametro_afectado=parametro,
                    valor_medido=0.0,
                    limite_min=0.0,
                    limite_max=0.0,
                    mensaje=mensaje,
                    fecha_generacion=get_caracas_now(),
                    estado=EstadoAlerta.PENDIENTE
                )
                session.add(nueva_alerta)
                session.commit()
                session.refresh(nueva_alerta)
                alertas_creadas.append(nueva_alerta)
        else:
            # Sensores específicos fallados
            for sensor in sensores_fallidos:
                parametro = f"SENSOR_{sensor.upper()}_NO_DISPONIBLE"
                mensaje = f"⚠️ Sensor de {sensor} no disponible - Revisar hardware"

                # Verificar si ya existe esta alerta para este sensor específico
                alerta_existente = session.exec(
                    select(Alerta)
                    .where(Alerta.id_producto_monitoreado == pm.id)
                    .where(Alerta.parametro_afectado == parametro)
                    .where(Alerta.estado == EstadoAlerta.PENDIENTE)
                ).first()

                if not alerta_existente:
                    nueva_alerta = Alerta(
                        id_producto_monitoreado=pm.id,
                        id_dato_monitoreo=None,
                        id_condicion=cond.id,
                        parametro_afectado=parametro,
                        valor_medido=0.0,
                        limite_min=getattr(condicion, f"{sensor}_min") if hasattr(condicion, f"{sensor}_min") else 0.0,
                        limite_max=getattr(condicion, f"{sensor}_max") if hasattr(condicion, f"{sensor}_max") else 0.0,
                        mensaje=mensaje,
                        fecha_generacion=get_caracas_now(),
                        estado=EstadoAlerta.PENDIENTE
                    )
                    session.add(nueva_alerta)
                    session.commit()
                    session.refresh(nueva_alerta)
                    alertas_creadas.append(nueva_alerta)

    return alertas_creadas
    """
    Crea alertas críticas para todos los productos monitoreados cuando el sensor no está disponible.
    """
    from core.models.productomonitoreado import ProductoMonitoreado
    from core.models.productofarmaceutico import ProductoFarmaceutico

    # Obtener todos los productos con monitoreo activo
    stmt = (
        select(ProductoMonitoreado, ProductoFarmaceutico, CondicionAlmacenamiento)
        .join(ProductoFarmaceutico, ProductoMonitoreado.id_producto == ProductoFarmaceutico.id)
        .join(CondicionAlmacenamiento, ProductoFarmaceutico.id_condicion == CondicionAlmacenamiento.id)
        .where(ProductoMonitoreado.fecha_finalizacion_monitoreo == None)
    )

    resultados = session.exec(stmt).all()
    alertas_creadas = []

    for pm, pf, cond in resultados:
        # Verificar si ya existe una alerta de sensor no disponible para este producto
        alerta_existente = session.exec(
            select(Alerta)
            .where(Alerta.id_producto_monitoreado == pm.id)
            .where(Alerta.parametro_afectado == "SENSOR_NO_DISPONIBLE")
            .where(Alerta.estado == EstadoAlerta.PENDIENTE)
        ).first()

        if alerta_existente:
            # Actualizar duración
            alerta_existente.duracion_minutos = (
                get_caracas_now() - alerta_existente.fecha_generacion
            ).total_seconds() / 60
            session.commit()
            alertas_creadas.append(alerta_existente)
        else:
            # Crear nueva alerta de sensor no disponible
            mensaje = f"🚨 Sensor NodeMCU no disponible - Verificar hardware" + (f": {mensaje_error}" if mensaje_error else "")
            nueva_alerta = Alerta(
                id_producto_monitoreado=pm.id,
                id_dato_monitoreo=None,  # No hay dato de monitoreo
                id_condicion=cond.id,
                parametro_afectado="SENSOR_NO_DISPONIBLE",
                valor_medido=0.0,
                limite_min=0.0,
                limite_max=0.0,
                mensaje=mensaje,
                fecha_generacion=get_caracas_now(),
                estado=EstadoAlerta.PENDIENTE
            )
            session.add(nueva_alerta)
            session.commit()
            session.refresh(nueva_alerta)
            alertas_creadas.append(nueva_alerta)

    return alertas_creadas

def cerrar_alerta_sensor_no_disponible(session: Session) -> int:
    """
    Cierra todas las alertas de SENSOR_NO_DISPONIBLE cuando el sensor vuelve a funcionar.
    Retorna el número de alertas cerradas.
    """
    alertas_a_cerrar = session.exec(
        select(Alerta)
        .where(Alerta.parametro_afectado == "SENSOR_NO_DISPONIBLE")
        .where(Alerta.estado == EstadoAlerta.PENDIENTE)
    ).all()

    count = 0
    for alerta in alertas_a_cerrar:
        alerta.estado = EstadoAlerta.RESUELTA
        alerta.fecha_resolucion = get_caracas_now()
        alerta.duracion_minutos = (
            get_caracas_now() - alerta.fecha_generacion
        ).total_seconds() / 60
        alerta.mensaje = "✅ Sensor NodeMCU restaurado - Monitoreo normal"
        count += 1

    session.commit()
    return count