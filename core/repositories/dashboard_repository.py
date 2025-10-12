from sqlmodel import Session, select
from sqlalchemy.sql import func
from core.models.usuario import Usuario
from core.models.productofarmaceutico import ProductoFarmaceutico
from core.models.alerta import Alerta, EstadoAlerta
from core.models.productomonitoreado import ProductoMonitoreado
from core.models.registro import Registro

def get_dashboard_metrics(session: Session):
    def count_usuarios():
        return session.exec(select(func.count()).select_from(Usuario)).one()
    
    def count_productos():
        return session.exec(select(func.count()).select_from(ProductoFarmaceutico)).one()
    
    def count_alertas_activas():
        return session.exec(select(func.count()).where(Alerta.estado == EstadoAlerta.PENDIENTE).select_from(Alerta)).one()
    
    def count_monitoreos_activos():
        return session.exec(select(func.count()).where(ProductoMonitoreado.fecha_finalizacion_monitoreo == None)).one()
    
    from concurrent.futures import ThreadPoolExecutor
    
    with ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(count_usuarios),
            executor.submit(count_productos),
            executor.submit(count_alertas_activas),
            executor.submit(count_monitoreos_activos)
        ]
        
        results = [f.result() for f in futures]
    
    return {
        "usuarios_registrados": results[0] or 0,
        "productos_inventario": results[1] or 0,
        "alertas_activas": results[2] or 0,
        "monitoreos_activos": results[3] or 0
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