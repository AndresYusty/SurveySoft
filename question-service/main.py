from flask import Flask
from controllers.question_controller import question_bp
from controllers.auth_controller import auth_bp
from controllers.history_controller import history_bp
from database import init_db
from config import SECRET_KEY
from database import Base, engine
from models.survey import EvaluationForm
from controllers.risk_controller import risk_bp

import logging


app = Flask(__name__)
# Configurar el logger
logging.basicConfig(level=logging.DEBUG)
app.logger.setLevel(logging.DEBUG)

app.secret_key = SECRET_KEY  # Configura la clave secreta desde config.py
app.register_blueprint(question_bp, url_prefix='/question')
app.register_blueprint(auth_bp, url_prefix='/auth')  # Registrar el Blueprint de autenticación
app.register_blueprint(history_bp, url_prefix='/history')  # Registrar el Blueprint de historial
app.register_blueprint(risk_bp, url_prefix='/risks')



Base.metadata.create_all(engine)

# Inicializa la base de datos
with app.app_context():
    init_db()
    
    # Inicializar las secciones específicas de ISO 25000
    try:
        from services.survey_service import initialize_iso25000_sections
        initialize_iso25000_sections()
    except Exception as e:
        app.logger.error(f"Error al inicializar las secciones ISO 25000: {e}")

if __name__ == '__main__':
    app.run(port=5002, debug=True)
