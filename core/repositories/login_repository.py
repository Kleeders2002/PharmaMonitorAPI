# login_repository.py
from sqlmodel import Session, select
from core.models.usuario import Usuario
from passlib.context import CryptContext

# Crear un contexto de encriptación
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def authenticate_user(session: Session, email: str, password: str):
    # Buscar el usuario por correo
    statement = select(Usuario).where(Usuario.email == email)
    usuario = session.exec(statement).first()

    # Verificar si el usuario existe y si la contraseña es correcta
    if usuario and pwd_context.verify(password, usuario.password):
        return usuario
    return None
