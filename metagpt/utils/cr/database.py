from __future__ import annotations

import asyncio
from typing import Any

from sqlalchemy import (
    Column,
    CursorResult,
    DateTime,
    Insert,
    Integer,
    Select,
    String,
    Update,
    exists,
    func,
    insert,
    select,
)
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import DeclarativeBase

database_url = "sqlite+aiosqlite:///./codereview.db"
engine = create_async_engine(database_url, echo=True)


class Base(DeclarativeBase):
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now())


class PointTable(Base):
    __tablename__ = "point"

    id = Column(Integer, primary_key=True)
    text = Column(String, nullable=False)
    file_path = Column(String, nullable=True)
    start_line = Column(Integer, nullable=True)
    end_line = Column(Integer, nullable=True)
    detail = Column(String, nullable=True)


async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def fetch_one(select_query: Select | Insert | Update) -> dict[str, Any] | None:
    async with engine.begin() as conn:
        cursor: CursorResult = await conn.execute(select_query)
        return cursor.first()._asdict() if cursor.rowcount > 0 else None


async def fetch_all(select_query: Select | Insert | Update) -> list[dict[str, Any]]:
    async with engine.begin() as conn:
        cursor: CursorResult = await conn.execute(select_query)
        return [r._asdict() for r in cursor.all()]


async def execute(select_query: Insert | Update) -> None:
    async with engine.begin() as conn:
        await conn.execute(select_query)


class PointDAO:
    """Operate Point table."""

    async def query(self, filters: dict = None, fields: list[str] = None) -> list[dict]:
        select_query = self._select_fields(PointTable, fields)

        if filters:
            for key, value in filters.items():
                select_query = select_query.filter(getattr(PointTable, key) == value)

        return await fetch_all(select_query)

    async def query_by_ids(self, ids: list[int], fields: list[str] = None) -> list[dict]:
        select_query = self._select_fields(PointTable, fields).where(PointTable.id.in_(ids))

        return await fetch_all(select_query)

    async def create(self, points: list[dict]):
        insert_query = insert(PointTable).values(points)

        return await execute(insert_query)

    async def exists(self, filters: dict) -> bool:
        exists_query = select(exists().where(*[getattr(PointTable, key) == value for key, value in filters.items()]))

        result = await fetch_one(exists_query)

        return result is not None

    def _select_fields(self, table: Base, fields: list[str] = None) -> Select:
        """Support select some fields."""

        if fields:
            return select(*[getattr(table, field) for field in fields])

        return select(table)


if __name__ == "__main__":

    async def main():
        await create_tables()

    asyncio.run(main())
