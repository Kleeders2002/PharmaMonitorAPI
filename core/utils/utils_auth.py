from datetime import datetime, timedelta
from jose import jwt
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import jwt

SECRET_KEY = "123456123456"
ALGORITHM = "HS256"

def generate_reset_token(email: str):
    expire = datetime.utcnow() + timedelta(hours=1)  # Token expira en 1 hora
    payload = {
        "sub": email,  # Aquí aseguramos que el email esté en "sub"
        "exp": expire
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token

def validate_reset_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise Exception("Token inválido")
        return email
    except Exception:
        raise Exception("Token inválido o expirado")

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

def send_email(to_email: str, subject: str, body: str):
    from_email = "kleesteban270@gmail.com"
    password = "xsqo kowv fkcf hhmh"  # Usa la contraseña de aplicación generada

    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject

    # Especificar la codificación UTF-8
    msg.attach(MIMEText(body, 'plain', 'utf-8'))

    try:
        logging.info("Configurando el servidor SMTP")
        server = smtplib.SMTP('smtp.gmail.com', 587)  # Usa 465 para SSL si prefieres
        server.starttls()
        server.login(from_email, password)
        logging.info("Inicio de sesión SMTP exitoso")
        text = msg.as_string()
        server.sendmail(from_email, to_email, text)
        logging.info("Correo enviado exitosamente a %s", to_email)
        server.quit()
    except Exception as e: 
        logging.error(f"Error al enviar el correo: {e}")







