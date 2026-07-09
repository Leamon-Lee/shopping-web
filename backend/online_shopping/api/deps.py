from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from minio import Minio
from online_shopping.database import async_session
from online_shopping.storage import get_minio_client

async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session

def get_minio() -> Minio:
    return get_minio_client()