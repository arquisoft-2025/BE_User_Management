from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from flasgger import Swagger
import bcrypt
from flask_jwt_extended import create_access_token, JWTManager
from password_generator import PasswordGenerator
from flask_mail import Mail, Message
import os
import requests
from flask_cors import CORS
from dotenv import load_dotenv
from prometheus_client import Counter, Histogram, generate_latest
import time
from functools import wraps

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)
# Allow local dev origins (Vite and Next dev servers)
CORS(app, supports_credentials=True, origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:3000"]) 

# Configuración de base de datos con variables de entorno
mysql_host = os.getenv('MYSQL_HOST', 'localhost')
mysql_port = os.getenv('MYSQL_PORT', '3306')
mysql_database = os.getenv('MYSQL_DATABASE', 'user_management')
mysql_user = os.getenv('MYSQL_USER', 'root')
mysql_password = os.getenv('MYSQL_PASSWORD', 'root')

app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+mysqlconnector://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}/{mysql_database}'
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

app.config["JWT_SECRET_KEY"] = os.getenv('JWT_SECRET_KEY', 'lkhjap8gy2p_03kt')
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


def send_mailjet_email(sender_email, recipient_email, subject, text):
    """Send an email using Mailjet API v3.1"""
    mj_public = os.getenv('MAILJET_API_KEY_PUBLIC')
    mj_private = os.getenv('MAILJET_API_KEY_PRIVATE')
    if not mj_public or not mj_private:
        raise RuntimeError("Mailjet API keys not configured in environment")

    url = "https://api.mailjet.com/v3.1/send"
    payload = {
      "Messages": [
        {
          "From": {"Email": sender_email},
          "To": [{"Email": recipient_email}],
          "Subject": subject,
          "TextPart": text
        }
      ]
    }
    resp = requests.post(url, json=payload, auth=(mj_public, mj_private), timeout=10)
    resp.raise_for_status()
    return resp.json()

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
    if bcrypt.checkpw(data["password"].encode('utf-8'), bytes(user.password)):
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
    data = request.get_json(silent=True)
    if not data or not data.get("email"):
        return jsonify({"error": "Campo 'email' requerido"}), 400

    user = User.query.filter_by(email=data.get("email")).first()
    if user is None:
        return jsonify({"mensaje": "El usuario no existe"}), 404

    # Generar nueva contraseña temporal
    new_pwd = PasswordGenerator().generate()
    sender = os.getenv('MAIL_SENDER') or os.getenv('MAIL_USERNAME')
    subject = "Recuperación de contraseña"
    body = f"Hola, tu nueva contraseña es: {new_pwd}"

    # Intentar enviar vía Mailjet API
    try:
        send_mailjet_email(sender, data.get("email"), subject, body)
    except Exception as e:
        app.logger.exception("Mailjet send failed for %s", data.get("email"))
        return jsonify({"error": "No se pudo enviar la nueva contraseña", "detail": str(e)}), 400

    # Si el envío fue exitoso, actualizar la contraseña en la base de datos
    try:
        user.password = bcrypt.hashpw(new_pwd.encode("utf-8"), bcrypt.gensalt())
        db.session.commit()
    except Exception as db_e:
        app.logger.exception("DB commit failed when saving new password for %s", data.get("email"))
        return jsonify({"error": "Error al actualizar la contraseña"}), 500

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
    app.run(host='0.0.0.0', debug=True, port=5002)

