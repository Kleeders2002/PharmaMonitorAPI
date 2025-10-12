from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSON  # Si usas PostgreSQL, o usa Column(JSON) para otros DB
from sqlmodel import Column, JSON

if TYPE_CHECKING:
    from core.models.usuario import Usuario

class Registro(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    id_usuario: int = Field(foreign_key="usuario.idusuario", index=True)
    nombre_usuario: str = Field(max_length=255)  # Nuevo campo
    rol_usuario: str = Field(max_length=50)      # Nuevo campo
    fecha: datetime = Field(default_factory=datetime.utcnow, index=True)
    tipo_operacion: str = Field(max_length=20)  # Ej: "crear", "actualizar", "eliminar"
    entidad_afectada: str = Field(max_length=50)  # Ej: "ProductoFarmaceutico"
    detalles: dict = Field(sa_column=Column(JSON))  # Detalles del cambio en formato JSON

    # Relación con Usuario
    usuario: Optional["Usuario"] = Relationship(back_populates="registros")