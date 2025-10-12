# dependencies.py (nuevo archivo)
from fastapi import Depends, Request, HTTPException
from sqlmodel import Session
from adapters.db.sqlmodel_database import get_session
from adapters.registro.registro_sql_adapter import RegistroSQLAdapter
from core.ports.registro_port import RegistroPort
from typing import Dict, Any
from core.jwt_handler import verify_token
from core.models.usuario import UserRead
from jose import JWTError


def get_registro(session: Session = Depends(get_session)) -> RegistroPort:
    return RegistroSQLAdapter(session)

# dependencies.py
def get_current_user(request: Request) -> UserRead:
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="No autenticado")
    
    try:
        token = token.replace("Bearer ", "")
        payload = verify_token(token)
        
        # Verificar campos esenciales
        if not all(key in payload for key in ["id", "sub", "nombre", "apellido", "foto", "rol"]):
            raise JWTError("Campos faltantes en el token")
        
        return UserRead(
            id=int(payload["id"]),
            email=payload["sub"],
            nombre=payload["nombre"],
            apellido=payload["apellido"],
            foto=payload["foto"],
            rol="Administrador" if payload["rol"] == 1 else "Usuario"
        )
    except (JWTError, KeyError, ValueError) as e:
        raise HTTPException(status_code=401, detail=f"Error de autenticación: {str(e)}") from e