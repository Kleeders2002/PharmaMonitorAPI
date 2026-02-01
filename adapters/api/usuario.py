from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from adapters.db.sqlmodel_database import get_session
from core.models.usuario import Usuario
from core.models.usuario import UserRead
from core.ports.registro_port import RegistroPort
from dependencies import get_registro, get_current_user
from core.repositories.usuario_repository import (
    get_usuarios, create_usuario, get_usuario_by_id, update_usuario, delete_usuario,
    get_usuario_by_email
)

router = APIRouter()

@router.get("/usuarios/", response_model=list[Usuario])
def listar_usuarios(session=Depends(get_session)):
    return get_usuarios(session)

@router.get("/usuarios/email/{email}", response_model=Usuario)
def obtener_usuario_por_email(email: str, session=Depends(get_session)):
    usuario = get_usuario_by_email(session, email)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuario

from schemas.squemas import ChangePasswordRequest  # Asegúrate de importar la clase



@router.get("/usuarios/{id}", response_model=Usuario)
def obtener_usuario(id: int, session=Depends(get_session)):
    usuario = get_usuario_by_id(session, id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuario


@router.post("/usuarios/", response_model=Usuario)
def crear_usuario(
    usuario: Usuario,
    session: Session = Depends(get_session),
    registro: RegistroPort = Depends(get_registro),
    current_user: UserRead = Depends(get_current_user)
):
    nuevo_usuario = create_usuario(session, usuario, registro, current_user)
    return nuevo_usuario

@router.put("/usuarios/{id}", response_model=Usuario)
def actualizar_usuario(
    id: int,
    usuario_actualizado: Usuario,
    session: Session = Depends(get_session),
    registro: RegistroPort = Depends(get_registro),
    current_user: UserRead = Depends(get_current_user)
):
    usuario = get_usuario_by_id(session, id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # Capturar datos antes de la actualización
    usuario_original = Usuario.from_orm(usuario)
    
    # Actualizar campos
    update_data = usuario_actualizado.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(usuario, key, value)

    return update_usuario(session, usuario, registro, current_user, usuario_original)

@router.delete("/usuarios/{id}")
def eliminar_usuario(
    id: int,
    session: Session = Depends(get_session),
    registro: RegistroPort = Depends(get_registro),
    current_user: UserRead = Depends(get_current_user)
):
    usuario = get_usuario_by_id(session, id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    detalles = usuario.dict()
    delete_usuario(session, usuario, registro, current_user, detalles)
    return {"detail": "Usuario eliminado exitosamente"}
