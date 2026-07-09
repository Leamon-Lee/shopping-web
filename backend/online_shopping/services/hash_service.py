from __future__ import annotations

import hashlib


def generate_product_hash(name: str, category_name: str) -> str:
    """
    基于商品名 + 分类名生成 SHA-256 哈希，作为商品与 MinIO 图片的一一对应标识。

    相同的名称和分类始终产生相同的哈希值，天然去重。
    """
    payload = f"{name.strip().lower()}::{category_name.strip().lower()}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()