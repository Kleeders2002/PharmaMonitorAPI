from typing import Optional
from sqlmodel import SQLModel, Field
from core.models.condicion_read import CondicionRead
from core.models.formafarmaceutica_read import FormaFarmaceuticaRead

class ProductoFarmaceuticoRead(SQLModel):
    id: Optional[int] = Field(default=None, primary_key=True)
    id_forma_farmaceutica: int
    id_condicion: int
    nombre: str
    formula: str
    concentracion: str
    indicaciones: str
    contraindicaciones: str
    efectos_secundarios: str
    foto: Optional[str]
    # Relaciones anidadas
    condicion: CondicionRead
    formafarmaceutica: FormaFarmaceuticaRead
    is_related: Optional[bool] = None
