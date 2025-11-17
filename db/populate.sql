-- Insertar películas
INSERT INTO peliculas (titulo, descripcion, anio, genero, precio) VALUES
('Inception', 'Un ladrón que roba secretos mediante la tecnología de los sueños.', 2010, 'Ciencia ficción', 10.00),
('The Matrix', 'Un hacker descubre que la realidad es una simulación.', 1999, 'Acción', 8.50),
('The Dark Knight', 'Batman lucha contra el Joker en Gotham City.', 2008, 'Acción', 9.00),
('Pulp Fiction', 'Historias entrelazadas del crimen en Los Ángeles.', 1994, 'Drama', 7.50);

-- Insertar actores
INSERT INTO actores (nombre, apellido) VALUES
('Leonardo', 'DiCaprio'),
('Keanu', 'Reeves'),
('Christian', 'Bale'),
('John', 'Travolta');

-- Insertar relaciones entre películas y actores
INSERT INTO peliculas_actores (pelicula_id, actor_id) VALUES
(1, 1),
(2, 2),
(3, 3),
(4, 4);

-- Usuario admin
INSERT INTO clientes (nombre, email, password_hash, saldo, es_admin)
VALUES (
  'admin',
  'admin@example.com',
  '8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918',
  0.00,
  TRUE
);

-- Usuarios normales
INSERT INTO clientes (nombre, email, password_hash, saldo, es_admin) VALUES
('Carlos Pérez', 'carlos.perez@email.com',
 '3c01bdbb26f358bab27f267924aa2c9a03fcfdb8b9b1d6d7b1e0e3f6d2b1b7e3', 50.00, FALSE),
('Ana García', 'ana.garcia@email.com',
 '2c1743a391305fbf367df8e4f069f9f9a44fbdc2437a0e1c4c8f6b4e7d6f9b8e', 20.00, FALSE),
('Luis Martínez','luis.martinez@email.com',
 '6b3a55e0261b0304143f805a2491b8269b28e44a2e5fcd4e7ed1e7e8e9a43f8b', 100.00, FALSE);

-- Relación de visualización
INSERT INTO cliente_pelicula (cliente_id, pelicula_id) VALUES
(1, 1),
(1, 2),
(2, 3),
(3, 4);

-- Valoraciones
INSERT INTO valoraciones (cliente_id, pelicula_id, puntuacion, comentario) VALUES
(1, 1, 5, 'Increíble película, un clásico moderno'),
(2, 3, 4, 'Muy buena película, pero algo larga'),
(3, 4, 5, 'Una obra maestra del cine');

-- Transacciones
INSERT INTO transacciones (cliente_id, pelicula_id, monto) VALUES
(1, 1, 10.00),
(2, 3, 8.00),
(3, 4, 7.00);
