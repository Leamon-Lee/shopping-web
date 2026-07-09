"""
Post-processor: Add product variants and try to get images for fallback products.
"""
import csv
import hashlib
import os
import random
import re
import uuid
from pathlib import Path

DATASET_DIR = Path(__file__).parent

def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text[:200]

def make_uuid(seed: str) -> str:
    return str(uuid.UUID(hashlib.sha256(seed.encode()).hexdigest()[:32]))

def add_variants():
    """Add product variants to all brand CSVs."""
    print("Adding product variants...")

    # Size templates by category keywords
    shoe_sizes = ["US 7", "US 7.5", "US 8", "US 8.5", "US 9", "US 9.5",
                  "US 10", "US 10.5", "US 11", "US 11.5", "US 12", "US 13"]
    clothing_sizes = ["XS", "S", "M", "L", "XL", "XXL"]
    clothing_sizes_women = ["XS", "S", "M", "L", "XL"]
    kids_sizes = ["2-3Y", "3-4Y", "4-5Y", "5-6Y", "6-7Y"]
    baby_sizes = ["0-3M", "3-6M", "6-9M", "9-12M", "12-18M", "18-24M"]
    color_variants = ["Black", "White", "Navy", "Gray", "Red"]
    electronic_colors = ["Midnight Black", "Starlight White", "Forest Green", "Ocean Blue"]
    storage_configs = ["128GB", "256GB", "512GB", "1TB"]
    ram_configs = ["8GB", "12GB", "16GB", "32GB"]

    all_variants = []

    for csv_file in sorted(DATASET_DIR.glob("*_products.csv")):
        brand = csv_file.stem.replace("_products", "")
        variants_file = DATASET_DIR / f"{brand}_product_variants.csv"

        if variants_file.exists():
            print(f"  {brand}: variants already exist, skipping")
            continue

        with open(csv_file, encoding="utf-8") as f:
            products = list(csv.DictReader(f))

        if not products:
            continue

        brand_variants = []
        for prod in products:
            cat_id = prod.get("category_id", "")
            name = prod["name"]
            price = float(prod["price"])
            pid = prod["id"]
            base_name = slugify(brand)

            # Determine variant type - electronics first (more specific), then clothing
            name_lower = name.lower()

            def has_word(text, word):
                import re
                return bool(re.search(r'\b' + re.escape(word) + r'\b', text))

            # Laptops / Tablets (before clothing since "laptop" contains "top")
            if any(kw in name_lower for kw in ["laptop", "tablet", "chromebook",
                                                 "thinkpad", "workstation", "ultrabook"]) or \
               has_word(name_lower, "pad"):
                for ram in ram_configs[:random.randint(2, 3)]:
                    for storage in storage_configs[:random.randint(2, 3)]:
                        var_name = f"{name} - {ram} RAM {storage}"
                        sku = f"{base_name}-{slugify(name)}-{ram.lower().replace(' ', '-')}-{storage.lower()}"
                        brand_variants.append({
                            "id": make_uuid(f"variant:{pid}:{ram}:{storage}"),
                            "product_id": pid,
                            "variant_id_str": f"var-{make_uuid(f'variant:{pid}:{ram}:{storage}')[:8]}",
                            "name": var_name,
                            "sku": sku[:64],
                            "price": round(price + {"8GB": 0, "12GB": 300, "16GB": 500, "32GB": 800}.get(ram, 0) +
                                           {"128GB": 0, "256GB": 200, "512GB": 500, "1TB": 1000}.get(storage, 0), 2),
                            "currency_code": "cny" if brand in ["xiaomi", "haier", "muji"] else "usd",
                            "inventory_count": random.randint(5, 100),
                            "manages_inventory": True,
                            "allows_backorder": False,
                        })

            # Smartphones (before clothing since "pro", "note" etc)
            elif any(kw in name_lower for kw in ["phone", "smartphone"]) or any(
                has_word(name_lower, kw) for kw in ["pro", "ultra", "redmi", "mix", "civi", "poco"]):
                for color in electronic_colors[:random.randint(2, 4)]:
                    for storage in storage_configs[:random.randint(2, 3)]:
                        var_name = f"{name} - {color} {storage}"
                        sku = f"{base_name}-{slugify(name)}-{color.lower().replace(' ', '-')}-{storage.lower()}"
                        brand_variants.append({
                            "id": make_uuid(f"variant:{pid}:{color}:{storage}"),
                            "product_id": pid,
                            "variant_id_str": f"var-{make_uuid(f'variant:{pid}:{color}:{storage}')[:8]}",
                            "name": var_name,
                            "sku": sku[:64],
                            "price": round(price + {"128GB": 0, "256GB": 200, "512GB": 600, "1TB": 1200}[storage], 2),
                            "currency_code": "cny",
                            "inventory_count": random.randint(20, 500),
                            "manages_inventory": True,
                            "allows_backorder": False,
                        })

            # Monitors / TV (before clothing)
            elif any(kw in name_lower for kw in ["monitor", "display", "television", " tv ", "tv", " oled", " qled"]):
                sku = f"{base_name}-{slugify(name)}"
                brand_variants.append({
                    "id": make_uuid(f"variant:{pid}:standard"),
                    "product_id": pid,
                    "variant_id_str": f"var-{make_uuid(f'variant:{pid}:standard')[:8]}",
                    "name": name,
                    "sku": sku[:64],
                    "price": price,
                    "currency_code": "cny",
                    "inventory_count": random.randint(5, 100),
                    "manages_inventory": True,
                    "allows_backorder": False,
                })

            # Shoes
            elif any(kw in name_lower for kw in ["shoe", "shoes", "sneaker", "sneakers", "air max", "air force",
                                                  "air jordan", "jordan", "dunk", "running", "trainer"]):
                for i, size in enumerate(shoe_sizes[:random.randint(6, 12)]):
                    sku = f"{base_name}-{slugify(name)}-{size.lower().replace(' ', '-')}"
                    brand_variants.append({
                        "id": make_uuid(f"variant:{pid}:{size}"),
                        "product_id": pid,
                        "variant_id_str": f"var-{make_uuid(f'variant:{pid}:{size}')[:8]}",
                        "name": f"{name} - {size}",
                        "sku": sku[:64],
                        "price": price + random.choice([0, 0, 0, 5.00, 10.00]),
                        "currency_code": "usd" if brand in ["nike", "uniqlo"] else "cny",
                        "inventory_count": random.randint(5, 150),
                        "manages_inventory": True,
                        "allows_backorder": False,
                    })

            # Clothing / Apparel
            elif any(kw in name_lower for kw in ["t-shirt", "shirt", "hoodie", "jacket", "coat", "sweater",
                                                   "cardigan", "jersey", "blouse", "dress", "leggings", "pants",
                                                   "shorts", "tank", "camisole", "bra", "skirt"]) or \
                 has_word(name_lower, "top"):
                sizes = clothing_sizes_women if any(kw in name_lower for kw in ["women", "bra", "dress", "camisole"]) else clothing_sizes
                for i, size in enumerate(sizes[:random.randint(4, 6)]):
                    sku = f"{base_name}-{slugify(name)}-{size.lower()}"
                    brand_variants.append({
                        "id": make_uuid(f"variant:{pid}:{size}"),
                        "product_id": pid,
                        "variant_id_str": f"var-{make_uuid(f'variant:{pid}:{size}')[:8]}",
                        "name": f"{name} - {size}",
                        "sku": sku[:64],
                        "price": round(price + random.choice([0, 0, 0, 0, 2.00]), 2),
                        "currency_code": "usd" if brand in ["nike", "uniqlo"] else "cny",
                        "inventory_count": random.randint(10, 200),
                        "manages_inventory": True,
                        "allows_backorder": False,
                    })

            # Kids/Baby
            elif any(kw in name_lower for kw in ["kids", "baby", "bodysuit", "infant"]):
                sizes = baby_sizes if "baby" in name_lower or "bodysuit" in name_lower else kids_sizes
                for i, size in enumerate(sizes[:random.randint(3, 5)]):
                    sku = f"{base_name}-{slugify(name)}-{size.lower()}"
                    brand_variants.append({
                        "id": make_uuid(f"variant:{pid}:{size}"),
                        "product_id": pid,
                        "variant_id_str": f"var-{make_uuid(f'variant:{pid}:{size}')[:8]}",
                        "name": f"{name} - {size}",
                        "sku": sku[:64],
                        "price": price,
                        "currency_code": "usd" if brand in ["nike", "uniqlo"] else "cny",
                        "inventory_count": random.randint(10, 150),
                        "manages_inventory": True,
                        "allows_backorder": False,
                    })

            # Appliances, Furniture, Audio, etc. - single variant
            elif any(kw in name_lower for kw in ["refrigerator", "washer", "freezer", "ac", "air condition",
                                                   "heater", "oven", "dishwasher", "cooktop", "hood",
                                                   "microwave", "vacuum", "fryer", "kettle", "blender",
                                                   "cooker", "dehumidifier", "humidifier", "table", "chair",
                                                   "stool", "shelf", "sofa", "bed", "desk", "furniture",
                                                   "purifier", "camera", "door lock", "bulb", "speaker",
                                                   "diffuser", "ruler", "pen", "highlighter",
                                                   "bag", "backpack", "duffel", "socks", "headband", "glove",
                                                   "belt", "charger", "cable", "power bank", "adapter", "dock",
                                                   "webcam", "headset", "stylus"]):
                sku = f"{base_name}-{slugify(name)}"
                brand_variants.append({
                    "id": make_uuid(f"variant:{pid}:default"),
                    "product_id": pid,
                    "variant_id_str": f"var-{make_uuid(f'variant:{pid}:default')[:8]}",
                    "name": name,
                    "sku": sku[:64],
                    "price": price,
                    "currency_code": "cny" if brand in ["xiaomi", "haier", "muji"] else "usd",
                    "inventory_count": random.randint(10, 300),
                    "manages_inventory": True,
                    "allows_backorder": False,
                })

            # Everything else (stationery, food, accessories) - single variant
            else:
                sku = f"{base_name}-{slugify(name)}"
                brand_variants.append({
                    "id": make_uuid(f"variant:{pid}:default"),
                    "product_id": pid,
                    "variant_id_str": f"var-{make_uuid(f'variant:{pid}:default')[:8]}",
                    "name": name,
                    "sku": sku[:64],
                    "price": price,
                    "currency_code": "usd" if brand in ["nike", "uniqlo", "dell"] else "cny",
                    "inventory_count": random.randint(10, 300),
                    "manages_inventory": True,
                    "allows_backorder": False,
                })

        # Save variants CSV
        if brand_variants:
            with open(variants_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=brand_variants[0].keys())
                writer.writeheader()
                writer.writerows(brand_variants)
            print(f"  {brand}: added {len(brand_variants)} variants to {variants_file.name}")
            all_variants.extend(brand_variants)

    print(f"\nTotal variants added: {len(all_variants)}")
    return True


def generate_placeholder_images():
    """Generate simple placeholder SVG images for products without images.
    These are rendered as PNG by converting the SVG."""
    print("\nGenerating placeholder images...")
    imgs_dir = DATASET_DIR / "imgs"

    # Brands with their primary colors
    brand_colors = {
        "muji": ("#7B3F3F", "#F5F5F0"),
        "uniqlo": ("#E8344A", "#FFFFFF"),
        "dell": ("#007DB8", "#FFFFFF"),
        "xiaomi": ("#FF6900", "#FFFFFF"),
        "haier": ("#003D8C", "#FFFFFF"),
    }

    # We'll generate simple SVG placeholders
    total_generated = 0
    for csv_file in sorted(DATASET_DIR.glob("*_product_images.csv")):
        brand = csv_file.stem.replace("_product_images", "")
        if brand == "nike":
            continue  # Nike already has real images

        with open(csv_file, encoding="utf-8") as f:
            images = list(csv.DictReader(f))

        for img in images:
            local_name = slugify(brand) + "-" + slugify(img["product_id"][:8]) + "-" + img["rank"]
            img_path = imgs_dir / f"{local_name}.svg"

            if not img_path.exists():
                primary, bg = brand_colors.get(brand, ("#666666", "#F0F0F0"))
                svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="400" height="400" viewBox="0 0 400 400">
  <rect width="400" height="400" fill="{bg}"/>
  <rect x="80" y="100" width="240" height="200" rx="12" fill="{primary}" opacity="0.15"/>
  <text x="200" y="210" text-anchor="middle" font-family="Arial,sans-serif"
        font-size="24" fill="{primary}" font-weight="bold">{brand.upper()}</text>
  <text x="200" y="245" text-anchor="middle" font-family="Arial,sans-serif"
        font-size="14" fill="#999">Product Image</text>
</svg>'''
                img_path.write_text(svg, encoding="utf-8")
                total_generated += 1

    print(f"  Generated {total_generated} placeholder SVGs")

    # Also update image CSV to point to local files
    for csv_file in sorted(DATASET_DIR.glob("*_product_images.csv")):
        brand = csv_file.stem.replace("_product_images", "")
        with open(csv_file, encoding="utf-8") as f:
            images = list(csv.DictReader(f))

        updated = False
        for img in images:
            if not img.get("image_url") or img["image_url"].strip() == "":
                local_name = slugify(brand) + "-" + slugify(img["product_id"][:8]) + "-" + img["rank"] + ".svg"
                img["image_url"] = f"imgs/{local_name}"
                updated = True

        if updated:
            with open(csv_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=images[0].keys())
                writer.writeheader()
                writer.writerows(images)
            print(f"  Updated image URLs in {csv_file.name}")


if __name__ == "__main__":
    add_variants()
    generate_placeholder_images()
    print("\nDone.")
