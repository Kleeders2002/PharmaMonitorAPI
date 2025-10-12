# core/ports/registro_port.py
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any

class RegistroPort(ABC):
    @abstractmethod
    def registrar(
        self,  # <--- ¡Aquí está self!
        usuario_id: id,
        nombre_usuario: str,  # Nuevo parámetro
        apellido_usuario: str,  # Nuevo parámetro
        rol_usuario: str,     # Nuevo parámetro
        operacion: str,
        entidad: str,
        entidad_id: int,
        detalles: Dict[str, Any]
    ) -> None:
        pass