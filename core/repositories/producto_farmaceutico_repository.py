from sqlalchemy.orm import joinedload
from sqlalchemy import select, exists
from sqlmodel import Session
from core.models.productofarmaceutico import ProductoFarmaceutico
from core.models.producto_farmaceutico_read import ProductoFarmaceuticoRead
from core.models.productomonitoreado import ProductoMonitoreado
from core.models.formafarmaceutica import FormaFarmaceutica
from core.models.condicionalmacenamiento import CondicionAlmacenamiento

from core.models.usuario import UserRead
from core.ports.registro_port import RegistroPort


def get_productos(session: Session):
    productos_bd = session.exec(
        select(ProductoFarmaceutico)
        .options(
            joinedload(ProductoFarmaceutico.condicion),
            joinedload(ProductoFarmaceutico.formafarmaceutica)
        )
    ).scalars().all()
    
    productos_read = []
    for producto in productos_bd:
        # Verificar si tiene productos monitoreados (EXACTAMENTE como en condiciones)
        is_related = session.exec(
            select(exists().where(ProductoMonitoreado.id_producto == producto.id))
        ).scalar_one()

        # Mapeo manteniendo tu estructura actual + el campo is_related
        producto_read = ProductoFarmaceuticoRead(
            id=producto.id,
            id_forma_farmaceutica=producto.id_forma_farmaceutica,
            id_condicion=producto.id_condicion,
            nombre=producto.nombre,
            formula=producto.formula,
            concentracion=producto.concentracion,
            indicaciones=producto.indicaciones,
            contraindicaciones=producto.contraindicaciones,
            efectos_secundarios=producto.efectos_secundarios,
            foto=producto.foto,
            condicion=producto.condicion,
            formafarmaceutica=producto.formafarmaceutica,
            is_related=is_related  # Nuevo campo agregado
        )
        productos_read.append(producto_read)
    
    return productos_read




# def get_producto_by_id(session: Session, id: int) -> ProductoFarmaceutico:
#     producto = session.exec(
#         select(ProductoFarmaceutico)
#         .where(ProductoFarmaceutico.id == id)
#         .options(
#             selectinload(ProductoFarmaceutico.condicion),
#             selectinload(ProductoFarmaceutico.formafarmaceutica)
#         )
#     ).first()
#     return producto

def get_producto_by_id(session: Session, id: int):
    return session.get(ProductoFarmaceutico, id)

def create_producto(
    session: Session,
    producto: ProductoFarmaceutico,
    registro: RegistroPort,
    usuario_actual: UserRead
):
    session.add(producto)
    session.commit()
    session.refresh(producto)
    
    detalles = producto.dict()

    # Obtener nombre de la forma farmacéutica
    forma_farmaceutica = session.query(FormaFarmaceutica).get(producto.id_forma_farmaceutica)
    detalles["forma_farmaceutica"] = forma_farmaceutica.descripcion if forma_farmaceutica else "Desconocido"
    del detalles["id_forma_farmaceutica"]  # Eliminar el campo del ID
    
    # Obtener nombre de la condición (ajusta el nombre del modelo según tu aplicación)
    condicion = session.query(CondicionAlmacenamiento).get(producto.id_condicion)
    detalles["condicion"] = condicion.nombre if condicion else "Desconocido"
    del detalles["id_condicion"]  # Eliminar el campo del ID

    # Formatear campos datetime si existen
    if 'fecha_creacion' in detalles:
        detalles["fecha_creacion"] = detalles["fecha_creacion"].isoformat()
    
    registro.registrar(
        usuario_id=usuario_actual.id,
        nombre_usuario=usuario_actual.nombre,
        rol_usuario=usuario_actual.rol,
        operacion="crear",
        entidad="ProductoFarmaceutico",
        entidad_id=producto.id,
        detalles=detalles
    )
    
    session.commit()
    return producto

def update_producto(
    session: Session,
    producto: ProductoFarmaceutico,
    registro: RegistroPort,
    usuario_actual: UserRead
):
    session.commit()
    session.refresh(producto)
    
    # Obtener detalles del producto
    detalles = producto.dict()
    
    # Obtener nombre de la forma farmacéutica
    forma_farmaceutica = session.query(FormaFarmaceutica).get(producto.id_forma_farmaceutica)
    detalles["forma_farmaceutica"] = forma_farmaceutica.descripcion if forma_farmaceutica else "Desconocido"
    del detalles["id_forma_farmaceutica"]  # Eliminar el campo del ID
    
    # Obtener nombre de la condición (ajusta el nombre del modelo según tu aplicación)
    condicion = session.query(CondicionAlmacenamiento).get(producto.id_condicion)
    detalles["condicion"] = condicion.nombre if condicion else "Desconocido"
    del detalles["id_condicion"]  # Eliminar el campo del ID
    
    # Formatear campos datetime si existen
    if 'fecha_actualizacion' in detalles:
        detalles["fecha_actualizacion"] = detalles["fecha_actualizacion"].isoformat()
    
    registro.registrar(
        usuario_id=usuario_actual.id,
        nombre_usuario=usuario_actual.nombre,
        rol_usuario=usuario_actual.rol,
        operacion="actualizar",
        entidad="ProductoFarmaceutico",
        entidad_id=producto.id,
        detalles=detalles
    )
    
    session.commit()
    return producto

def delete_producto(
    session: Session,
    producto: ProductoFarmaceutico,
    registro: RegistroPort,
    usuario_actual: UserRead
):
    entidad_id = producto.id
    detalles = producto.dict()

    # Obtener nombre de la forma farmacéutica
    forma_farmaceutica = session.query(FormaFarmaceutica).get(producto.id_forma_farmaceutica)
    detalles["forma_farmaceutica"] = forma_farmaceutica.descripcion if forma_farmaceutica else "Desconocido"
    del detalles["id_forma_farmaceutica"]  # Eliminar el campo del ID
    
    # Obtener nombre de la condición (ajusta el nombre del modelo según tu aplicación)
    condicion = session.query(CondicionAlmacenamiento).get(producto.id_condicion)
    detalles["condicion"] = condicion.nombre if condicion else "Desconocido"
    del detalles["id_condicion"]  # Eliminar el campo del ID
    
    # Formatear campos datetime si existen
    if 'fecha_eliminacion' in detalles:
        detalles["fecha_eliminacion"] = detalles["fecha_eliminacion"].isoformat()
    
    session.delete(producto)
    
    registro.registrar(
        usuario_id=usuario_actual.id,
        nombre_usuario=usuario_actual.nombre,
        rol_usuario=usuario_actual.rol,
        operacion="eliminar",
        entidad="ProductoFarmaceutico",
        entidad_id=entidad_id,
        detalles=detalles
    )
    
    session.commit()


# Antes de los registros

# def create_producto(session: Session, producto: ProductoFarmaceutico):
#     session.add(producto)
#     session.commit()
#     session.refresh(producto)
#     return producto

# def update_producto(session: Session, producto: ProductoFarmaceutico):
#     session.commit()
#     session.refresh(producto)
#     return producto

# def delete_producto(session: Session, producto: ProductoFarmaceutico):
#     session.delete(producto)
#     session.commit()