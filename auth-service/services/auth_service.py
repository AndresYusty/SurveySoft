from werkzeug.security import generate_password_hash, check_password_hash
from models.user import User
from database import SessionLocal
from sqlalchemy.exc import IntegrityError
import secrets
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os


def create_user(username, password, email=None, role='user'):
    session = SessionLocal()

    # Verifica si el nombre de usuario ya existe
    existing_user = session.query(User).filter_by(username=username).first()
    if existing_user:
        session.close()
        return None

    try:
        hashed_password = generate_password_hash(password)
        user = User(username=username, password=hashed_password, email=email, role=role)
        session.add(user)
        session.commit()
        return user
    except IntegrityError:
        session.rollback()
        return None
    finally:
        session.close()

def authenticate_user(username, password):
    session = SessionLocal()
    user = session.query(User).filter_by(username=username).first()
    session.close()

    # Verifica si el usuario existe y la contraseña es correcta
    if user and check_password_hash(user.password, password):
        return user
    return None

def generate_reset_token():
    """Genera un token único para restablecer la contraseña"""
    return secrets.token_urlsafe(32)

def send_reset_email(email, token):
    """Envía un correo electrónico con el enlace para restablecer la contraseña"""
    # Configuración del servidor SMTP (ajusta según tu proveedor de correo)
    smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    smtp_username = os.getenv('SMTP_USERNAME')
    smtp_password = os.getenv('SMTP_PASSWORD')

    if not all([smtp_username, smtp_password]):
        raise ValueError("Las credenciales SMTP no están configuradas")

    # Crear mensaje
    msg = MIMEMultipart()
    msg['From'] = smtp_username
    msg['To'] = email
    msg['Subject'] = "Recuperación de Contraseña - SurveySoft"

    # Crear el cuerpo del mensaje
    reset_url = f"http://localhost:5001/auth/reset-password/{token}"
    body = f"""
    Hola,

    Has solicitado restablecer tu contraseña en SurveySoft. 
    Para restablecer tu contraseña, haz clic en el siguiente enlace:

    {reset_url}

    Este enlace expirará en 1 hora.

    Si no solicitaste este cambio, puedes ignorar este correo.

    Saludos,
    El equipo de SurveySoft
    """
    msg.attach(MIMEText(body, 'plain'))

    try:
        # Conectar al servidor SMTP
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        
        # Enviar correo
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Error al enviar correo: {e}")
        return False

def request_password_reset(email):
    """Inicia el proceso de recuperación de contraseña"""
    session = SessionLocal()
    user = session.query(User).filter_by(email=email).first()
    
    if not user:
        session.close()
        return False, "No se encontró ninguna cuenta asociada a ese correo electrónico."
    
    if not user.email:
        session.close()
        return False, "Esta cuenta no tiene un correo electrónico registrado. Por favor, contacta al administrador."

    # Generar token y establecer fecha de expiración
    token = generate_reset_token()
    expires = datetime.utcnow() + timedelta(hours=1)
    
    # Actualizar usuario con el token
    user.reset_token = token
    user.reset_token_expires = expires
    session.commit()
    session.close()

    # Enviar correo electrónico
    if send_reset_email(email, token):
        return True, "Se han enviado las instrucciones a tu correo electrónico."
    else:
        return False, "Hubo un error al enviar el correo electrónico. Por favor, intenta nuevamente más tarde."

def reset_password(token, new_password):
    """Restablece la contraseña usando el token"""
    session = SessionLocal()
    user = session.query(User).filter_by(reset_token=token).first()
    
    if not user or user.reset_token_expires < datetime.utcnow():
        session.close()
        return False

    # Actualizar contraseña y limpiar token
    user.password = generate_password_hash(new_password)
    user.reset_token = None
    user.reset_token_expires = None
    session.commit()
    session.close()
    
    return True
