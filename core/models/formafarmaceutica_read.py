from typing import Optional
from sqlmodel import SQLModel, Field

class FormaFarmaceuticaRead(SQLModel):
    id: Optional[int] = Field(default=None, primary_key=True)
    descripcion: str
