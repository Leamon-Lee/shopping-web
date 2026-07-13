from __future__ import annotations

import hashlib


def generate_product_hash(name: str, category_name: str) -> str:
    """Generate a unique SHA-256 hash for product-image mapping."""
    import uuid
    payload = f"{name.strip().lower()}::{category_name.strip().lower()}::{uuid.uuid4().hex}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()