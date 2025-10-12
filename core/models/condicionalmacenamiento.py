from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from core.models.productofarmaceutico import ProductoFarmaceutico
    from core.models.alerta import Alerta

class CondicionAlmacenamiento(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(..., max_length=255)
    temperatura_min: float = Field(...)
    temperatura_max: float = Field(...)
    humedad_min: float = Field(...)
    humedad_max: float = Field(...)
    lux_min: float = Field(...)
    lux_max: float = Field(...)
    presion_min: float = Field(...)
    presion_max: float = Field(...)
    fecha_actualizacion: datetime = Field(default_factory=datetime.utcnow, index=True)

    productos: List["ProductoFarmaceutico"] = Relationship(back_populates="condicion")
    alertas: List["Alerta"] = Relationship(back_populates="condicion")
