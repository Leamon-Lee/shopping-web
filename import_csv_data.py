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
import os
import sys
import uuid
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from sqlalchemy import text
from online_shopping.database import async_session
from online_shopping.storage import get_minio_client

DATASET_DIR = Path(__file__).parent / "docker" / "postgres" / "dataset"
IMAGES_DIR = DATASET_DIR / "imgs"


async def clear_existing():
    async with async_session() as db:
        await db.execute(text("DELETE FROM product_images"))
        await db.execute(text("DELETE FROM product_variants"))
        await db.execute(text("DELETE FROM products"))
        await db.execute(text("DELETE FROM product_categories"))
        await db.commit()
        print("Cleared existing product data.")


async def import_all():
    brands = ["nike", "skechers", "underarmour"]

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
        for row in all_images:
            if row["product_id"] not in successful_product_ids:
                continue
            try:
                await db.execute(
                    text("INSERT INTO product_images (id, product_id, image_url, rank) "
                         "VALUES (:id, :pid, :url, :rank)"),
                    {"id": uuid.UUID(row["id"]), "pid": uuid.UUID(row["product_id"]),
                     "url": row["image_url"], "rank": int(row["rank"])},
                )
                await db.commit()
                img_count += 1
            except Exception as e:
                await db.rollback()
        print(f"Inserted {img_count} images.")

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

    # Step 5: Upload local images to MinIO
    await upload_to_minio(all_images, successful_product_ids, product_hash_map)
    print("\nImport complete!")


async def upload_to_minio(all_images, successful_ids, hash_map):
    client = get_minio_client()
    bucket = "shopping-products"
    uploaded = 0

    for row in all_images:
        if row["product_id"] not in successful_ids:
            continue
        img_url = row.get("image_url", "")
        if not img_url:
            continue
        if img_url.startswith("http"):
            continue  # Skip remote CDN URLs (Nike)

        if img_url.startswith("imgs/"):
            img_path = IMAGES_DIR / os.path.basename(img_url)
        else:
            img_path = Path(img_url)

        if not img_path.exists():
            continue

        try:
            product_hash = hash_map.get(row["product_id"], row["product_id"])
            data = img_path.read_bytes()
            content_type = "image/svg+xml" if img_path.suffix == ".svg" else "image/png"
            object_name = f"products/{product_hash}/{img_path.name}"

            client.put_object(
                bucket_name=bucket,
                object_name=object_name,
                data=io.BytesIO(data),
                length=len(data),
                content_type=content_type,
            )
            uploaded += 1
            if uploaded % 50 == 0:
                print(f"  MinIO: uploaded {uploaded} images...")
        except Exception as e:
            print(f"  MinIO error for {img_path.name}: {e}")

    if uploaded > 0:
        print(f"MinIO: uploaded {uploaded} images to '{bucket}'.")
    else:
        print("MinIO: no local images to upload (Nike images are CDN-hosted).")


def main():
    asyncio.run(import_all())


if __name__ == "__main__":
    main()
