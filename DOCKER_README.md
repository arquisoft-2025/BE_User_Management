# Docker Setup - User Management API

## Archivos Docker creados

1. **Dockerfile** - Imagen de la aplicación Flask
2. **docker-compose.yml** - Orquestación completa con MongoDB y Prometheus
3. **.dockerignore** - Optimización del build
4. **init-mongo.js** - Inicialización de la base de datos
5. **prometheus.yml** - Configuración de métricas

## Comandos para ejecutar

### Opción 1: Solo la aplicación
```bash
# Construir la imagen
docker build -t user-management-api .

# Ejecutar el contenedor (necesitas MongoDB ejecutándose por separado)
docker run -p 5002:5002 -e MONGO_URI="mongodb://localhost:27017/user_management" user-management-api
```

### Opción 2: Stack completo con docker-compose (RECOMENDADO)
```bash
# Levantar todos los servicios
docker-compose up -d

# Ver logs
docker-compose logs -f

# Detener servicios
docker-compose down

# Detener y eliminar volúmenes
docker-compose down -v
```

## Servicios incluidos

- **user_management_api**: API Flask en puerto 5002
- **mongodb**: Base de datos MongoDB en puerto 27017
- **prometheus**: Sistema de métricas en puerto 9090

## URLs de acceso

- API: http://localhost:5002
- Swagger UI: http://localhost:5002/apidocs
- Prometheus: http://localhost:9090
- MongoDB: mongodb://admin:password123@localhost:27017

## Variables de entorno

Puedes crear un archivo `.env` con:
```
MONGO_URI=mongodb://admin:password123@mongodb:27017/user_management?authSource=admin
FLASK_ENV=production
JWT_SECRET_KEY=your-secret-key
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
```

## Notas importantes

1. El usuario por defecto de MongoDB es `admin:password123`
2. Se crea un usuario administrador con email `admin@example.com` y password `admin123`
3. Las métricas de Prometheus están disponibles en `/metrics`
4. Los datos se persisten en volúmenes Docker