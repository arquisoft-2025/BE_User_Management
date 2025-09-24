// Script de inicialización para MongoDB
db = db.getSiblingDB('user_management');

// Crear colección de usuarios con índices
db.createCollection('users');

// Crear índice único para el email
db.users.createIndex({ "email": 1 }, { unique: true });

// Crear índice para búsquedas por nombre
db.users.createIndex({ "first_name": 1, "last_name": 1 });

// Crear índice para búsquedas por estado
db.users.createIndex({ "is_active": 1 });

// Insertar usuario administrador por defecto (opcional)
db.users.insertOne({
    "first_name": "Admin",
    "last_name": "User",
    "email": "admin@example.com",
    "password": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj5ZxiXqoXnO", // password: admin123
    "is_active": true,
    "created_at": new Date(),
    "updated_at": new Date()
});

print('Base de datos user_management inicializada correctamente');