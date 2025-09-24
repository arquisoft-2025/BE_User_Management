# API REST - Gestion y acceso de usuarios

API creada para la gestion de usuarios y acceso de usuarios dentro del sistema Donatello

## Ejecucion de la API

Para ejecutar la API primero hay que crear un entorno virtual y activarlo con los siguientes comandos:

```bash
python -m venv venv
.\venv\Scripts\activate
```

Una vez dentro del entorno virtual, se deben instalar las librerias usados con el siguiente comando:

```bash
pip install -r requirements.txt
```

Por ultimo se ejecuta la API con el siguiente comando:

```bash
python app.py
```

Esto hara que la API se ejecuta en la URL http://127.0.0.1:5002 y su documentacion en Swagger se encontrara en http://127.0.0.1:5002/apidocs

## Configuración de la Base de Datos (MySQL)

### 1. Instalar MySQL (si aún no lo tienes)
- Descargar desde: https://dev.mysql.com/downloads/installer/
- Durante la instalación, anota la contraseña del usuario `root`.

### 2. Agregar MySQL al PATH (opcional pero recomendado)
En Windows, agrega la carpeta `bin` de la instalación, por ejemplo:
```
C:\Program Files\MySQL\MySQL Server 8.0\bin
```

### 3. Crear la base de datos
Puedes usar el cliente de línea de comandos de MySQL:
```powershell
"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -p
```
Dentro del prompt de MySQL:
```sql
CREATE DATABASE user_management CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE user_management;
```
No necesitas crear manualmente la tabla `users`; SQLAlchemy la generará con `db.create_all()` al iniciar la aplicación.

### 4. Cadena de conexión
Actualmente la cadena está configurada en `app.py` como:
```
mysql+mysqlconnector://root:root@localhost/user_management
```
Si tu contraseña de root no es `root`, cámbiala en esa línea. Ejemplo:
```python
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:MI_PASSWORD@localhost/user_management'
```

### 5. Dependencias del conector
`requirements.txt` incluye `mysql-connector-python`. Si hay error de importación, instala manualmente:
```bash
pip install mysql-connector-python
```

## Endpoints disponibles

### POST /register

Encargado de registrar al usuario dentro del sistema

#### Ejemplo

URL: http://127.0.0.1:5002/register

Body:

```json
{
  "name": "Juan",
  "email": "example@example.com",
  "password": "1234"
}
```

Respuesta:

```json
{
  "mensaje": "Usuario registrado"
}
```

### POST /login

Encargado de permitir el login del usuarios, dandole un token de acceso tipo JWT

#### Ejemplo

URL: http://127.0.0.1:5002/login

Body:

```json
{
  "email": "example@example.com",
  "password": "1234"
}
```

Respuesta:

```json
{
  "name": "Juan",
  "email": "example@example.com",
  "admin": "false",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTc1MjI2NjU4MSwianRpIjoiMDhlOTkxNTMtNjVlMC00ZDI2LWI2MzktNDBiY2ExZmMzMGZiIiwidHlwZSI6ImFjY2VzcyIsInN1YiI6ImV4YW1wbGVAZXhhbXBsZS5jb20iLCJuYmYiOjE3NTIyNjY1ODEsImNzcmYiOiIzN2NhZjcxOC1kY2JiLTQ3ZDEtYmMxZC1mNzAwN2RhOWJmYWEiLCJleHAiOjE3NTIyNjc0ODF9.vU3pnee8AhmhbVhOP26mA_rTDQ4EdrrV8GTw9U5UfAI"
}
```

### POST /recover

Encargado de generar un nuevo clave para el usuario en caso de que haya perdido la original.

#### Ejemplo

URL: http://127.0.0.1:5002/recover

Body:

```json
{
  "email": "nofovag693@jxbav.com"
}
```

Respuesta:

```json
{
  "mensaje": "La nueva contraseña fue entregada"
}
```
