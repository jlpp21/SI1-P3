from __future__ import annotations

from datetime import datetime
from typing import Dict, List, TypedDict  # ya casi no lo usamos, pero no molesta

from quart import Quart, request, jsonify, abort
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from db.db import async_session
from db.models import (
    Pelicula,
    Cliente,
    Transaccion,
    Carrito,
    CarritoPelicula,
)

app = Quart(__name__)


# ----------------------------
# Helpers de acceso a BD
# ----------------------------
async def get_movie_by_id(session: AsyncSession, movie_id: int):
    result = await session.execute(select(Pelicula).where(Pelicula.id == movie_id))
    return result.scalars().first()


async def get_or_create_open_cart(session: AsyncSession, client_id: int) -> Carrito:
    """
    Devuelve el carrito ABIERTO del cliente, o lo crea si no existe.
    """
    result = await session.execute(
        select(Carrito).where(
            Carrito.cliente_id == client_id,
            Carrito.estado == "ABIERTO",
        )
    )
    cart = result.scalars().first()
    if cart:
        return cart

    cart = Carrito(cliente_id=client_id, estado="ABIERTO", total=0.0)
    session.add(cart)
    await session.flush()  # para que tenga id
    return cart


# ----------------------------
# Rutas existentes (tipo P2)
# ----------------------------

@app.route("/movies", methods=["GET"])
async def get_movies():
    params = request.args
    title = params.get("title")
    genre = params.get("genre")
    actor = params.get("actor")  # pendiente: join con actores
    year = params.get("year")

    async with async_session() as session:
        query = select(Pelicula)
        if title:
            query = query.where(Pelicula.titulo.ilike(f"%{title}%"))
        if genre:
            query = query.where(Pelicula.genero.ilike(f"%{genre}%"))
        if year:
            try:
                query = query.where(Pelicula.anio == int(year))
            except ValueError:
                abort(400, "Invalid year")
        # actor pendiente

        result = await session.execute(query)
        movies = result.scalars().all()

        return jsonify([{
            "movieid": m.id,
            "title": m.titulo,
            "description": m.descripcion,
            "year": m.anio,
            "genre": m.genero,
            "price": float(m.precio),
        } for m in movies])


@app.route("/movies/<int:movie_id>", methods=["GET"])
async def get_movie_details(movie_id: int):
    async with async_session() as session:
        movie = await get_movie_by_id(session, movie_id)
        if not movie:
            abort(404, "Movie not found")
        return jsonify({
            "movieid": movie.id,
            "title": movie.titulo,
            "description": movie.descripcion,
            "year": movie.anio,
            "genre": movie.genero,
            "price": float(movie.precio),
        })


# ======================================================
# CARRITO usando tablas carritos + carrito_peliculas
# (stock, total, saldo y transacciones via TRIGGERS)
# ======================================================

@app.route("/cart/<int:movie_id>", methods=["PUT"])
async def add_to_cart(movie_id: int):
    """
    Añade una película al carrito del cliente en la BBDD.
    Espera JSON: { "client_id": <id> }

    - Usa carritos + carrito_peliculas
    - Los triggers actualizan stock y total
    - Si la película ya está en el carrito: 409 CONFLICT
    """
    data = await request.get_json(force=True, silent=True) or {}
    client_id = data.get("client_id")
    if client_id is None:
        abort(400, "Client ID is required")

    try:
        client_id = int(client_id)
    except Exception:
        abort(400, "Client ID must be an integer")

    async with async_session() as session:
        # Comprobar que el cliente existe
        res_cli = await session.execute(select(Cliente).where(Cliente.id == client_id))
        cliente = res_cli.scalars().first()
        if not cliente:
            abort(404, "Client not found")

        movie = await get_movie_by_id(session, movie_id)
        if not movie:
            abort(404, "Movie not found")

        # Carrito ABIERTO del cliente (o se crea)
        cart = await get_or_create_open_cart(session, client_id)

        # ¿La película ya está en el carrito?
        res_item = await session.execute(
            select(CarritoPelicula).where(
                CarritoPelicula.carrito_id == cart.id,
                CarritoPelicula.pelicula_id == movie.id,
            )
        )
        existing_item = res_item.scalars().first()
        if existing_item:
            # Misma semántica que en P2: no permitir duplicados
            abort(409, "Movie already in cart")

        # Insertar línea de carrito (cantidad=1)
        item = CarritoPelicula(
            carrito_id=cart.id,
            pelicula_id=movie.id,
            cantidad=1,
            precio_unitario=float(movie.precio),
        )
        session.add(item)

        # Los triggers se encargan de:
        #  - restar stock
        #  - recalcular total del carrito
        await session.commit()

        return jsonify({
            "cartid": cart.id,
            "movieid": movie.id,
            "message": "Added to cart",
        }), 200


@app.route("/cart", methods=["GET"])
async def get_cart():
    """
    Devuelve el contenido del carrito ABIERTO del cliente.
    Espera query param: ?client_id=<id>
    """
    client_id = request.args.get("client_id")
    if client_id is None:
        abort(400, "Client ID is required")
    try:
        client_id = int(client_id)
    except Exception:
        abort(400, "Client ID must be an integer")

    async with async_session() as session:
        # Carrito abierto del cliente
        res_cart = await session.execute(
            select(Carrito).where(
                Carrito.cliente_id == client_id,
                Carrito.estado == "ABIERTO",
            )
        )
        cart = res_cart.scalars().first()
        if not cart:
            return jsonify([])

        # Items del carrito + datos de la película
        res_items = await session.execute(
            select(CarritoPelicula, Pelicula)
            .join(Pelicula, CarritoPelicula.pelicula_id == Pelicula.id)
            .where(CarritoPelicula.carrito_id == cart.id)
        )
        rows = res_items.all()

        return jsonify([
            {
                "movieid": pelicula.id,
                "title": pelicula.titulo,
                "price": float(item.precio_unitario),
                "quantity": item.cantidad,
            }
            for (item, pelicula) in rows
        ])


@app.route("/cart/checkout", methods=["POST"])
async def checkout_cart():
    """
    Pago del carrito ABIERTO del cliente:

    - Calcula el total (usando carritos.total)
    - Aplica el descuento del cliente
    - Si saldo insuficiente -> 402 PAYMENT_REQUIRED
    - Si saldo suficiente -> pone el carrito en estado 'PAGADO'
      y LOS TRIGGERS:
        * descuentan saldo
        * crean transacciones
        * ponen fecha_pago
    """
    data = await request.get_json(force=True, silent=True) or {}
    client_id = data.get("client_id")
    if client_id is None:
        abort(400, "Client ID is required")
    try:
        client_id = int(client_id)
    except Exception:
        abort(400, "Client ID must be an integer")

    async with async_session() as session:
        # Cliente
        res_cli = await session.execute(select(Cliente).where(Cliente.id == client_id))
        cliente = res_cli.scalars().first()
        if not cliente:
            abort(404, "Client not found")

        # Carrito ABIERTO
        res_cart = await session.execute(
            select(Carrito).where(
                Carrito.cliente_id == client_id,
                Carrito.estado == "ABIERTO",
            )
        )
        cart = res_cart.scalars().first()
        if not cart:
            return jsonify({"message": "Cart is empty", "total": 0.0})

        total_original = float(cart.total)
        descuento = float(cliente.descuento_percent or 0.0)
        total_con_descuento = total_original * (1 - descuento / 100.0)

        # Comprobación de saldo (la actualización real la hace el TRIGGER)
        if float(cliente.saldo) < total_con_descuento:
            abort(402, "Insufficient funds")

        # Marcar carrito como PAGADO -> dispara trigger trg_carrito_pagar
        cart.estado = "PAGADO"
        session.add(cart)
        await session.commit()

        return jsonify({
            "message": "Checkout successful",
            "cartid": cart.id,
            "total_original": total_original,
            "discount_percent": descuento,
            "total_charged": total_con_descuento,
        })


@app.route("/user/credit", methods=["POST"])
async def add_credit():
    data = await request.get_json(force=True, silent=True) or {}
    client_id = data.get("client_id")
    amount = data.get("amount")

    if client_id is None or amount is None:
        abort(400, "Client ID and amount are required")

    try:
        client_id = int(client_id)
        amount = float(amount)
        if amount <= 0:
            raise ValueError()
    except Exception:
        abort(400, "Amount must be a positive number")

    async with async_session() as session:
        res = await session.execute(select(Cliente).where(Cliente.id == client_id))
        cliente = res.scalars().first()
        if not cliente:
            abort(404, "Client not found")

        cliente.saldo = float(cliente.saldo) + amount
        await session.commit()

        return jsonify({"message": "Credit added", "new_credit": float(cliente.saldo)})


# ======================================================
#  ENDPOINTS NUEVOS PRACTICA 3
# ======================================================

@app.route("/estadisticaVentas/<int:anio>/<pais>", methods=["GET"])
async def estadistica_ventas(anio: int, pais: str):
    """
    Devuelve las ventas (transacciones) de un año y país.
    Usa la tabla transacciones y clientes.
    """
    query = text("""
        SELECT t.id AS transaccion_id,
               t.cliente_id,
               c.nombre AS cliente_nombre,
               c.pais AS cliente_pais,
               t.pelicula_id,
               t.monto,
               t.fecha AS fecha
        FROM transacciones t
        JOIN clientes c ON t.cliente_id = c.id
        WHERE EXTRACT(YEAR FROM t.fecha) = :anio
          AND c.pais = :pais
        ORDER BY t.fecha
    """)

    async with async_session() as session:
        result = await session.execute(query, {"anio": anio, "pais": pais})
        rows = result.mappings().all()

    return jsonify([dict(r) for r in rows])


@app.route("/clientesSinPedidos", methods=["GET"])
async def clientes_sin_pedidos():
    """
    Devuelve clientes que no tienen ninguna transacción.
    """
    query = text("""
        SELECT c.id, c.nombre, c.email, c.pais, c.saldo
        FROM clientes c
        LEFT JOIN transacciones t ON t.cliente_id = c.id
        WHERE t.id IS NULL
        ORDER BY c.id;
    """)

    async with async_session() as session:
        result = await session.execute(query)
        rows = result.mappings().all()

    return jsonify([dict(r) for r in rows])


# helpers de SQL para los deletes por país
BORRADO_SQL = {
    "cliente_pelicula": """
        DELETE FROM cliente_pelicula
        WHERE cliente_id IN (SELECT id FROM clientes WHERE pais = :pais);
    """,
    "valoraciones": """
        DELETE FROM valoraciones
        WHERE cliente_id IN (SELECT id FROM clientes WHERE pais = :pais);
    """,
    "transacciones": """
        DELETE FROM transacciones
        WHERE cliente_id IN (SELECT id FROM clientes WHERE pais = :pais);
    """,
    "carrito_peliculas": """
        DELETE FROM carrito_peliculas
        WHERE carrito_id IN (
            SELECT id FROM carritos
            WHERE cliente_id IN (SELECT id FROM clientes WHERE pais = :pais)
        );
    """,
    "carritos": """
        DELETE FROM carritos
        WHERE cliente_id IN (SELECT id FROM clientes WHERE pais = :pais);
    """,
    "clientes": """
        DELETE FROM clientes
        WHERE pais = :pais;
    """,
}


@app.route("/borraPais/<pais>", methods=["POST"])
async def borra_pais(pais: str):
    """
    Versión correcta: borra en el orden adecuado y hace COMMIT final.
    """
    async with async_session() as session:
        trans = await session.begin()
        try:
            await session.execute(text(BORRADO_SQL["cliente_pelicula"]), {"pais": pais})
            await session.execute(text(BORRADO_SQL["valoraciones"]), {"pais": pais})
            await session.execute(text(BORRADO_SQL["transacciones"]), {"pais": pais})
            await session.execute(text(BORRADO_SQL["carrito_peliculas"]), {"pais": pais})
            await session.execute(text(BORRADO_SQL["carritos"]), {"pais": pais})
            await session.execute(text(BORRADO_SQL["clientes"]), {"pais": pais})

            await trans.commit()
            return jsonify({"status": "ok", "pais": pais})
        except Exception as e:
            await trans.rollback()
            abort(500, f"Error en borraPais: {e}")


@app.route("/borraPaisIncorrecto/<pais>", methods=["POST"])
async def borra_pais_incorrecto(pais: str):
    """
    Versión incorrecta: intenta borrar clientes primero, saltará error de FK
    y se hace ROLLBACK.
    """
    async with async_session() as session:
        trans = await session.begin()
        try:
            # MAL: primero clientes
            await session.execute(text(BORRADO_SQL["clientes"]), {"pais": pais})

            # Estas igual ni se ejecutan si ya salta el error antes
            await session.execute(text(BORRADO_SQL["transacciones"]), {"pais": pais})

            await trans.commit()
            return jsonify({"status": "ok", "pais": pais})
        except Exception as e:
            await trans.rollback()
            abort(500, f"Error en borraPaisIncorrecto (rollback aplicado): {e}")


@app.route("/borraPaisIntermedio/<pais>", methods=["POST"])
async def borra_pais_intermedio(pais: str):
    """
    Versión intermedia:
      - Borra primero valoraciones, transacciones y carritos y hace COMMIT parcial
      - Luego intenta borrar clientes mal y provoca error
      - Tras el ROLLBACK los cambios anteriores se conservan
    """
    async with async_session() as session:
        # Primer bloque: commit parcial
        trans1 = await session.begin()
        try:
            await session.execute(text(BORRADO_SQL["valoraciones"]), {"pais": pais})
            await session.execute(text(BORRADO_SQL["transacciones"]), {"pais": pais})
            await session.execute(text(BORRADO_SQL["carrito_peliculas"]), {"pais": pais})
            await session.execute(text(BORRADO_SQL["carritos"]), {"pais": pais})
            await trans1.commit()
        except Exception as e:
            await trans1.rollback()
            abort(500, f"Error en la fase intermedia (1): {e}")

        # Segundo bloque: borrado mal hecho
        trans2 = await session.begin()
        try:
            # MAL: intentar borrar clientes sin limpiar cliente_pelicula
            await session.execute(text(BORRADO_SQL["clientes"]), {"pais": pais})
            await trans2.commit()
            msg = "No hubo error (revisa restricciones FK)"
        except Exception as e:
            await trans2.rollback()
            msg = f"Error en fase intermedia (2), rollback parcial: {e}"

        return jsonify({"status": "intermedio", "pais": pais, "detalle": msg})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5051, debug=True)
