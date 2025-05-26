import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# Configuración de la URI de la base de datos MySQL
# DATABASE_URI = "mysql+pymysql://root:Manchas12345.@localhost:3308/auth_service_db"

# Configuración de la base de datos
DATABASE_URL = os.getenv('DATABASE_URL', 'mysql+pymysql://root:Manchas12345.@localhost:3308/auth_service_db')

# Configuración del servidor SMTP
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SMTP_USERNAME = os.getenv('SMTP_USERNAME')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')

# Clave secreta para la aplicación
SECRET_KEY = os.getenv('SECRET_KEY', 'auth_service_secret_key_12345')
