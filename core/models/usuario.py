from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from typing import Optional, List



from pydantic import BaseModel, ConfigDict

from core.models.registro import Registro

class Usuario(SQLModel, table=True):
    idusuario: Optional[int] = Field(default=None, primary_key=True, alias="ID_Usuario")
    nombre: str = Field(..., max_length=100, alias="Nombre")
    apellido: str = Field(..., max_length=100, alias="Apellido")
    email: str = Field(..., max_length=255, unique=True, alias="Email")
    password: str = Field(..., max_length=255, alias="Contraseña")
    idrol: int = Field(..., foreign_key="rol.idrol", alias="ID_Rol")
    fechacreacion: datetime = Field(default_factory=datetime.utcnow, alias="Fecha_Creacion")
    foto: Optional[str] = Field(default=None, max_length=255)
    
    # Agrega la relación hacia Registro
    registros: List["Registro"] = Relationship(back_populates="usuario")


class UserRead(BaseModel):
    id: int
    email: str
    nombre: str
    apellido: str
    rol: str  # Nombre del rol, no el ID
    foto: str

    model_config = ConfigDict(
        from_attributes=True,  # Reemplaza orm_mode
        populate_by_name=True  # Nuevo nombre para allow_population_by_field_name
    ) 