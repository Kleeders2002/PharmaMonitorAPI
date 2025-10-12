from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from datetime import datetime

from core.models.alerta import Alerta
from core.models.datomonitoreo import DatoMonitoreo
from adapters.db.sqlmodel_database import get_session
from core.repositories import alerta_repository

router = APIRouter()

@router.get("/alertas/", response_model=list[Alerta])
def listar_alertas(session=Depends(get_session)):
    return alerta_repository.get_alertas(session)

@router.post("/alertas/", response_model=Alerta)
def crear_alerta(
    dato_monitoreo_id: int,  # ID del DatoMonitoreo que dispara la alerta
    session: Session = Depends(get_session)
):
    try:
        # Obtener el dato de monitoreo de la DB
        dato = session.get(DatoMonitoreo, dato_monitoreo_id)
        if not dato:
            raise HTTPException(status_code=404, detail="Dato de monitoreo no encontrado")
        
        # Lógica central en el repositorio
        return alerta_repository.crear_alerta(session, dato)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))