"""
Import scraped product data from CSV files into PostgreSQL and MinIO.

Reads CSV files from docker/postgres/dataset/ and:
- Clears existing product data from DB
- Inserts categories, products, images, and variants
- Uploads local product images to MinIO
"""
import asyncio
import csv
import io
import mimetypes
import os
import sys
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from sqlalchemy import text
from online_shopping.config import settings
from online_shopping.database import async_session
from online_shopping.storage import build_image_path, get_minio_client

DATASET_DIR = Path(__file__).parent / "docker" / "postgres" / "dataset"
IMAGES_DIR = DATASET_DIR / "imgs"
SEED_MANAGER_PREFIX = "seed_mgr_"
REMOTE_IMAGE_TIMEOUT_SECONDS = 20


BRAND_LABELS = {
    "dell": "Dell",
    "haier": "Haier",
    "muji": "Muji",
    "nike": "Nike",
    "skechers": "Skechers",
    "underarmour": "Under Armour",
    "uniqlo": "Uniqlo",
    "xiaomi": "Xiaomi",
}


def brand_label(brand: str) -> str:
    return BRAND_LABELS.get(brand, brand.replace("_", " ").title())


def seed_uuid(kind: str, brand: str) -> uuid.UUID:
    return uuid.uuid5(uuid.NAMESPACE_DNS, f"shopping-web-seed-{kind}-{brand}")


def image_extension_from_url(url: str, content_type: str | None = None) -> str:
    parsed_path = urllib.parse.urlparse(url).path
    suffix = Path(parsed_path).suffix.lower()
    if suffix in {".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg"}:
        return suffix
    guessed = mimetypes.guess_extension((content_type or "").split(";")[0].strip())
    if guessed in {".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg"}:
        return guessed
    return ".jpg"


def public_minio_url(object_name: str) -> str:
    return (
        f"{settings.public_minio_base_url.rstrip('/')}/"
        f"{settings.minio_bucket_products}/{object_name}"
    )


def upload_bytes_to_minio(product_hash: str, file_name: str, data: bytes, content_type: str) -> str:
    object_name = build_image_path(product_hash, file_name)
    get_minio_client().put_object(
        bucket_name=settings.minio_bucket_products,
        object_name=object_name,
        data=io.BytesIO(data),
        length=len(data),
        content_type=content_type,
    )
    return public_minio_url(object_name)


def mirror_remote_image_to_minio(row: dict, product_hash: str) -> str:
    source_url = row["image_url"]
    request = urllib.request.Request(
        source_url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/126.0 Safari/537.36"
            )
        },
    )
    with urllib.request.urlopen(request, timeout=REMOTE_IMAGE_TIMEOUT_SECONDS) as response:
        data = response.read()
        content_type = response.headers.get("Content-Type", "image/jpeg").split(";")[0]

    suffix = image_extension_from_url(source_url, content_type)
    file_name = f"{row['id']}{suffix}"
    return upload_bytes_to_minio(product_hash, file_name, data, content_type or "image/jpeg")


def upload_local_image_to_minio(row: dict, product_hash: str) -> str:
    image_url = row["image_url"]
    if image_url.startswith("imgs/"):
        image_path = IMAGES_DIR / os.path.basename(image_url)
    else:
        image_path = Path(image_url)

    data = image_path.read_bytes()
    suffix = image_path.suffix.lower()
    content_type = (
        "image/svg+xml" if suffix == ".svg"
        else "image/jpeg" if suffix in {".jpg", ".jpeg"}
        else "image/png" if suffix == ".png"
        else "application/octet-stream"
    )
    return upload_bytes_to_minio(product_hash, image_path.name, data, content_type)


def materialize_image_url(row: dict, product_hash: str) -> str:
    image_url = row.get("image_url", "")
    if not image_url:
        raise ValueError("image_url is empty")
    if image_url.startswith(("http://", "https://")):
        return mirror_remote_image_to_minio(row, product_hash)
    return upload_local_image_to_minio(row, product_hash)


async def clear_existing():
    async with async_session() as db:
        await db.execute(text("DELETE FROM shop_products"))
        await db.execute(text("DELETE FROM product_approvals"))
        await db.execute(
            text(
                "DELETE FROM shops WHERE manager_id IN ("
                "SELECT m.id FROM managers m "
                "JOIN accounts a ON a.id = m.account_id "
                "WHERE a.user_name LIKE :seed_prefix"
                ")"
            ),
            {"seed_prefix": f"{SEED_MANAGER_PREFIX}%"},
        )
        await db.execute(
            text(
                "DELETE FROM managers WHERE account_id IN ("
                "SELECT id FROM accounts WHERE user_name LIKE :seed_prefix"
                ")"
            ),
            {"seed_prefix": f"{SEED_MANAGER_PREFIX}%"},
        )
        await db.execute(
            text("DELETE FROM accounts WHERE user_name LIKE :seed_prefix"),
            {"seed_prefix": f"{SEED_MANAGER_PREFIX}%"},
        )
        for table in [
            "cart_items",
            "category_products",
            "catalog_products",
            "product_reviews",
            "product_images",
            "product_variants",
            "products",
            "product_categories",
        ]:
            await db.execute(text(f"DELETE FROM {table}"))
        await db.commit()
        print("Cleared existing product data.")


async def import_all():
    brands = sorted({
        path.name.removesuffix("_products.csv")
        for path in DATASET_DIR.glob("*_products.csv")
    })

    # ---- Load all CSV data ----
    # Categories with dedup by normalized name
    cat_by_name: dict[str, dict] = {}
    cat_id_map: dict[str, str] = {}  # original cat_id -> deduped cat_id

    all_products: list[dict] = []
    all_images: list[dict] = []
    all_variants: list[dict] = []
    product_hash_map: dict[str, str] = {}  # product_id -> product_hash

    for brand in brands:
        cat_file = DATASET_DIR / f"{brand}_product_categories.csv"
        if cat_file.exists():
            with open(cat_file, encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    name = row["name"]
                    oid = row["id"]
                    if name not in cat_by_name:
                        cat_by_name[name] = row
                        cat_id_map[oid] = oid
                    else:
                        cat_id_map[oid] = cat_by_name[name]["id"]

        prod_file = DATASET_DIR / f"{brand}_products.csv"
        if prod_file.exists():
            with open(prod_file, encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    row["_brand"] = brand
                    # Remap category_id through dedup
                    raw_cid = row.get("category_id", "")
                    if raw_cid and raw_cid in cat_id_map:
                        row["category_id"] = cat_id_map[raw_cid]
                    elif raw_cid:
                        fallback_name = f"{brand.title()} Catalog {raw_cid[:8]}"
                        if fallback_name not in cat_by_name:
                            cat_by_name[fallback_name] = {
                                "id": raw_cid,
                                "name": fallback_name,
                                "description": f"Imported {brand.title()} products.",
                            }
                        cat_id_map[raw_cid] = raw_cid
                    all_products.append(row)
                    product_hash_map[row["id"]] = row["product_hash"]

        img_file = DATASET_DIR / f"{brand}_product_images.csv"
        if img_file.exists():
            with open(img_file, encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    row["_brand"] = brand
                    all_images.append(row)

        var_file = DATASET_DIR / f"{brand}_product_variants.csv"
        if var_file.exists():
            with open(var_file, encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    all_variants.append(row)

    print(f"CSV loaded: {len(cat_by_name)} categories, {len(all_products)} products, "
          f"{len(all_images)} images, {len(all_variants)} variants")

    # ---- Clear & Insert ----
    await clear_existing()

    successful_product_ids: set[str] = set()

    async with async_session() as db:
        # Step 1: Insert categories
        for name, row in cat_by_name.items():
            await db.execute(
                text("INSERT INTO product_categories (id, name, description) "
                     "VALUES (:id, :name, :desc)"),
                {"id": uuid.UUID(row["id"]), "name": row["name"],
                 "desc": row["description"]},
            )
        await db.commit()
        print(f"Inserted {len(cat_by_name)} categories.")

        # Step 2: Insert products
        prod_count, skip_count = 0, 0
        for row in all_products:
            try:
                cid = uuid.UUID(row["category_id"]) if row.get("category_id") else None
                await db.execute(
                    text(
                        "INSERT INTO products (id, product_hash, category_id, name, slug, "
                        "description, price, available_item_count, metadata_json) "
                        "VALUES (:id, :hash, :cid, :name, :slug, :desc, :price, :stock, :meta)"
                    ),
                    {"id": uuid.UUID(row["id"]), "hash": row["product_hash"],
                     "cid": cid, "name": row["name"], "slug": row["slug"],
                     "desc": row["description"], "price": float(row["price"]),
                     "stock": int(row["available_item_count"]),
                     "meta": row.get("metadata_json", "{}")},
                )
                await db.commit()  # commit each product to avoid transaction abort cascade
                successful_product_ids.add(row["id"])
                prod_count += 1
            except Exception as e:
                await db.rollback()
                skip_count += 1
        print(f"Inserted {prod_count} products (skipped {skip_count}).")

        # Step 3: Insert images
        img_count = 0
        imaged_product_ids: set[str] = set()
        for row in all_images:
            if row["product_id"] not in successful_product_ids:
                continue
            try:
                product_hash = product_hash_map.get(row["product_id"], row["product_id"])
                image_url = materialize_image_url(row, product_hash)
                await db.execute(
                    text("INSERT INTO product_images (id, product_id, image_url, rank) "
                         "VALUES (:id, :pid, :url, :rank)"),
                    {"id": uuid.UUID(row["id"]), "pid": uuid.UUID(row["product_id"]),
                     "url": image_url, "rank": int(row["rank"])},
                )
                await db.commit()
                imaged_product_ids.add(row["product_id"])
                img_count += 1
                if img_count % 50 == 0:
                    print(f"  MinIO+DB images: {img_count} linked...")
            except Exception as e:
                await db.rollback()
                print(f"  Image skipped for product {row.get('product_id')}: {e}")
        print(f"Inserted {img_count} images.")

        missing_image_ids = successful_product_ids - imaged_product_ids
        if missing_image_ids:
            for product_id in missing_image_ids:
                await db.execute(
                    text("DELETE FROM products WHERE id = :id"),
                    {"id": uuid.UUID(product_id)},
                )
            await db.commit()
            print(f"Removed {len(missing_image_ids)} products without MinIO-linked images.")
        successful_product_ids = imaged_product_ids

        # Step 4: Insert variants
        var_count = 0
        for row in all_variants:
            if row["product_id"] not in successful_product_ids:
                continue
            try:
                await db.execute(
                    text(
                        "INSERT INTO product_variants (id, product_id, variant_id_str, "
                        "name, sku, price, inventory_count) "
                        "VALUES (:id, :pid, :vid_str, :name, :sku, :price, :inv)"
                    ),
                    {"id": uuid.UUID(row["id"]), "pid": uuid.UUID(row["product_id"]),
                     "vid_str": row["variant_id_str"], "name": row["name"],
                     "sku": row["sku"], "price": float(row["price"]),
                     "inv": int(row["inventory_count"])},
                )
                await db.commit()
                var_count += 1
            except Exception as e:
                await db.rollback()
        print(f"Inserted {var_count} variants.")

        default_var_count = 0
        for row in all_products:
            if row["id"] not in successful_product_ids:
                continue
            result = await db.execute(
                text("SELECT 1 FROM product_variants WHERE product_id = :pid LIMIT 1"),
                {"pid": uuid.UUID(row["id"])},
            )
            if result.first():
                continue
            slug = row["slug"]
            await db.execute(
                text(
                    "INSERT INTO product_variants (id, product_id, variant_id_str, "
                    "name, sku, price, inventory_count) "
                    "VALUES (:id, :pid, :vid_str, :name, :sku, :price, :inv)"
                ),
                {
                    "id": uuid.uuid4(),
                    "pid": uuid.UUID(row["id"]),
                    "vid_str": f"variant_{slug}",
                    "name": "Default Variant",
                    "sku": f"SKU-{slug[:40].upper()}-{row['id'][:8]}",
                    "price": float(row["price"]),
                    "inv": int(row["available_item_count"]),
                },
            )
            default_var_count += 1
        await db.commit()
        print(f"Inserted {default_var_count} default variants.")

        # Step 5: Insert seed shops and connect imported products to their source shop.
        brand_products: dict[str, list[dict]] = {}
        for row in all_products:
            if row["id"] in successful_product_ids:
                brand_products.setdefault(row["_brand"], []).append(row)

        shop_count = 0
        shop_product_count = 0
        for brand, rows in sorted(brand_products.items()):
            account_id = seed_uuid("account", brand)
            manager_id = seed_uuid("manager", brand)
            shop_id = seed_uuid("shop", brand)
            manager_user_name = f"{SEED_MANAGER_PREFIX}{brand}"[:20]
            label = brand_label(brand)

            await db.execute(
                text(
                    "INSERT INTO accounts (id, user_name, password_hash, status, "
                    "first_name, last_name, email) "
                    "VALUES (:id, :user_name, :password_hash, 'active', :first_name, "
                    "'Manager', :email) "
                    "ON CONFLICT (user_name) DO UPDATE SET "
                    "email = EXCLUDED.email, status = 'active'"
                ),
                {
                    "id": account_id,
                    "user_name": manager_user_name,
                    "password_hash": "seeded-development-password",
                    "first_name": label,
                    "email": f"{manager_user_name}@shopping.local",
                },
            )
            await db.execute(
                text(
                    "INSERT INTO managers (id, account_id) VALUES (:id, :account_id) "
                    "ON CONFLICT (account_id) DO NOTHING"
                ),
                {"id": manager_id, "account_id": account_id},
            )
            await db.execute(
                text(
                    "INSERT INTO shops (id, manager_id, name, status, reviewed_at) "
                    "VALUES (:id, :manager_id, :name, 'active', now()) "
                    "ON CONFLICT (name) DO UPDATE SET status = 'active'"
                ),
                {"id": shop_id, "manager_id": manager_id, "name": label},
            )
            shop_count += 1

            for row in rows:
                await db.execute(
                    text(
                        "INSERT INTO shop_products (shop_id, product_id, added_by_manager_id) "
                        "VALUES (:shop_id, :product_id, :manager_id) "
                        "ON CONFLICT (shop_id, product_id) DO NOTHING"
                    ),
                    {
                        "shop_id": shop_id,
                        "product_id": uuid.UUID(row["id"]),
                        "manager_id": manager_id,
                    },
                )
                shop_product_count += 1
        await db.commit()
        print(f"Inserted {shop_count} shops and {shop_product_count} shop-product links.")

    print("\nImport complete!")


def main():
    asyncio.run(import_all())


if __name__ == "__main__":
    main()
