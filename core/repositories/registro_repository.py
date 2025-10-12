from sqlmodel import Session, select
from core.models.registro import Registro

def get_registros(session: Session):
    return session.exec(select(Registro)).all()