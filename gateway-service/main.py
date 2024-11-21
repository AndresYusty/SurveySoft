from flask import Flask, redirect, request

app = Flask(__name__)

# Ruta para el servicio de autenticación
@app.route('/auth/<path:path>', methods=['GET', 'POST'])
def auth_service(path):
    return redirect(f"http://localhost:5001/auth/{path}", code=307)

# Ruta para el servicio de preguntas (question-service)
@app.route('/question/<path:path>', methods=['GET', 'POST'])
def question_service(path):
    return redirect(f"http://localhost:5002/question/{path}", code=307)

@app.route('/question/', methods=['GET'])
def question_home():
    return redirect("http://localhost:5002/question/home", code=307)

# Ruta para el servicio de evaluaciones
@app.route('/evaluation/<path:path>', methods=['GET', 'POST'])
def evaluation_service(path):
    return redirect(f"http://localhost:5003/evaluation/{path}", code=307)

if __name__ == '__main__':
    app.run(port=5000, debug=True)
