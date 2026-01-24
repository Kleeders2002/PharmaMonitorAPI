# core/routers/dashboard_router.py
from fastapi import APIRouter, Depends, HTTPException
from adapters.db.sqlmodel_database import get_session
from core.repositories.dashboard_repository import get_dashboard_metrics, get_usuarios_test, get_ultimos_productos, get_ultimos_registros, get_ultimos_usuarios
from typing import Dict
from core.models.DashboardMetricsRead import DashboardMetricsRead
from core.models.usuario import Usuario
from core.models.registro import Registro
from typing import List
from core.models.productofarmaceutico import ProductoFarmaceutico
from sqlmodel import Session

router = APIRouter()

@router.get("/dashboard/metrics", response_model=DashboardMetricsRead)
def obtener_metricas_dashboard(session=Depends(get_session)):
    try:
        metrics = get_dashboard_metrics(session)
        return metrics
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo métricas del dashboard: {str(e)}"
        )
    
@router.get("/dashboard/metrics/user-count", tags=["dashboard"])
def obtener_conteo_usuarios(session=Depends(get_session)):
    """
    Devuelve el número total de usuarios registrados
    """
    try:
        count = get_usuarios_test(session)
        return {"usuarios_registrados": count}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo conteo de usuarios: {str(e)}"
        )
    

@router.get("/dashboard/metrics/last-product", tags=["dashboard"], response_model=List[ProductoFarmaceutico])
async def obtener_ultimos_productos(session: Session = Depends(get_session)):
    try:
        return get_ultimos_productos(session)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error recuperando últimos productos: {str(e)}"
        )
    
@router.get("/dashboard/metrics/last-registros", tags=["dashboard"], response_model=List[Registro])
async def obtener_ultimos_registros(session: Session = Depends(get_session)):
    try:
        return get_ultimos_registros(session)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error recuperando últimos registros: {str(e)}"
        )
    
@router.get("/dashboard/metrics/last-users", tags=["dashboard"], response_model=List[Registro])
async def obtener_ultimos_usuarios(session: Session = Depends(get_session)):
    try:
        return get_ultimos_usuarios(session)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error recuperando últimos registros: {str(e)}"
        )

