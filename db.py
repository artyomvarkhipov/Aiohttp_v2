import datetime
import os

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, MappedColumn, mapped_column

DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5431")
DB_USER = os.getenv("POSTGRES_USER", "app")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "secret")
DB_NAME = os.getenv("POSTGRES_DB", "app")

DB_DSN = (
    f"postgresql+asyncpg://"
    f"{DB_USER}:{DB_PASSWORD}@"
    f"{DB_HOST}:{DB_PORT}/"
    f"{DB_NAME}"
)


engine = create_async_engine(DB_DSN)
Session = async_sessionmaker(bind=engine, expire_on_commit=False)


class Base(DeclarativeBase, AsyncAttrs):
    id: MappedColumn[int] = mapped_column(Integer, primary_key=True)

    @property
    def id_dict(self):
        return {"id": self.id}


class User(Base):
    __tablename__ = "users"

    name: MappedColumn[str] = mapped_column(String, unique=True)
    password: MappedColumn[str] = mapped_column(String)
    registration_time: MappedColumn[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    @property
    def dict(self):
        return {
            "name": self.name,
            "registration_time": self.registration_time.isoformat(),
        }


class Ad(Base):
    __tablename__ = "ads"

    title: MappedColumn[str] = mapped_column(String, nullable=False)
    description: MappedColumn[str] = mapped_column(String, nullable=False)
    owner: MappedColumn[str] = mapped_column(String, nullable=False)
    created_at: MappedColumn[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    @property
    def dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "owner": self.owner,
            "created_at": self.created_at.isoformat(),
        }


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    await engine.dispose()
