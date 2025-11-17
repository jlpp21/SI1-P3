from sqlalchemy import (
    Column, Integer, String, ForeignKey, Float, Boolean, Numeric, Text, DateTime
)
from sqlalchemy.orm import relationship
from db.db import Base


class Pelicula(Base):
    __tablename__ = "peliculas"

    id = Column(Integer, primary_key=True)
    titulo = Column(String(255), nullable=False)
    descripcion = Column(Text, nullable=True)
    anio = Column(Integer, nullable=False)
    genero = Column(String(100), nullable=True)
    precio = Column(Float, nullable=False)

    # añadidos P3
    stock = Column(Integer, nullable=False, default=100)
    valoracion_media = Column(Float, default=0.0)

    # relaciones
    actores = relationship(
        "Actor",
        secondary="peliculas_actores",
        back_populates="peliculas",
    )
    valoraciones = relationship("Valoracion", back_populates="pelicula")
    transacciones = relationship("Transaccion", back_populates="pelicula")
    carrito_items = relationship("CarritoPelicula", back_populates="pelicula")


class Actor(Base):
    __tablename__ = "actores"

    id = Column(Integer, primary_key=True)
    nombre = Column(String(255), nullable=False)
    apellido = Column(String(255), nullable=False)

    peliculas = relationship(
        "Pelicula",
        secondary="peliculas_actores",
        back_populates="actores",
    )


class PeliculaActor(Base):
    __tablename__ = "peliculas_actores"

    pelicula_id = Column(Integer, ForeignKey("peliculas.id"), primary_key=True)
    actor_id = Column(Integer, ForeignKey("actores.id"), primary_key=True)


class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(255), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(64), nullable=False)
    saldo = Column(Float, default=0.0)
    es_admin = Column(Boolean, default=False)

    # campos nuevos P3
    pais = Column(String(100), nullable=True)
    descuento_percent = Column(Numeric(5, 2), nullable=False, default=0)

    # relaciones
    transacciones = relationship("Transaccion", back_populates="cliente")
    valoraciones = relationship("Valoracion", back_populates="cliente")
    visualizaciones = relationship("ClientePelicula", back_populates="cliente")
    carritos = relationship("Carrito", back_populates="cliente")


class ClientePelicula(Base):
    __tablename__ = "cliente_pelicula"

    cliente_id = Column(Integer, ForeignKey("clientes.id"), primary_key=True)
    pelicula_id = Column(Integer, ForeignKey("peliculas.id"), primary_key=True)
    fecha_visualizacion = Column(DateTime)

    cliente = relationship("Cliente", back_populates="visualizaciones")
    pelicula = relationship("Pelicula")


class Valoracion(Base):
    __tablename__ = "valoraciones"

    cliente_id = Column(Integer, ForeignKey("clientes.id"), primary_key=True)
    pelicula_id = Column(Integer, ForeignKey("peliculas.id"), primary_key=True)
    puntuacion = Column(Integer, nullable=False)
    comentario = Column(Text, nullable=True)

    cliente = relationship("Cliente", back_populates="valoraciones")
    pelicula = relationship("Pelicula", back_populates="valoraciones")


class Transaccion(Base):
    __tablename__ = "transacciones"

    id = Column(Integer, primary_key=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False)
    pelicula_id = Column(Integer, ForeignKey("peliculas.id"), nullable=False)
    monto = Column(Float, nullable=False)
    fecha = Column(DateTime)       # coincide con schema.sql (TIMESTAMP)
    fecha_pago = Column(DateTime)  # añadida en actualiza.sql

    cliente = relationship("Cliente", back_populates="transacciones")
    pelicula = relationship("Pelicula", back_populates="transacciones")


# ======= Tablas nuevas de carrito (P3) =======

class Carrito(Base):
    __tablename__ = "carritos"

    id = Column(Integer, primary_key=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False)
    estado = Column(String(20), nullable=False, default="ABIERTO")
    total = Column(Float, nullable=False, default=0.0)

    cliente = relationship("Cliente", back_populates="carritos")
    items = relationship("CarritoPelicula", back_populates="carrito")


class CarritoPelicula(Base):
    __tablename__ = "carrito_peliculas"

    id = Column(Integer, primary_key=True)
    carrito_id = Column(Integer, ForeignKey("carritos.id"), nullable=False)
    pelicula_id = Column(Integer, ForeignKey("peliculas.id"), nullable=False)
    cantidad = Column(Integer, nullable=False)
    precio_unitario = Column(Float, nullable=False)

    carrito = relationship("Carrito", back_populates="items")
    pelicula = relationship("Pelicula", back_populates="carrito_items")
