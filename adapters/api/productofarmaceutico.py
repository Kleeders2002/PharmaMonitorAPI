from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from adapters.db.sqlmodel_database import get_session
from core.models.productofarmaceutico import ProductoFarmaceutico
from core.models.producto_farmaceutico_read import ProductoFarmaceuticoRead
from core.models.usuario import UserRead
from core.ports.registro_port import RegistroPort
from dependencies import get_registro, get_current_user
from core.repositories.producto_farmaceutico_repository import (
    get_productos,
    create_producto,
    get_producto_by_id,
    update_producto,
    delete_producto
)

router = APIRouter()

@router.get("/productos/", response_model=list[ProductoFarmaceuticoRead])
def listar_productos(session: Session = Depends(get_session)):
    return get_productos(session)

@router.post("/productos/", response_model=ProductoFarmaceuticoRead)
def crear_producto(
    producto: ProductoFarmaceutico,
    session: Session = Depends(get_session),
    Registro: RegistroPort = Depends(get_registro),
    current_user: UserRead = Depends(get_current_user)
):
    return create_producto(session, producto, Registro, current_user)

@router.put("/productos/{id}", response_model=ProductoFarmaceuticoRead)
def actualizar_producto(
    id: int,
    producto_actualizado: ProductoFarmaceutico,
    session: Session = Depends(get_session),
    Registro: RegistroPort = Depends(get_registro),
    current_user: UserRead = Depends(get_current_user)
):
    producto = get_producto_by_id(session, id)
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    # Actualizar campos
    for key, value in producto_actualizado.dict(exclude_unset=True).items():
        setattr(producto, key, value)

    return update_producto(session, producto, Registro, current_user)

@router.delete("/productos/{id}")
def eliminar_producto(
    id: int,
    session: Session = Depends(get_session),
    Registro: RegistroPort = Depends(get_registro),
    current_user: UserRead = Depends(get_current_user)
):
    producto = get_producto_by_id(session, id)
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    delete_producto(session, producto, Registro, current_user)
    return {"detail": "Producto eliminado exitosamente"}