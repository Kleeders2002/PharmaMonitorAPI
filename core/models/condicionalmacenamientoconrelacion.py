from pydantic import BaseModel
from datetime import datetime

class CondicionAlmacenamientoConRelacion(BaseModel):
    id: int
    nombre: str
    temperatura_min: float
    temperatura_max: float
    humedad_min: float
    humedad_max: float
    lux_min: float
    lux_max: float
    presion_min: float
    presion_max: float
    fecha_actualizacion: datetime
    is_related: bool

    class Config:
        orm_mode = True
