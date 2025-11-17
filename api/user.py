from quart import Quart, request, jsonify, abort
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from db.db import async_session, Base
from db.models import Cliente
import hashlib

app = Quart(__name__)


# ==========================
# Funciones auxiliares
# ==========================

async def get_user_by_name(session: AsyncSession, name: str):
    result = await session.execute(select(Cliente).filter(Cliente.nombre == name))
    return result.scalars().first()

async def get_user_by_id(session: AsyncSession, uid: int):
    result = await session.execute(select(Cliente).filter(Cliente.id == uid))
    return result.scalars().first()

async def save_user(session: AsyncSession, name, email, password_hash):
    new_user = Cliente(nombre=name, email=email, saldo=0.0, password_hash=password_hash)
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    return new_user


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


# ==========================
# Rutas
# ==========================

@app.route("/user", methods=["PUT"])
async def register_user():
    data = await request.get_json()
    name = data.get("name")
    email = data.get("email", f"{name}@example.com")
    password = data.get("password")

    if not name or not password:
        print("Datos incompletos para registrar el usuario.")
        return abort(400)

    async with async_session() as session:
        user = await get_user_by_name(session, name)
        if user:
            print(f"El usuario {name} ya existe.")
            return abort(409, "User already exists")

        hashed_password = hash_password(password)
        new_user = await save_user(session, name, email, hashed_password)
        return jsonify({
            "uid": new_user.id,
            "username": new_user.nombre,
        })


@app.route("/user", methods=["POST"])
async def login_user():
    data = await request.get_json()
    name = data.get("name")
    password = data.get("password")

    if not name or not password:
        return abort(400)

    async with async_session() as session:
        user = await get_user_by_name(session, name)
        if not user:
            return abort(404)

        if user.password_hash != hash_password(password):
            return abort(403)

        token = hashlib.sha256(f"{user.nombre}{user.id}".encode()).hexdigest()

        return jsonify({
            "uid": user.id,
            "name": user.nombre,
            "email": user.email,
            "token": token,
        })


@app.route("/user/<int:uid>", methods=["DELETE"])
async def delete_user(uid: int):
    async with async_session() as session:
        user = await get_user_by_id(session, uid)
        if not user:
            return abort(404)

        await session.delete(user)
        await session.commit()
        return jsonify({"deleted": uid})


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5050, debug=True)
