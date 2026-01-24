from sqlmodel import Session, select
from sqlalchemy.sql import func
from core.models.usuario import Usuario
from core.models.productofarmaceutico import ProductoFarmaceutico
from core.models.alerta import Alerta, EstadoAlerta
from core.models.productomonitoreado import ProductoMonitoreado
from core.models.registro import Registro

def get_dashboard_metrics(session: Session):
    """Versión simple y confiable - ejecuta queries en secuencia"""
    
    usuarios_registrados = session.exec(
        select(func.count()).select_from(Usuario)
    ).one()
    
    productos_inventario = session.exec(
        select(func.count()).select_from(ProductoFarmaceutico)
    ).one()
    
    alertas_activas = session.exec(
        select(func.count())
        .where(Alerta.estado == EstadoAlerta.PENDIENTE)
        .select_from(Alerta)
    ).one()
    
    monitoreos_activos = session.exec(
        select(func.count())
        .where(ProductoMonitoreado.fecha_finalizacion_monitoreo == None)
    ).one()
    
    return {
        "usuarios_registrados": usuarios_registrados or 0,
        "productos_inventario": productos_inventario or 0,
        "alertas_activas": alertas_activas or 0,
        "monitoreos_activos": monitoreos_activos or 0
    }


def get_usuarios_test(session: Session):
    return session.exec(select(func.count()).select_from(Usuario)).one()

def get_ultimos_productos(session: Session):
    return session.exec(
        select(ProductoFarmaceutico)
        .order_by(ProductoFarmaceutico.id.desc())
        .limit(3)
    ).all()

def get_ultimos_registros(session: Session, limit: int = 10):
    return session.exec(
        select(Registro)
        .order_by(Registro.fecha.desc())
        .limit(limit)
    ).all()

def get_ultimos_usuarios(session: Session, limit: int = 10):
    return session.exec(
        select(Usuario)
        .order_by(Usuario.fecha.desc())
        .limit(limit)
    ).all()