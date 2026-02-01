from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from core.models.condicionalmacenamiento import CondicionAlmacenamiento
    from core.models.productomonitoreado import ProductoMonitoreado
    from core.models.formafarmaceutica import FormaFarmaceutica

class ProductoFarmaceutico(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    id_forma_farmaceutica: int = Field(..., foreign_key="formafarmaceutica.id", index=True)
    id_condicion: int = Field(..., foreign_key="condicionalmacenamiento.id", index=True)
    nombre: str = Field(..., max_length=255, index=True)
    formula: str = Field(..., max_length=255)
    concentracion: str = Field(..., max_length=255)
    indicaciones: str = Field(...)
    contraindicaciones: str = Field(...)
    efectos_secundarios: str = Field(...)
    foto: Optional[str] = Field(default=None, max_length=255)

    # Usar cadenas para las referencias
    condicion: Optional["CondicionAlmacenamiento"] = Relationship(back_populates="productos")
    productos_monitoreados: List["ProductoMonitoreado"] = Relationship(back_populates="producto")
    formafarmaceutica: Optional["FormaFarmaceutica"] = Relationship(back_populates="productos")