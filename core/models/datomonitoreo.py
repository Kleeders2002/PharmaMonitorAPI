from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from core.models.productomonitoreado import ProductoMonitoreado
    from core.models.alerta import Alerta

class DatoMonitoreo(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    id_producto_monitoreado: int = Field(..., foreign_key="productomonitoreado.id", index=True)
    fecha: datetime = Field(default_factory=datetime.utcnow, index=True)
    temperatura: float = Field(...)
    humedad: float = Field(...)
    lux: float = Field(...)
    presion: float = Field(...)

    productomonitoreado: Optional["ProductoMonitoreado"] = Relationship(back_populates="datos_monitoreo")
    alertas: List["Alerta"] = Relationship(back_populates="dato_monitoreo") 
    
