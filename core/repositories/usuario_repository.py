from sqlmodel import Session, select
from core.models.usuario import Usuario
from passlib.context import CryptContext  # Asegúrate de tener esta librería para encriptar contraseñas
from core.ports.registro_port import RegistroPort
from core.models.usuario import UserRead


# Crear un contexto para la encriptación de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_usuarios(session: Session):
    return session.exec(select(Usuario)).all()

# def get_current_user(session: Session, email: str):
#     return session.exec(select(Usuario).where(Usuario.email == email)).first()


def get_usuario_by_id(session: Session, id: int):
    return session.get(Usuario, id)


# Función para obtener usuario por email
def get_usuario_by_email(session: Session, email: str):
    return session.exec(select(Usuario).where(Usuario.email == email)).first()

def create_usuario(
    session: Session,
    usuario: Usuario,
    registro: RegistroPort,
    current_user: UserRead
):
    session.add(usuario)
    session.commit()
    session.refresh(usuario)
    
    # Registrar creación
    detalles = usuario.dict()
    sanitize_user_details(detalles)  # Eliminar datos sensibles

    if 'fechacreacion' in detalles:
        detalles['fechacreacion'] = detalles['fechacreacion'].isoformat()

    
    registro.registrar(
        usuario_id=current_user.id,
        nombre_usuario=current_user.nombre,
        rol_usuario=current_user.rol,
        operacion="crear",
        entidad="Usuario",
        entidad_id=usuario.idusuario,
        detalles=detalles
    )
    
    session.commit()
    return usuario

def update_usuario(
    session: Session,
    usuario: Usuario,
    registro: RegistroPort,
    current_user: UserRead,
    original_data: Usuario  # Cambiar el tipo a Usuario en lugar de dict
):
    session.commit()
    session.refresh(usuario)
    
    # Convertir ambos objetos a diccionarios
    nuevos_datos = usuario.__dict__  # Usar __dict__ para SQLAlchemy models
    original_dict = original_data.__dict__
    
    # Filtrar atributos internos de SQLAlchemy
    nuevos_datos = {k: v for k, v in nuevos_datos.items() if not k.startswith('_')}
    original_dict = {k: v for k, v in original_dict.items() if not k.startswith('_')}
    
    # Identificar cambios
    cambios = {
        key: {
            "anterior": original_dict.get(key),
            "nuevo": nuevos_datos.get(key)
        }
        for key in nuevos_datos if original_dict.get(key) != nuevos_datos.get(key)
    }
    
    if cambios:
        registro.registrar(
            usuario_id=current_user.id,
            nombre_usuario=current_user.nombre,
            rol_usuario=current_user.rol,
            operacion="actualizar",
            entidad="Usuario",
            entidad_id=usuario.idusuario,
            detalles=cambios
        )
    
    session.commit()
    return usuario

def delete_usuario(
    session: Session,
    usuario: Usuario,
    registro: RegistroPort,
    current_user: UserRead,
    detalles: dict
):
    sanitize_user_details(detalles)  # Limpiar datos sensibles

    if 'fechacreacion' in detalles:
        detalles['fechacreacion'] = detalles['fechacreacion'].isoformat()
    
    registro.registrar(
        usuario_id=current_user.id,
        nombre_usuario=current_user.nombre,
        rol_usuario=current_user.rol,
        operacion="eliminar",
        entidad="Usuario",
        entidad_id=usuario.idusuario,
        detalles=detalles
    )
    
    session.delete(usuario)
    session.commit()

# def update_usuario_password(
#     session: Session,
#     usuario: Usuario,
#     new_password: str,
#     registro: RegistroPort,
#     current_user: UserRead
# ):
#     # Capturar estado anterior del usuario
#     usuario_original = usuario.dict()
    
#     # Actualizar contraseña
#     usuario.password = pwd_context.hash(new_password)
#     session.add(usuario)
#     session.commit()
#     session.refresh(usuario)    
#     # Registrar el cambio sin exponer la contraseña
#     registro.registrar(
#         usuario_id=current_user.id,
#         nombre_usuario=current_user.nombre,
#         rol_usuario=current_user.rol,
#         operacion="actualizar",
#         entidad="Usuario",
#         entidad_id=usuario.idusuario,
#         detalles={
#             "campo_actualizado": "password",
#             "tipo_operacion": "Cambio de contraseña",
#             "detalles": "Contraseña actualizada exitosamente"
#         }
#     )
    
#     session.commit()
#     return usuario

# --- Función auxiliar ---
def sanitize_user_details(detalles: dict):
    campos_sensibles = ['hashed_password', 'password', 'token_recuperacion']
    for campo in campos_sensibles:
        detalles.pop(campo, None)
    return detalles

# Antes de los Registros

# Función para actualizar solo la contraseña
def update_usuario_password(session: Session, usuario: Usuario, new_password: str):
    usuario.password = pwd_context.hash(new_password)  # Encriptamos la nueva contraseña
    session.add(usuario)  # Agregar el usuario a la sesión para ser actualizado
    session.commit()  # Confirmar los cambios
    session.refresh(usuario)  # Refrescar la instancia del usuario con los datos actualizados de la base de datos
    return usuario

# def create_usuario(session: Session, usuario: Usuario):
#     session.add(usuario)
#     session.commit()
#     session.refresh(usuario)
#     return usuario

# def update_usuario(session: Session, usuario: Usuario):
#     session.commit()
#     session.refresh(usuario)
#     return usuario

# def delete_usuario(session: Session, usuario: Usuario):
#     session.delete(usuario)
#     session.commit()



