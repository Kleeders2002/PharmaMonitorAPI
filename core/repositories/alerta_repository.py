from sqlmodel import Session, select
from datetime import datetime
from typing import List, Optional
from core.models.alerta import Alerta, EstadoAlerta
from core.models.datomonitoreo import DatoMonitoreo
from core.models.condicionalmacenamiento import CondicionAlmacenamiento
from core.models.productomonitoreado import ProductoMonitoreado

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
                datetime.now() - alerta_existente.fecha_generacion
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
                fecha_generacion=datetime.now(),
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
        alerta.fecha_resolucion = datetime.now()
        alerta.duracion_minutos = (
            datetime.now() - alerta.fecha_generacion
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