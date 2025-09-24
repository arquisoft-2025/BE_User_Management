from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from flasgger import Swagger
import bcrypt
from flask_jwt_extended import create_access_token, JWTManager
from password_generator import PasswordGenerator
from flask_mail import Mail, Message
import os
from flask_cors import CORS
from dotenv import load_dotenv
from prometheus_client import Counter, Histogram, generate_latest
import time
from functools import wraps

app = Flask(__name__)
CORS(app, supports_credentials=True, origins=["http://localhost:5173"])
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:root@localhost/user_management'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
swagger = Swagger(app)
db = SQLAlchemy(app)

# MÉTRICAS
REQUEST_COUNT = Counter('user_management_http_requests_total', 'Total Requests', ['method', 'endpoint'])
REQUEST_LATENCY = Histogram('user_management_http_request_duration_seconds', 'Request Latency', ['endpoint'])
ERROR_COUNT = Counter('user_management_http_request_errors_total', 'Total Errors', ['endpoint'])

def monitor_metrics(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        endpoint = request.endpoint or 'unknown'
        method = request.method
        REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()
        try:
            response = f(*args, **kwargs)
            return response
        except Exception:
            ERROR_COUNT.labels(endpoint=endpoint).inc()
            raise
        finally:
            duration = time.time() - start_time
            REQUEST_LATENCY.labels(endpoint=endpoint).observe(duration)
    return decorated_function

# MODELO USER
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.LargeBinary(128), nullable=False)
    admin = db.Column(db.String(10), default="false")

with app.app_context():
    db.create_all()

app.config["JWT_SECRET_KEY"] = "lkhjap8gy2p 03kt"
jwt = JWTManager(app)
load_dotenv()
app.config.update(
    MAIL_USERNAME = os.getenv('MAIL_USERNAME'),
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD'),
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = 587,
    MAIL_USE_TLS = True,
    MAIL_USE_SSL = False,
)
mail = Mail(app)

@app.route('/register', methods=['POST'])
@monitor_metrics
def register():
    """
    Registra al usuario en el sistema
    ---
    parameters:
      - in: body
        name: user_information
        required: true
        schema:
          type: object
          properties:
            name:
              type: string
              example: Diego
            email:
              type: string
              example: prueba1@example.com
            password:
              type: string
              example: "12345678"
    responses:
      200:
        description: Usuario registrado
      400:
        description: Este email ya esta registrado o falta información
    """
    import logging
    try:
        data = request.get_json(force=True)
        nombre = data.get("name") or data.get("nombre")
        email = data.get("email")
        password = data.get("password")
        if not nombre or not email or not password:
            return jsonify({"error": "No hay informacion suficiente"}), 400
        try:
            hashed_pwd = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
            user = User(name=nombre, email=email, password=hashed_pwd)
            db.session.add(user)
            db.session.commit()
            return jsonify({"mensaje": "Usuario registrado"}), 200
        except IntegrityError:
            db.session.rollback()
            return jsonify({"error": "Este email ya esta registrado"}), 400
        except Exception as e:
            db.session.rollback()
            logging.exception("Error in /register endpoint")
            return jsonify({"error": "Error interno: " + str(e)}), 500
    except Exception as ex:
        logging.exception("Error parsing JSON")
        return jsonify({"error": "Invalid JSON"}), 400

@app.route('/login', methods=['POST'])
@monitor_metrics
def login():
    """
    Permite que el usuario inicie sesion dentro del sistema
    ---
    parameters:
      - in: body
        name: user_login_information
        required: true
        schema:
          type: object
          properties:
            email:
              type: string
              example: prueba1@example.com
            password:
              type: string
              example: "12345678"
    responses:
      200:
        description: login realizado correctamente
      400:
        description: Contraseña incorrecta
      404:
        description: El usuario no existe
    """
    data = request.get_json()
    user = User.query.filter_by(email=data.get("email")).first()
    if user is None:
        return jsonify({"mensaje": "El usuario no existe"}), 404
    if bcrypt.checkpw(data["password"].encode('utf-8'), user.password):
        return jsonify({
            "name": user.name,
            "email": user.email,
            "admin": user.admin,
            "access_token": create_access_token(identity=user.email)
        }), 200
    else:
        return jsonify({"mensaje": "Contraseña incorrecta"}), 400

@app.route('/recover', methods=['POST'])
@monitor_metrics
def recover():
    """
    Permite que el usuario pueda generar una nueva contraseña en caso de que haya olvidado la original
    ---
    parameters:
      - in: body
        name: user_login_information
        required: true
        schema:
          type: object
          properties:
            email:
              type: string
              example: prueba1@example.com
    responses:
      200:
        description: Contraseña entregada correctamente
      400:
        description: No se pudo enviar la contraseña
      404:
        description: El usuario no existe
    """
    data = request.get_json()
    user = User.query.filter_by(email=data.get("email")).first()
    if user is None:
        return jsonify({"mensaje": "El usuario no existe"}), 404
    new_pwd = PasswordGenerator().generate()
    user.password = bcrypt.hashpw(new_pwd.encode("utf-8"), bcrypt.gensalt())
    db.session.commit()
    msg = Message(
        subject="Recuperación de contraseña",
        sender=os.getenv('MAIL_USERNAME'),
        recipients=[data["email"]],
        body=f"Hola, tu nueva contraseña es: {new_pwd}"
    )
    try:
        mail.send(msg)
    except:
        return jsonify({"error": "No se pudo enviar la nueva contraseña"}), 400
    return jsonify({"mensaje": "La nueva contraseña fue entregada"}), 200

@app.route("/metrics", methods=["GET"])
def metrics():
    """
    Endpoint para exponer métricas de Prometheus
    ---
    tags:
      - Métricas
    responses:
      200:
        description: Métricas de Prometheus
        content:
          text/plain:
            schema:
              type: string
    """
    return generate_latest(), 200, {'Content-Type': 'text/plain; charset=utf-8'}

@app.after_request
def add_log_and_headers(response):
    try:
        if request.path.startswith('/register') or request.path.startswith('/login'):
            response.headers.setdefault('Content-Type', 'application/json; charset=utf-8')
        print(f"[LOG] {request.method} {request.path} -> {response.status_code}")
    except Exception:
        pass
    return response

if __name__ == "__main__":
  app.run(debug=True, port=5002)
