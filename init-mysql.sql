-- Script de inicialización para MySQL
-- Crear base de datos si no existe
CREATE DATABASE IF NOT EXISTS user_management;

-- Usar la base de datos
USE user_management;

-- Crear tabla de usuarios (SQLAlchemy la creará automáticamente, pero esto es para referencia)
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password VARBINARY(128) NOT NULL,
    admin VARCHAR(10) DEFAULT 'false',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_email (email),
    INDEX idx_admin (admin)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insertar usuario administrador por defecto (la contraseña debe ser hasheada por la aplicación)
-- Este es solo un ejemplo, la aplicación debe insertar usuarios con bcrypt
INSERT IGNORE INTO users (name, email, password, admin) 
VALUES ('Administrator', 'admin@example.com', 'change_this_password', 'true');

-- Crear usuario de aplicación con permisos
CREATE USER IF NOT EXISTS 'user_app'@'%' IDENTIFIED BY 'userpass123';
GRANT ALL PRIVILEGES ON user_management.* TO 'user_app'@'%';
FLUSH PRIVILEGES;

SELECT 'Base de datos user_management inicializada correctamente' AS mensaje;