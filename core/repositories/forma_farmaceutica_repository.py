from sqlmodel import Session, select
from core.models.formafarmaceutica import FormaFarmaceutica

def get_formafarmaceutica(session: Session):
    return session.exec(select(FormaFarmaceutica)).all()