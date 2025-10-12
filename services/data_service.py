from sqlmodel import Session
from core.repositories import dato_monitoreo_repository, alerta_repository
from typing import AsyncGenerator
from core.models.datomonitoreo import DatoMonitoreo

async def procesar_datos(datos: AsyncGenerator[DatoMonitoreo, None], session: Session):
    async for dato in datos:
        try:
            # Guardar dato en DB
            db_dato = dato_monitoreo_repository.create_dato_monitoreo(session, dato)
            
            # Generar alerta si es necesario
            alerta = alerta_repository.crear_alerta(session, db_dato)
            
        except Exception as e:
            print(f"Error procesando dato: {str(e)}")