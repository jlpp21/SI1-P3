🎬 SI1 — Práctica 3
Microservicios, Transacciones, Triggers, Bloqueos y Optimización

Este proyecto implementa el backend completo de la Práctica 3 de SI1, siguiendo la arquitectura basada en microservicios (User Service y Catalog Service), una base de datos PostgreSQL y un conjunto de triggers, procedimientos almacenados y optimizaciones solicitadas en el enunciado.

📁 1. Estructura del proyecto
P3/
│
├── api/                 → Microservicios (user + catalog)
│   ├── api.py           → Catalog service (películas, carrito, checkout, consultas P3)
│   ├── user.py          → User service (registro, login, borrado)
│   ├── cliente.py       → Cliente de pruebas (P2)
│   ├── Dockerfile       → Imagen de los dos servicios (común)
│   └── requirements.txt → Dependencias Python
│
├── db/                  → Base de datos
│   ├── schema.sql       → Esquema base (P2)
│   ├── populate.sql     → Datos de ejemplo
│   ├── actualiza.sql    → Rediseño BBDD + triggers + proc. + modificación cascadas + pg_sleep
│   ├── optimizacion.sql → Índices para mejorar consultas exigidas
│   ├── models.py        → ORM SQLAlchemy
│   ├── db.py            → Conexión asíncrona a PostgreSQL
│   └── __init__.py
│
├── docker/              → Infraestructura
│   ├── docker-compose.yml → Orquesta la BD + user + catalog
│   └── init.sql           → Lanza schema → populate → actualiza
│
└── memoria/
    └── memoria.pdf      → Explicación de EXPLAIN, transacciones, bloqueos, triggers, etc.

🚀 2. Descripción general del sistema
Microservicio User (user.py)

✔ Registro de usuarios
✔ Login con token
✔ Borrado por admin
✔ Hash de contraseñas
✔ Compatible con P3 (atributos nuevos en BD)

Microservicio Catalog (api.py)

Incluye todo lo pedio en la práctica 3:

✔ /movies y /movies/<id>
✔ Carrito persistente en base de datos
✔ Uso de tablas:

carritos

carrito_peliculas

✔ Triggers automáticos:

actualización de stock

recálculo del total

descuento del cliente

creación de transacciones

actualización de saldo

fecha de pago

✔ Endpoint de pago /cart/checkout
✔ Añadido un pg_sleep dentro del trigger de pago para estudiar bloqueos/deadlocks
✔ Consultas P3:

/estadisticaVentas/<anio>/<pais>

/clientesSinPedidos

✔ Gestión de transacciones P3:

/borraPais/<pais>

/borraPaisIncorrecto/<pais>

/borraPaisIntermedio/<pais>

Base de datos (actualiza.sql)

Incluye:

✔ Nuevos campos:

clientes.pais

clientes.descuento_percent

peliculas.stock

peliculas.valoracion_media

transacciones.fecha_pago

✔ Nuevas tablas:

carritos

carrito_peliculas

✔ Triggers:

recálculo de total

actualización de stock

aplicación de descuento

facturación del carrito

actualización de valoración media

✔ Procedimientos almacenados:

recalc_total_carrito

recalc_valoracion_media

✔ pg_sleep(10) incluido para estudiar bloqueos/deadlocks
✔ Se han eliminado los ON DELETE CASCADE desde clientes, como pide el enunciado

Optimización

✔ optimizacion.sql añade los índices adecuados para que /estadisticaVentas use un plan eficiente (ver memoria EXPLAIN).

Docker

docker-compose.yml levanta:

PostgreSQL (con init automático)

User Service (puerto 5050)

Catalog Service (puerto 5051)

✔ 3. Cómo ejecutar el proyecto

Desde la carpeta P3/docker/:

docker compose up --build


Servicios disponibles:

Servicio	URL
User service	http://localhost:5050

Catalog service	http://localhost:5051

PostgreSQL	localhost:9999
📌 4. Características destacadas según enunciado

✔ Sin ON DELETE CASCADE en cliente

✔ Lógica transaccional completa para /borraPais*

✔ Deadlock reproducible con pg_sleep

✔ EXPLAIN optimizado

✔ Triggers automáticos que eliminan lógica de negocio en Python

✔ Carrito persistente en BD y no en memoria

🧪 5. Fichero de pruebas

Puedes ejecutar:

python cliente.py


(El cliente es el de P2, pero sirve para comprobar registro, login y catálogo.)

📄 6. Memoria

Incluye:

Explicación de los EXPLAIN antes/después

Justificación de índices

Análisis de transacciones y rollbacks

Bloqueos, espera y deadlock con pg_sleep

🎉 7. Estado final

➡️ El proyecto está completo, funciona, y cumple todas las especificaciones de la práctica 3.