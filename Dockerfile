# Usar Python 3.11 como imagen base
FROM python:3.11-slim

# Establecer directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema necesarias para MySQL
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivos de requisitos
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código fuente
COPY . .

# Crear usuario no-root para mayor seguridad
RUN useradd --create-home --shell /bin/bash app && chown -R app:app /app
USER app

# Exponer puerto
EXPOSE 5002

# Variables de entorno por defecto
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Comando por defecto
CMD ["python", "app.py"]