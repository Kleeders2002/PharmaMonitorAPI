from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from adapters.db.sqlmodel_database import get_session
from core.models.formafarmaceutica import FormaFarmaceutica
from core.repositories.forma_farmaceutica_repository import (
    get_formafarmaceutica
)

router = APIRouter()

@router.get("/formafarmaceutica/", response_model=list[FormaFarmaceutica])
def listar_formafarmaceutica(session: Session = Depends(get_session)):
    return get_formafarmaceutica(session)  