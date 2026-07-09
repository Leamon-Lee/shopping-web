import os
from dataclasses import dataclass

@dataclass
class Settings:
    # PostgreSQL
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://shopping_user:shopping_password@localhost:5432/shopping",
    )

    # MinIO
    minio_endpoint: str = os.getenv("MINIO_ENDPOINT", "localhost:9000")
    minio_access_key: str = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    minio_secret_key: str = os.getenv("MINIO_SECRET_KEY", "minioadmin123")
    minio_secure: bool = os.getenv("MINIO_SECURE", "false").lower() == "true"
    minio_bucket_products: str = os.getenv("MINIO_BUCKET_PRODUCTS", "shopping-products")
    minio_bucket_data: str = os.getenv("MINIO_BUCKET_DATA", "shopping-data")

settings = Settings()