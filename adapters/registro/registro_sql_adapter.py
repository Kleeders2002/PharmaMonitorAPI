# adapters/registro/registro_sql_adapter.py
from sqlmodel import Session
from core.models.registro import Registro
from core.ports.registro_port import RegistroPort
from datetime import datetime
from core.utils.datetime_utils import get_caracas_now

class RegistroSQLAdapter(RegistroPort):
    def __init__(self, session: Session):
        self.session = session  # <--- Self aquí referencia la instancia del adaptador
    
    def registrar(
        self,  # Self permite acceder a los atributos de la instancia
        usuario_id: int,
        nombre_usuario: str,  # Nuevos parámetros
        rol_usuario: str,
        operacion: str,
        entidad: str,
        entidad_id: int,
        detalles: dict
    ) -> None:
        nuevo_registro = Registro(
            id_usuario=usuario_id,
            nombre_usuario=nombre_usuario,
            rol_usuario=rol_usuario,
            tipo_operacion=operacion,
            entidad_afectada=entidad,
            id_entidad=entidad_id,
            detalles=detalles,
            fecha=get_caracas_now()
        )
        self.session.add(nuevo_registro)  # Accede al session de la instancia