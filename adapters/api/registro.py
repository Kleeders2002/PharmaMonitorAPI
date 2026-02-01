from fastapi import APIRouter, Depends, HTTPException
from adapters.db.sqlmodel_database import get_session
from core.models.registro import Registro
from core.repositories.registro_repository import (
    get_registros
)

router = APIRouter()

@router.get("/registros/", response_model=list[Registro])
def listar_registros(session=Depends(get_session)):
    return get_registros(session)
