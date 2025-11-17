from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# Usamos la misma URL que en docker-compose (asyncpg)
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://alumnodb:1234@db:5432/si1"
)

engine = create_async_engine(
    DATABASE_URL,
    echo=False,      # pon True si quieres ver el SQL por consola
    future=True
)

Base = declarative_base()

async_session = sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession
)
