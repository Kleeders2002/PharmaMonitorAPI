from sqlmodel import Session, select
from core.models.datomonitoreo import DatoMonitoreo
from passlib.context import CryptContext  # Asegúrate de tener esta librería para encriptar contraseñas


def get_datosmonitoreo(session: Session):
    return session.exec(
        select(DatoMonitoreo)
        .order_by(DatoMonitoreo.fecha.desc())
        # .limit(30)
    ).all()


def get_datosmonitoreo_by_id(session: Session, id: int):
    return session.exec(
        select(DatoMonitoreo)
        .where(DatoMonitoreo.id_producto_monitoreado == id)
        .order_by(DatoMonitoreo.fecha.desc())
        # .limit(30)
    ).all()

def create_dato_monitoreo(session: Session, dato: DatoMonitoreo) -> DatoMonitoreo:
    session.add(dato)
    session.commit()
    session.refresh(dato)
    return dato