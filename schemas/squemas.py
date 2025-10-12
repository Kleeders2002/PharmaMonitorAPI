from pydantic import BaseModel, EmailStr
from fastapi import Form


class ChangePasswordRequest(BaseModel):
    new_password: str = Form(...)  # Ahora espera un campo de formulario

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str