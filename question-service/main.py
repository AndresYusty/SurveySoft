from flask import Flask
from controllers.question_controller import question_bp
from controllers.auth_controller import auth_bp
from database import init_db
from config import SECRET_KEY
from database import Base, engine
from models.survey import EvaluationForm  # Importa el modelo

app = Flask(__name__)
app.secret_key = SECRET_KEY  # Configura la clave secreta desde config.py
app.register_blueprint(question_bp, url_prefix='/question')
app.register_blueprint(auth_bp, url_prefix='/auth')  # Registrar el Blueprint de autenticación
Base.metadata.create_all(engine)

# Inicializa la base de datos
with app.app_context():
    init_db()

if __name__ == '__main__':
    app.run(port=5002, debug=True)
