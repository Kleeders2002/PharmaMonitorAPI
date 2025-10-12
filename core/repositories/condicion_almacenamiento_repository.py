from fastapi import Depends
from sqlmodel import Session
from sqlalchemy import select, exists

from core.models.condicionalmacenamiento import CondicionAlmacenamiento
from core.models.productofarmaceutico import ProductoFarmaceutico
from core.models.usuario import UserRead
from core.ports.registro_port import RegistroPort


def get_condiciones(session: Session):
    condiciones = session.exec(
        select(CondicionAlmacenamiento)
    ).scalars().all()

    result = []
    for condicion in condiciones:
        is_related = session.exec(
            select(exists().where(ProductoFarmaceutico.id_condicion == condicion.id))
        ).scalar_one()

        result.append({
            "id": condicion.id,
            "nombre": condicion.nombre,
            "temperatura_min": condicion.temperatura_min,
            "temperatura_max": condicion.temperatura_max,
            "humedad_min": condicion.humedad_min,
            "humedad_max": condicion.humedad_max,
            "lux_min": condicion.lux_min,
            "lux_max": condicion.lux_max,
            "presion_min": condicion.presion_min,
            "presion_max": condicion.presion_max,
            "fecha_actualizacion": condicion.fecha_actualizacion,
            "is_related": is_related
        })

    return result


def get_condicion_by_id(session: Session, id: int):
    return session.get(CondicionAlmacenamiento, id)


def create_condicion(
    session: Session,
    condicion: CondicionAlmacenamiento,
    registro: RegistroPort,
    usuario_actual: UserRead
):
    session.add(condicion)
    session.commit()
    session.refresh(condicion)
    
    detalles = condicion.dict()
    detalles["fecha_actualizacion"] = detalles["fecha_actualizacion"].isoformat()
    
    registro.registrar(
        usuario_id=usuario_actual.id,
        nombre_usuario=usuario_actual.nombre,
        rol_usuario=usuario_actual.rol,
        operacion="crear",
        entidad="CondicionAlmacenamiento",
        entidad_id=condicion.id,
        detalles=detalles
    )
    
    session.commit()
    return condicion


def update_condicion(
    session: Session,
    condicion: CondicionAlmacenamiento,
    registro: RegistroPort,
    usuario_actual: UserRead
):
    detalles = condicion.dict()
    detalles["fecha_actualizacion"] = detalles["fecha_actualizacion"].isoformat()
    
    registro.registrar(
        usuario_id=usuario_actual.id,
        nombre_usuario=usuario_actual.nombre,
        rol_usuario=usuario_actual.rol,
        operacion="actualizar",
        entidad="CondicionAlmacenamiento",
        entidad_id=condicion.id,
        detalles=detalles
    )
    
    session.commit()
    session.refresh(condicion)
    
    return condicion


def delete_condicion(
    session: Session,
    condicion: CondicionAlmacenamiento,
    registro: RegistroPort,
    usuario_actual: UserRead
):
    entidad_id = condicion.id
    detalles = condicion.dict()
    detalles["fecha_actualizacion"] = (
        detalles.get("fecha_actualizacion", "").isoformat() 
        if detalles.get("fecha_actualizacion") 
        else None
    )
    
    session.delete(condicion)
    
    registro.registrar(
        usuario_id=usuario_actual.id,
        nombre_usuario=usuario_actual.nombre,
        rol_usuario=usuario_actual.rol,
        operacion="eliminar",
        entidad="CondicionAlmacenamiento",
        entidad_id=entidad_id,
        detalles=detalles
    )
    
    session.commit()


# Antes de los Registros

# def create_condicion(session: Session, condicion: CondicionAlmacenamiento):
#     session.add(condicion)
#     session.commit()
#     session.refresh(condicion)
#     return condicion

# def update_condicion(session: Session, condicion: CondicionAlmacenamiento):
#     session.commit()
#     session.refresh(condicion)
#     return condicion

# def delete_condicion(session: Session, condicion: CondicionAlmacenamiento):
#     session.delete(condicion)
#     session.commit()
