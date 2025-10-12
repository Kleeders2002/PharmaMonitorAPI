from sqlmodel import SQLModel, Field
from typing import Optional

class Rol(SQLModel, table=True):
    idrol: Optional[int] = Field(default=None, primary_key=True, alias="ID_Rol")
    descripcion: str = Field(..., max_length=255, alias="Descripcion")