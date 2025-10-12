from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List

from core.models.productofarmaceutico import ProductoFarmaceutico

class FormaFarmaceutica(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    descripcion: str = Field(..., max_length=255, index=True)
    productos: List["ProductoFarmaceutico"] = Relationship(back_populates="formafarmaceutica")
