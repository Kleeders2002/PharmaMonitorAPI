from sqlmodel import Session, select
from core.models.usuario import Usuario
from passlib.context import CryptContext  # Asegúrate de tener esta librería para encriptar contraseñas
from core.ports.registro_port import RegistroPort
from core.models.usuario import UserRead


# Crear un contexto para la encriptación de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_current_user(session: Session, email: str):
    return session.exec(select(Usuario).where(Usuario.email == email)).first()

def update_perfil(
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
            entidad="Perfil",
            entidad_id=usuario.idusuario,
            detalles=cambios
        )
    
    session.commit()
    return usuario

def update_usuario_password(
    session: Session,
    usuario: Usuario,
    new_password: str,
    registro: RegistroPort,
    current_user: UserRead
):
    
    # Actualizar contraseña
    usuario.password = pwd_context.hash(new_password)
    session.add(usuario)
    session.commit()
    session.refresh(usuario)    
    # Registrar el cambio sin exponer la contraseña
    registro.registrar(
        usuario_id=current_user.id,
        nombre_usuario=current_user.nombre,
        rol_usuario=current_user.rol,
        operacion="actualizar",
        entidad="Perfil",
        entidad_id=usuario.idusuario,
        detalles={
            "campo_actualizado": "password",
            "tipo_operacion": "Cambio de contraseña",
            "detalles": "Contraseña actualizada exitosamente"
        }
    )
    
    session.commit()
    return usuario