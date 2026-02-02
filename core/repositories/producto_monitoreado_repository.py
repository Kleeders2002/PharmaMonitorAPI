# core/repositories/productomonitoreado_repository.py
from fastapi import HTTPException
from sqlmodel import Session, select
from core.models.productomonitoreado import ProductoMonitoreado
from core.models.productofarmaceutico import ProductoFarmaceutico
from core.models.alerta import Alerta, EstadoAlerta
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from core.models.usuario import UserRead
from core.ports.registro_port import RegistroPort
from core.utils.datetime_utils import get_caracas_now
import json

def get_productos_monitoreados(session: Session):
    return session.exec(select(ProductoMonitoreado)).all()


# En tu archivo de repositorios (ej: repositories/producto_monitoreado.py)
def get_producto_monitoreado_detalle(session: Session, id: int):
    query = (
        select(ProductoMonitoreado)
        .where(ProductoMonitoreado.id == id)
        .options(
            joinedload(ProductoMonitoreado.producto).joinedload(ProductoFarmaceutico.condicion)
        )
    )
    return session.exec(query).unique().first()


def get_productos_monitoreados_detalles(session: Session):
    query = (
        select(ProductoMonitoreado)
        .options(
            joinedload(ProductoMonitoreado.producto).joinedload(ProductoFarmaceutico.condicion)
        )
    )
    return session.exec(query).unique().all()

def create_producto_monitoreado(
    session: Session,
    producto_monitoreado: ProductoMonitoreado,
    registro: RegistroPort,
    current_user: UserRead
):
    # Validar que no exista un producto monitoreado activo
    # Un producto está activo si su fecha_finalizacion_monitoreo es None
    stmt = select(ProductoMonitoreado).where(
        ProductoMonitoreado.fecha_finalizacion_monitoreo == None
    )
    producto_activo = session.exec(stmt).first()

    if producto_activo:
        # Ya existe un producto con monitoreo activo
        nombre_producto_activo = (
            producto_activo.producto.nombre
            if producto_activo.producto
            else "Producto Desconocido"
        )
        raise HTTPException(
            status_code=400,
            detail={
                "error": "producto_activo_existe",
                "message": f"Ya existe un producto en monitoreo activo: '{nombre_producto_activo}' (ID: {producto_activo.id}). "
                          f"Solo se puede monitorear un producto a la vez. "
                          f"Detén el monitoreo actual antes de comenzar uno nuevo.",
                "producto_activo_id": producto_activo.id,
                "producto_activo_nombre": nombre_producto_activo
            }
        )

    session.add(producto_monitoreado)
    session.commit()
    session.refresh(producto_monitoreado)
    
    # Obtener el nombre del producto farmacéutico
    nombre_producto = (producto_monitoreado.producto.nombre 
                       if producto_monitoreado.producto 
                       else "Producto Desconocido")
    
    # Construir detalles del registro
    detalles = {
        "id": producto_monitoreado.id,
        "nombre_producto": nombre_producto,
        "id_producto_farmaceutico": producto_monitoreado.id_producto,
        "localizacion": producto_monitoreado.localizacion,
        "fecha_inicio_monitoreo": producto_monitoreado.fecha_inicio_monitoreo.isoformat(),
        "cantidad": producto_monitoreado.cantidad
    }
    
    registro.registrar(
        usuario_id=current_user.id,
        nombre_usuario=current_user.nombre,
        rol_usuario=current_user.rol,
        operacion="crear",
        entidad="ProductoMonitoreado",
        entidad_id=producto_monitoreado.id,  # Usar el ID del monitoreo, no del producto
        detalles=detalles
    )
    
    session.commit()
    return producto_monitoreado

def stop_producto_monitoreado(
    session: Session, 
    producto_id: int,
    registro: RegistroPort,
    current_user: UserRead
):
    producto = session.get(ProductoMonitoreado, producto_id)
    if producto:
        try:
            # 1. Actualizar fecha de finalización del producto
            fecha_fin = get_caracas_now()
            producto.fecha_finalizacion_monitoreo = fecha_fin
            
            # 2. Cerrar alertas asociadas pendientes
            alertas_pendientes = session.query(Alerta).filter(
                Alerta.id_producto_monitoreado == producto_id,
                Alerta.estado == EstadoAlerta.PENDIENTE
            ).all()
            
            for alerta in alertas_pendientes:
                alerta.estado = EstadoAlerta.RESUELTA
                alerta.fecha_resolucion = fecha_fin
                # Calcular duración en minutos
                if alerta.fecha_generacion:
                    duracion = (fecha_fin - alerta.fecha_generacion).total_seconds() / 60
                    alerta.duracion_minutos = round(duracion, 2)
            
            # 3. Commit de cambios
            session.commit()
            session.refresh(producto)
            
            # 4. Registrar la operación
            detalles = {
                "id_producto": producto.id,
                "nombre_producto": producto.producto.nombre if producto.producto else "N/A",
                "alertas_resueltas": len(alertas_pendientes),
                "fecha_inicio": producto.fecha_inicio_monitoreo.isoformat() if producto.fecha_inicio_monitoreo else "N/A",
                "fecha_fin": fecha_fin.isoformat(),
                "duracion_total_dias": (fecha_fin - producto.fecha_inicio_monitoreo).days if producto.fecha_inicio_monitoreo else 0
            }
            
            registro.registrar(
                usuario_id=current_user.id,
                nombre_usuario=current_user.nombre,
                rol_usuario=current_user.rol,
                operacion="detener",
                entidad="ProductoMonitoreado",
                entidad_id=producto.id,
                detalles=detalles
            )
            
            session.commit()

            return producto
            
        except SQLAlchemyError as e:
            session.rollback()
            raise HTTPException(status_code=500, detail=f"Error al detener monitoreo: {str(e)}")
    
    return None