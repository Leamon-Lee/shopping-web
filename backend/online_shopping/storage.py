from minio import Minio

from online_shopping.config import settings

_minio_client: Minio | None = None


def get_minio_client() -> Minio:
    global _minio_client
    if _minio_client is None:
        _minio_client = Minio(
            endpoint=settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
        )
    return _minio_client


def build_image_path(product_hash: str, file_name: str) -> str:
    return f"products/{product_hash}/{file_name}"


def upload_product_image(product_hash: str, file_name: str, data: bytes, content_type: str = "image/jpeg") -> str:
    client = get_minio_client()
    object_path = build_image_path(product_hash, file_name)
    client.put_object(
        bucket_name=settings.minio_bucket_products,
        object_name=object_path,
        data=data,
        length=len(data),
        content_type=content_type,
    )
    return object_path


def get_image_url(product_hash: str, file_name: str) -> str:
    base_url = settings.public_minio_base_url.rstrip("/")
    return f"{base_url}/{settings.minio_bucket_products}/{build_image_path(product_hash, file_name)}"
