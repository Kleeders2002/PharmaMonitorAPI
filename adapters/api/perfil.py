from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from adapters.db.sqlmodel_database import get_session
from core.models.usuario import Usuario
from core.models.usuario import UserRead
from core.ports.registro_port import RegistroPort
from dependencies import get_registro, get_current_user
from core.repositories.usuario_repository import (get_usuario_by_id)

from core.repositories.perfil_repository import (
    update_perfil, update_usuario_password
)

from schemas.squemas import ChangePasswordRequest

# from core.utils.utils_auth import generate_reset_token, validate_reset_token  # Para el token

router = APIRouter()

@router.get("/perfil", response_model=UserRead)
def obtener_usuario_actual(
    current_user: Usuario = Depends(get_current_user)
):
    return current_user


@router.put("/perfil", response_model=Usuario)
def actualizar_perfil(
    usuario_actualizado: Usuario,  # O un esquema de actualización específico
    current_user: Usuario = Depends(get_current_user),
    session: Session = Depends(get_session),
    registro: RegistroPort = Depends(get_registro)
):
    # Obtenemos el usuario actual desde la base de datos usando el id del usuario autenticado.
    usuario = get_usuario_by_id(session, current_user.id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Capturamos el estado actual antes de modificar
    usuario_original = Usuario.from_orm(usuario)
    
    # Actualizamos solo los campos que se han enviado (excluyendo los que no se envían)
    update_data = usuario_actualizado.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(usuario, key, value)
    
    # Llamamos a la función del repositorio para actualizar y registrar la operación.
    return update_perfil(session, usuario, registro, current_user, usuario_original)
    # usuario_actualizado_db = update_perfil(session, usuario, registro, current_user, usuario_original)
    # return UserRead.from_orm(usuario_actualizado_db)  # Conversión a UserRead

@router.put("/perfil/password", response_model=Usuario)
def cambiar_contrasena(
    request: ChangePasswordRequest,
    session: Session = Depends(get_session),
    registro: RegistroPort = Depends(get_registro),
    current_user: UserRead = Depends(get_current_user)  

):
    id = current_user.id

    usuario = get_usuario_by_id(session, id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    return update_usuario_password(
        session, 
        usuario, 
        request.new_password,
        registro,
        current_user
    )


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
