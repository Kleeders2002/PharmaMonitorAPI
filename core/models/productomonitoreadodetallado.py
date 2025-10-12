# core/schemas/productomonitoreado.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ProductoMonitoreadoDetallado(BaseModel):
    id: int | None
    id_producto: int
    localizacion: str
    fecha_inicio_monitoreo: datetime
    fecha_finalizacion_monitoreo: Optional[datetime] = None  # Permite None
    cantidad: int
    nombre_producto: str | None
    foto_producto: str | None
    temperatura_min: float | None
    temperatura_max: float | None
    humedad_min: float | None
    humedad_max: float | None
    lux_min: float | None
    lux_max: float | None
    presion_min: float | None
    presion_max: float | None

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True