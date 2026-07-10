import os
from dataclasses import dataclass, field

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
    public_minio_base_url: str = os.getenv("PUBLIC_MINIO_BASE_URL", "http://localhost:9000")

    # JWT
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-in-production")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    jwt_expire_minutes: int = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))  # 24 hours

settings = Settings()
