from fastapi import APIRouter, Depends, HTTPException, Response, Request
from fastapi.security import OAuth2PasswordBearer
from pydantic import EmailStr
from sqlmodel import Session
from jose import jwt, JWTError
from datetime import timedelta


from schemas.login import LoginData
from schemas.squemas import ForgotPasswordRequest, ResetPasswordRequest
from adapters.db.sqlmodel_database import get_session
from core.jwt_handler import create_access_token, create_refresh_token, get_current_user, SECRET_KEY, ALGORITHM
from core.repositories.login_repository import authenticate_user
from core.utils.utils_auth import send_email, generate_reset_token, validate_reset_token
from core.repositories.usuario_repository import get_usuario_by_email, update_usuario_password
from core.models.usuario import Usuario

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

router = APIRouter()

@router.post("/silent-renew")
def silent_renew(
    request: Request,
    response: Response,
    session: Session = Depends(get_session)
):
    try:
        # 1. Validar refresh token
        refresh_token = request.cookies.get("refresh_token")
        if not refresh_token:
            raise HTTPException(status_code=401, detail="Refresh token requerido")
        
        # 2. Extraer y decodificar token
        token = refresh_token.replace("Bearer ", "").strip()
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # 3. Verificar usuario en base de datos
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Token inválido")
        
        usuario = get_usuario_by_email(session, email)
        if not usuario:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        # 4. Generar nuevos tokens
        new_access_token = create_access_token({
            "sub": usuario.email,
            "id": usuario.idusuario,
            "rol": usuario.idrol,
            "nombre": usuario.nombre,
            "apellido": usuario.apellido,
            "foto": usuario.foto
        })
        
        new_refresh_token = create_refresh_token({"sub": usuario.email})

        # 5. Actualizar cookies
        response.set_cookie(
            key="access_token",
            value=f"Bearer {new_access_token}",
            httponly=True,
            secure=True,
            samesite="None",
            max_age= 15 * 60 # 15 segundos para pruebas
        )
        
        response.set_cookie(
            key="refresh_token",
            value=f"Bearer {new_refresh_token}",
            httponly=True,
            secure=True,
            samesite="None",
            max_age=7 * 24 * 60 * 60  # 7 días
        )
        
        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token
        }
    
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expirado")
    except (JWTError, AttributeError) as e:
        raise HTTPException(status_code=401, detail=f"Token inválido: {str(e)}")

@router.post("/login")
def login(data: LoginData, response: Response, session=Depends(get_session)):
    usuario = authenticate_user(session, data.email, data.password)
    if not usuario:
        raise HTTPException(status_code=400, detail="Correo o contraseña incorrectos")
    
    access_token = create_access_token({
        "sub": usuario.email,
        "id": usuario.idusuario,
        "rol": usuario.idrol,
        "nombre": usuario.nombre,
        "apellido": usuario.apellido,
        "foto": usuario.foto
    })
    
    refresh_token = create_refresh_token({"sub": usuario.email})

    response.set_cookie(
        key="access_token", 
        value=f"Bearer {access_token}",
        httponly=True,
        secure=True,
        samesite="None",
        max_age= 15 * 60
    )
    
    response.set_cookie(
        key="refresh_token",
        value=f"Bearer {refresh_token}",
        httponly=True,
        secure=True,
        samesite="None",
        max_age=7 * 24 * 60 * 60
    )

    return {
        "message": "Login exitoso",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": usuario
    }


@router.post("/refresh-token")
def refresh_token(request: Request, response: Response, session=Depends(get_session)):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token requerido")
    
    try:
        # Limpiar y validar token
        token = refresh_token.replace("Bearer ", "").strip()
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Buscar usuario
        usuario = session.query(Usuario).filter_by(email=payload["sub"]).first()
        if not usuario:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        # Generar nuevo access token
        new_access_token = create_access_token({
            "sub": usuario.email,
            "id": usuario.idusuario,
            "rol": usuario.idrol,
            "nombre": usuario.nombre,
            "apellido": usuario.apellido,
            "foto": usuario.foto
        })
        
        # Actualizar cookie
        response.set_cookie(
            key="access_token",
            value=f"Bearer {new_access_token}",
            httponly=True,
            secure=True,
            samesite="None",
            max_age= 15 * 60
        )
        
        return {"message": "Token actualizado"}
    
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expirado")
    except (JWTError, AttributeError):
        raise HTTPException(status_code=401, detail="Refresh token inválido")


# Endpoint /check-auth SIMPLIFICADO - Solo verifica autenticación, NO renueva tokens
@router.get("/check-auth")
async def check_auth(
    request: Request,
    response: Response,
    session: Session = Depends(get_session)
):
    """
    Verifica si el usuario está autenticado.
    IMPORTANTE: Este endpoint NO renueva tokens automáticamente.
    La renovación de tokens debe ser explícita mediante /silent-renew.
    Esto evita que después de un logout, el check-auth renueve el token
    basándose en un refresh token residual.
    """
    try:
        # Intentar obtener usuario con el access token actual
        user_data = get_current_user(request)
        return {"authenticated": True, "user": user_data}

    except HTTPException as e:
        # NO renovar automáticamente, solo retornar no autenticado
        # Si el token expiró, el frontend debe llamar explícitamente a /silent-renew
        return {"authenticated": False}

def verify_token(request: Request, grace_period: int = 0):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="No autenticado")
    
    token = token.replace("Bearer ", "").strip()
    try:
        # Añadir margen de gracia
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], options={"leeway": grace_period})
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")

@router.post("/logout")
def logout(response: Response):
    """
    Elimina las cookies de autenticación.
    IMPORTANTE: Para eliminar una cookie correctamente, se deben especificar
    los mismos parámetros con los que se creó (secure, httponly, samesite, path).
    """
    # Eliminar access_token con los mismos parámetros que se creó
    response.delete_cookie(
        key="access_token",
        path="/",
        secure=True,
        httponly=True,
        samesite="None"
    )
    # Eliminar refresh_token con los mismos parámetros que se creó
    response.delete_cookie(
        key="refresh_token",
        path="/",
        secure=True,
        httponly=True,
        samesite="None"
    )
    # También intentar con samesite="Lax" para mayor compatibilidad
    response.delete_cookie(
        key="access_token",
        path="/",
        samesite="Lax"
    )
    response.delete_cookie(
        key="refresh_token",
        path="/",
        samesite="Lax"
    )
    return {"message": "Logout exitoso"}


@router.get("/verificar-cookies")
def verificar_cookies(request: Request):
    cookies = request.cookies
    return {"cookies": cookies}


# En tu ruta de FastAPI para restablecimiento de contraseña
@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest, session: Session = Depends(get_session)):
    email = request.email
    usuario = get_usuario_by_email(session, email)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Generar token único para el restablecimiento de contraseña
    reset_token = generate_reset_token(email)
    
    # Usar HTTP en lugar de HTTPS para el enlace de restablecimiento de contraseña
    reset_link = f"http://localhost:3000/reset-password?token={reset_token}"
    send_email(email, "Restablece tu contraseña", f"Haz clic en este enlace para restablecer tu contraseña: {reset_link}")
    
    return {"message": "Correo enviado con éxito"}


@router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest, session=Depends(get_session)):
    # Validar el token
    email = validate_reset_token(request.token)
    
    if not email:
        raise HTTPException(status_code=400, detail="Token inválido o expirado")
    
    # Buscar al usuario con el correo
    usuario = get_usuario_by_email(session, email)
    if not usuario:  
        raise HTTPException(status_code=404, detail="Usuario no encontrado")         
    
    

    # Actualizar la contraseña del usuario
    update_usuario_password(session, usuario, request.new_password)

    return {"message": "Contraseña actualizada con éxito"} 


@router.get("/health")
async def health_check():
    return {"status": "OK", "version": "1.0.0"}