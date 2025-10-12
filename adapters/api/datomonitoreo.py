from fastapi import APIRouter, Depends, HTTPException
from adapters.db.sqlmodel_database import get_session
from core.models.datomonitoreo import DatoMonitoreo
from core.repositories.dato_monitoreo_repository import (
    get_datosmonitoreo,
    get_datosmonitoreo_by_id
)


router = APIRouter()

@router.get("/datosmonitoreo/", response_model=list[DatoMonitoreo])
def listar_datosmonitoreo(session=Depends(get_session)):
    return get_datosmonitoreo(session)

@router.get("/datosmonitoreo/{id}", response_model=list[DatoMonitoreo])
def obtener_datosmonitoreo(id: int, session=Depends(get_session)):
   return get_datosmonitoreo_by_id(session, id)
