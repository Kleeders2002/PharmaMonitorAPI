from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from enum import Enum

# Definir ENUM para estados (opcional pero recomendado)
class EstadoAlerta(str, Enum):
    PENDIENTE = "pendiente"
    RESUELTA = "resuelta"

if TYPE_CHECKING:
    from core.models.productomonitoreado import ProductoMonitoreado
    from core.models.condicionalmacenamiento import CondicionAlmacenamiento
    from core.models.datomonitoreo import DatoMonitoreo

class Alerta(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Foreign Keys
    id_producto_monitoreado: int = Field(..., foreign_key="productomonitoreado.id", index=True)
    id_dato_monitoreo: Optional[int] = Field(default=None, foreign_key="datomonitoreo.id")
    id_condicion: int = Field(..., foreign_key="condicionalmacenamiento.id", index=True)
    
    # Atributos de la alerta
    parametro_afectado: str = Field(..., max_length=50)
    valor_medido: float = Field(...)
    limite_min: float = Field(...)
    limite_max: float = Field(...)
    mensaje: str = Field(...)
    fecha_generacion: datetime = Field(default_factory=datetime.now)
    estado: EstadoAlerta = Field(default=EstadoAlerta.PENDIENTE)
    fecha_resolucion: Optional[datetime] = None
    duracion_minutos: Optional[float] = None  # Duración total de la alerta
    
    # Relaciones
    producto_monitoreado: Optional["ProductoMonitoreado"] = Relationship(back_populates="alertas")
    dato_monitoreo: Optional["DatoMonitoreo"] = Relationship(back_populates="alertas")
    condicion: Optional["CondicionAlmacenamiento"] = Relationship(back_populates="alertas") 