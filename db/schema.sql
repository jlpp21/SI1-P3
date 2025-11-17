-- ==========================================
-- SCHEMA.SQL - PRACTICA 2 BASE PARA P3
-- ==========================================

-- Tabla de películas
CREATE TABLE peliculas (
    id SERIAL PRIMARY KEY,
    titulo VARCHAR(255) NOT NULL,
    descripcion TEXT,
    anio INT NOT NULL,
    genero VARCHAR(100),
    precio DECIMAL(10,2) NOT NULL
);

-- Tabla de actores
CREATE TABLE actores (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    apellido VARCHAR(255) NOT NULL
);

-- Relación muchos a muchos películas-actores
CREATE TABLE peliculas_actores (
    pelicula_id INT REFERENCES peliculas(id) ON DELETE CASCADE,
    actor_id INT REFERENCES actores(id) ON DELETE CASCADE,
    PRIMARY KEY (pelicula_id, actor_id)
);

-- Tabla de clientes
CREATE TABLE clientes (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(64) NOT NULL,
    saldo DECIMAL(10, 2) DEFAULT 0.00,
    es_admin BOOLEAN DEFAULT FALSE
);

-- Visualización de contenido por clientes
CREATE TABLE cliente_pelicula (
    cliente_id INT REFERENCES clientes(id) ON DELETE CASCADE,
    pelicula_id INT REFERENCES peliculas(id) ON DELETE CASCADE,
    fecha_visualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (cliente_id, pelicula_id)
);

-- Valoraciones de películas por clientes
CREATE TABLE valoraciones (
    cliente_id INT REFERENCES clientes(id) ON DELETE CASCADE,
    pelicula_id INT REFERENCES peliculas(id) ON DELETE CASCADE,
    puntuacion INT CHECK (puntuacion >= 1 AND puntuacion <= 5),
    comentario TEXT,
    PRIMARY KEY (cliente_id, pelicula_id)
);

-- Transacciones realizadas por los clientes
CREATE TABLE transacciones (
    id SERIAL PRIMARY KEY,
    cliente_id INT REFERENCES clientes(id) ON DELETE CASCADE,
    pelicula_id INT REFERENCES peliculas(id) ON DELETE CASCADE,
    monto DECIMAL(10, 2) NOT NULL,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
