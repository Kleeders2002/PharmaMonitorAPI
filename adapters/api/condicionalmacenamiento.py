from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from datetime import datetime
from adapters.db.sqlmodel_database import get_session
from core.models.condicionalmacenamiento import CondicionAlmacenamiento
from core.models.condicionalmacenamientoconrelacion import CondicionAlmacenamientoConRelacion
from core.models.usuario import UserRead
from core.ports.registro_port import RegistroPort
from dependencies import get_registro, get_current_user
from core.repositories.condicion_almacenamiento_repository import (
    get_condiciones,
    get_condicion_by_id,
    create_condicion,
    update_condicion,
    delete_condicion
)
from core.utils.datetime_utils import get_caracas_now

router = APIRouter()

@router.get("/condiciones/", response_model=list[CondicionAlmacenamientoConRelacion])
def listar_condiciones(session: Session = Depends(get_session)):
    return get_condiciones(session)

@router.get("/condiciones/{id}", response_model=CondicionAlmacenamiento)
def obtener_condicion(id: int, session: Session = Depends(get_session)):
    condicion = get_condicion_by_id(session, id)
    if not condicion:
        raise HTTPException(status_code=404, detail="Condición no encontrada")
    return condicion

@router.post("/condiciones/")
def crear_condicion(condicion: CondicionAlmacenamiento, session: Session = Depends(get_session), Registro: RegistroPort = Depends(get_registro), current_user: UserRead = Depends(get_current_user)):
    return create_condicion(session, condicion, Registro, current_user)

@router.put("/condiciones/{id}", response_model=CondicionAlmacenamiento)
def actualizar_condicion(
    id: int,
    condicion_actualizada: CondicionAlmacenamiento,
    session: Session = Depends(get_session),
    Registro: RegistroPort = Depends(get_registro),
    current_user: UserRead = Depends(get_current_user)
):
    condicion = get_condicion_by_id(session, id)
    if not condicion:
        raise HTTPException(status_code=404, detail="Condición no encontrada")

    # Actualizar campos editables
    condicion.nombre = condicion_actualizada.nombre
    condicion.temperatura_min = condicion_actualizada.temperatura_min
    condicion.temperatura_max = condicion_actualizada.temperatura_max
    condicion.humedad_min = condicion_actualizada.humedad_min
    condicion.humedad_max = condicion_actualizada.humedad_max
    condicion.lux_min = condicion_actualizada.lux_min
    condicion.lux_max = condicion_actualizada.lux_max
    condicion.presion_min = condicion_actualizada.presion_min
    condicion.presion_max = condicion_actualizada.presion_max

    # Actualizar fecha automáticamente
    condicion.fecha_actualizacion = get_caracas_now()

    return update_condicion(session, condicion, Registro, current_user)

@router.delete("/condiciones/{id}")
def eliminar_condicion(
    id: int,
    session: Session = Depends(get_session),
    Registro: RegistroPort = Depends(get_registro),
    current_user: UserRead = Depends(get_current_user)
):
    condicion = get_condicion_by_id(session, id)
    if not condicion:
        raise HTTPException(status_code=404, detail="Condición no encontrada")
    delete_condicion(session, condicion, Registro, current_user)
    return {"detail": "Condición eliminada exitosamente"}
