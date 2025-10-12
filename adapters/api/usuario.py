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
# from core.utils.utils_auth import generate_reset_token, validate_reset_token  # Para el token

router = APIRouter()

@router.get("/usuarios/", response_model=list[Usuario])
def listar_usuarios(session=Depends(get_session)):
    return get_usuarios(session)


# @router.get("/usuarios/me", response_model=UserRead)
# def obtener_usuario_actual(
#     current_user: Usuario = Depends(get_current_user)
# ):
#     return current_user


# @router.put("/usuarios/me", response_model=UserRead)
# def actualizar_usuario_actual(
#     usuario_actualizado: Usuario,  # O un esquema de actualización específico
#     current_user: Usuario = Depends(get_current_user),
#     session: Session = Depends(get_session),
#     registro: RegistroPort = Depends(get_registro)
# ):
#     # Obtenemos el usuario actual desde la base de datos usando el id del usuario autenticado.
#     usuario = get_usuario_by_id(session, current_user.id)
#     if not usuario:
#         raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
#     # Capturamos el estado actual antes de modificar
#     usuario_original = Usuario.from_orm(usuario)
    
#     # Actualizamos solo los campos que se han enviado (excluyendo los que no se envían)
#     update_data = usuario_actualizado.dict(exclude_unset=True)
#     for key, value in update_data.items():
#         setattr(usuario, key, value)
    
#     # Llamamos a la función del repositorio para actualizar y registrar la operación.
#     return update_usuario(session, usuario, registro, current_user, usuario_original)




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

# @router.put("/usuarios/{id}/cambiar_contrasena", response_model=Usuario)
# def cambiar_contrasena(
#     id: int,
#     request: ChangePasswordRequest,
#     session: Session = Depends(get_session),
#     registro: RegistroPort = Depends(get_registro),
#     current_user: UserRead = Depends(get_current_user)
# ):
#     usuario = get_usuario_by_id(session, id)
#     if not usuario:
#         raise HTTPException(status_code=404, detail="Usuario no encontrado")

#     return update_usuario_password(
#         session, 
#         usuario, 
#         request.new_password,
#         registro,
#         current_user
#     )

# Antes de los Registros

# @router.post("/usuarios/", response_model=Usuario)
# def crear_usuario(usuario: Usuario, session=Depends(get_session)):
#     return create_usuario(session, usuario)

# @router.put("/usuarios/{id}", response_model=Usuario)
# def actualizar_usuario(id: int, usuario_actualizado: Usuario, session=Depends(get_session)):
#     usuario = get_usuario_by_id(session, id)
#     if not usuario:
#         raise HTTPException(status_code=404, detail="Usuario no encontrado")

#     usuario.nombre = usuario_actualizado.nombre
#     usuario.apellido = usuario_actualizado.apellido
#     usuario.email = usuario_actualizado.email
#     usuario.idrol = usuario_actualizado.idrol
#     usuario.foto = usuario_actualizado.foto
#     return update_usuario(session, usuario)

# @router.delete("/usuarios/{id}")
# def eliminar_usuario(id: int, session=Depends(get_session)):
#     usuario = get_usuario_by_id(session, id)
#     if not usuario:
#         raise HTTPException(status_code=404, detail="Usuario no encontrado")
#     delete_usuario(session, usuario)
#     return {"detail": "Usuario eliminado exitosamente"}


# @router.put("/usuarios/{id}/cambiar_contrasena", response_model=Usuario)
# def cambiar_contrasena(id: int, request: ChangePasswordRequest, session = Depends(get_session)):
#     usuario = get_usuario_by_id(session, id)
#     if not usuario:
#         raise HTTPException(status_code=404, detail="Usuario no encontrado")

#     return update_usuario_password(session, usuario, request.new_password)
