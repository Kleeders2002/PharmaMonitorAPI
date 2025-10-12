from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from core.models.productofarmaceutico import ProductoFarmaceutico
    from core.models.datomonitoreo import DatoMonitoreo
    from core.models.alerta import Alerta

class ProductoMonitoreado(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    id_producto: int = Field(..., foreign_key="productofarmaceutico.id", index=True)
    localizacion: str = Field(..., max_length=255, index=True)
    fecha_inicio_monitoreo: datetime = Field(default_factory=datetime.utcnow)
    fecha_finalizacion_monitoreo: Optional[datetime] = Field(default=None)
    cantidad: int = Field(...)
    
    producto: Optional["ProductoFarmaceutico"] = Relationship(back_populates="productos_monitoreados")
    datos_monitoreo: List["DatoMonitoreo"] = Relationship(back_populates="productomonitoreado")
    alertas: List["Alerta"] = Relationship(back_populates="producto_monitoreado")
