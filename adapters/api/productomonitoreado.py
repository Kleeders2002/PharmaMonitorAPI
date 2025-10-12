from fastapi import APIRouter, Depends, HTTPException
from adapters.db.sqlmodel_database import get_session
from core.models.productomonitoreado import ProductoMonitoreado
from core.models.productomonitoreadodetallado import ProductoMonitoreadoDetallado
from datetime import datetime 
from dependencies import get_registro, get_current_user
from sqlmodel import Session
from core.models.usuario import UserRead
from core.ports.registro_port import RegistroPort

from core.repositories.producto_monitoreado_repository import (
    get_productos_monitoreados,
    get_productos_monitoreados_detalles,
    create_producto_monitoreado,
    stop_producto_monitoreado,
    get_producto_monitoreado_detalle
)

router = APIRouter()


@router.get("/productosmonitoreados/", response_model=list[ProductoMonitoreado])
def listar_productos_monitoreados(session=Depends(get_session)):
    return get_productos_monitoreados(session)

@router.get("/productosmonitoreados/detalles/{id}", response_model=ProductoMonitoreadoDetallado)
def obtener_producto_monitoreado(id: int, session = Depends(get_session)):
    db_producto = get_producto_monitoreado_detalle(session, id)
    
    if not db_producto:
        raise HTTPException(status_code=404, detail="Producto monitoreado no encontrado")
    
    return ProductoMonitoreadoDetallado(
        id=db_producto.id,
        id_producto=db_producto.id_producto,
        localizacion=db_producto.localizacion,
        fecha_inicio_monitoreo=db_producto.fecha_inicio_monitoreo,
        fecha_finalizacion_monitoreo=db_producto.fecha_finalizacion_monitoreo,
        cantidad=db_producto.cantidad,
        nombre_producto=db_producto.producto.nombre if db_producto.producto else None,
        foto_producto=db_producto.producto.foto if db_producto.producto else None,
        temperatura_min=db_producto.producto.condicion.temperatura_min if db_producto.producto and db_producto.producto.condicion else None,
        temperatura_max=db_producto.producto.condicion.temperatura_max if db_producto.producto and db_producto.producto.condicion else None,
        humedad_min=db_producto.producto.condicion.humedad_min if db_producto.producto and db_producto.producto.condicion else None,
        humedad_max=db_producto.producto.condicion.humedad_max if db_producto.producto and db_producto.producto.condicion else None,
        lux_min=db_producto.producto.condicion.lux_min if db_producto.producto and db_producto.producto.condicion else None,
        lux_max=db_producto.producto.condicion.lux_max if db_producto.producto and db_producto.producto.condicion else None,
        presion_min=db_producto.producto.condicion.presion_min if db_producto.producto and db_producto.producto.condicion else None,
        presion_max=db_producto.producto.condicion.presion_max if db_producto.producto and db_producto.producto.condicion else None
    )

@router.get("/productosmonitoreados/detalles", response_model=list[ProductoMonitoreadoDetallado])
def listar_productos_monitoreados(session = Depends(get_session)):
    db_productos = get_productos_monitoreados_detalles(session)
    
    return [
        ProductoMonitoreadoDetallado(
            id=producto.id,
            id_producto=producto.id_producto,
            localizacion=producto.localizacion,
            fecha_inicio_monitoreo=producto.fecha_inicio_monitoreo,
            fecha_finalizacion_monitoreo=producto.fecha_finalizacion_monitoreo,
            cantidad=producto.cantidad,
            nombre_producto=producto.producto.nombre if producto.producto else None,
            foto_producto=producto.producto.foto if producto.producto else None,
            temperatura_min=producto.producto.condicion.temperatura_min if producto.producto and producto.producto.condicion else None,
            temperatura_max=producto.producto.condicion.temperatura_max if producto.producto and producto.producto.condicion else None,
            humedad_min=producto.producto.condicion.humedad_min if producto.producto and producto.producto.condicion else None,
            humedad_max=producto.producto.condicion.humedad_max if producto.producto and producto.producto.condicion else None,
            lux_min=producto.producto.condicion.lux_min if producto.producto and producto.producto.condicion else None,
            lux_max=producto.producto.condicion.lux_max if producto.producto and producto.producto.condicion else None,
            presion_min=producto.producto.condicion.presion_min if producto.producto and producto.producto.condicion else None,
            presion_max=producto.producto.condicion.presion_max if producto.producto and producto.producto.condicion else None
        )
        for producto in db_productos
    ]



@router.post("/productosmonitoreados/", response_model=ProductoMonitoreado)
def crear_producto_monitoreado(
    producto_monitoreado: ProductoMonitoreado,
    session: Session = Depends(get_session),
    registro: RegistroPort = Depends(get_registro),  # Nueva dependencia
    current_user: UserRead = Depends(get_current_user)  # Nueva dependencia
):
    return create_producto_monitoreado(session, producto_monitoreado, registro, current_user)



@router.patch("/productosmonitoreados/{producto_id}/detener", response_model=ProductoMonitoreado)
def detener_monitoreo(
    producto_id: int,
    session: Session = Depends(get_session),
    registro: RegistroPort = Depends(get_registro),  # Nueva dependencia
    current_user: UserRead = Depends(get_current_user)  # Nueva dependencia
):
    db_producto = stop_producto_monitoreado(session, producto_id, registro, current_user)  # Modificado
    
    if not db_producto:
        raise HTTPException(status_code=404, detail="Producto monitoreado no encontrado")
    
    # Obtener detalles actualizados
    db_productos = get_productos_monitoreados(session)
    producto_detallado = next((p for p in db_productos if p.id == producto_id), None)
    
    if not producto_detallado:
        raise HTTPException(status_code=500, detail="Error al obtener detalles actualizados")
    
    return producto_detallado