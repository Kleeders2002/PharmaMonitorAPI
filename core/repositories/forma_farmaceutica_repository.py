from sqlmodel import Session, select
from core.models.formafarmaceutica import FormaFarmaceutica

def get_formafarmaceutica(session: Session):
    return session.exec(select(FormaFarmaceutica)).all()

# def create_producto(session: Session, formafarmaceutica: FormaFarmaceutica):
#     session.add(formafarmaceutica)
#     session.commit()
#     session.refresh(formafarmaceutica)
#     return formafarmaceutica 