"""
Scraper V2: Replace fake/SVG-only products with real scraped data.

Sources:
1. Logitech (logitech.com) - JSON-LD on product detail pages
   Categories: Mice, Keyboards, Webcams, Headsets, Speakers
2. Under Armour (underarmour.com) - Constructor.io browse API
   Categories: Men's Shoes, Men's Clothing

Output: CSV files for import into PostgreSQL + images in imgs/
"""
import asyncio
import csv
import hashlib
import json
import os
import random
import re
import uuid
from pathlib import Path
from urllib.parse import urljoin, urlparse

import httpx
from playwright.async_api import async_playwright

DATASET_DIR = Path(__file__).parent
IMAGES_DIR = DATASET_DIR / "imgs"
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0.0.0 Safari/537.36"
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text[:200]

def make_uuid(seed: str) -> str:
    return str(uuid.UUID(hashlib.sha256(seed.encode()).hexdigest()[:32]))

def make_hash(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()

def now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


class DataCollector:
    def __init__(self, brand: str):
        self.brand = brand
        self.categories: list[dict] = []
        self.products: list[dict] = []
        self.images: list[dict] = []
        self.variants: list[dict] = []
        self.image_files: list[tuple[str, str]] = []

    def add_category(self, name: str, description: str = "") -> str:
        cat_id = make_uuid(f"category:{self.brand}:{name}")
        slug = slugify(f"{self.brand}-{name}")
        if not any(c["id"] == cat_id for c in self.categories):
            self.categories.append({
                "id": cat_id, "name": name, "slug": slug,
                "description": description or f"{name} from {self.brand}",
            })
        return cat_id

    def add_product(self, category_id: str, name: str, description: str,
                    price: float, image_urls: list[str],
                    metadata: dict = None, variants: list[dict] = None,
                    stock: int = 100) -> str:
        if any(p["name"] == name for p in self.products):
            return ""
        if len(name) < 4:
            return ""

        prod_id = make_uuid(f"product:{self.brand}:{name}")
        slug = slugify(f"{self.brand}-{name}")
        product_hash = make_hash(f"{self.brand}:{name}")

        self.products.append({
            "id": prod_id, "product_hash": product_hash,
            "category_id": category_id, "name": name, "slug": slug,
            "description": description, "price": price,
            "available_item_count": stock,
            "metadata_json": json.dumps(metadata or {}, ensure_ascii=False),
        })

        if not image_urls:
            image_urls = [""]
        has_real = any(u and u.strip() for u in image_urls)
        for rank, img_url in enumerate(image_urls):
            if not img_url or not img_url.strip():
                if has_real:
                    continue
                img_url = ""
            img_id = make_uuid(f"image:{prod_id}:{rank}")
            self.images.append({
                "id": img_id, "product_id": prod_id,
                "image_url": img_url, "rank": rank,
            })
            if img_url:
                ext = ".jpg"
                parsed = urlparse(img_url)
                if parsed.path.lower().endswith((".png", ".webp", ".gif")):
                    ext = os.path.splitext(parsed.path)[1].lower()
                local_name = f"{slugify(self.brand)}-{slugify(name)}-{rank}{ext}"
                self.image_files.append((img_url, local_name))

        if variants:
            for v in variants:
                self.add_variant(prod_id, v["name"], v.get("price", price),
                                 v.get("sku", ""), v.get("currency", "usd"))

        return prod_id

    def add_variant(self, product_id: str, name: str, price: float,
                    sku: str = "", currency: str = "usd"):
        var_id = make_uuid(f"variant:{product_id}:{name}")
        if not sku:
            sku = f"{slugify(self.brand)}-{slugify(name)}-{random.randint(1000, 9999)}"
        self.variants.append({
            "id": var_id, "product_id": product_id,
            "variant_id_str": f"var-{var_id[:8]}",
            "name": name[:160], "sku": sku[:64], "price": price,
            "currency_code": currency,
            "inventory_count": random.randint(10, 200),
            "manages_inventory": True, "allows_backorder": False,
        })

    def save_csvs(self):
        for name, data in [
            ("product_categories", self.categories),
            ("products", self.products),
            ("product_images", self.images),
            ("product_variants", self.variants),
        ]:
            if not data:
                continue
            path = DATASET_DIR / f"{self.brand}_{name}.csv"
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
            print(f"  Saved {len(data)} rows to {path.name}")


# ======================================================================
# Logitech scraper (JSON-LD on product detail pages)
# ======================================================================

LOGITECH_CATEGORY_PAGES = {
    "Mice": "https://www.logitech.com/en-us/shop/c/mice",
    "Keyboards": "https://www.logitech.com/en-us/shop/c/keyboards",
    "Webcams": "https://www.logitech.com/en-us/shop/c/webcams",
    "Headsets": "https://www.logitech.com/en-us/shop/c/headsets",
    "Speakers": "https://www.logitech.com/en-us/shop/c/speakers",
}


async def scrape_logitech():
    print("\n[LOGITECH] Scraping logitech.com via JSON-LD ...")
    c = DataCollector("logitech")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        for cat_name, list_url in LOGITECH_CATEGORY_PAGES.items():
            if len(c.products) >= 45:
                break
            cat_id = c.add_category(cat_name)
            print(f"  Category: {cat_name}")

            try:
                page = await browser.new_page()
                await page.goto(list_url, timeout=30000, wait_until="domcontentloaded")
                await page.wait_for_timeout(5000)
                await page.evaluate("window.scrollBy(0, 3000)")
                await page.wait_for_timeout(2000)

                # Collect product detail page URLs from listing
                product_links = set()
                link_els = await page.query_selector_all("a[href]")
                for el in link_els:
                    href = await el.get_attribute("href")
                    if href and "/shop/p/" in href:
                        full = urljoin("https://www.logitech.com", href)
                        product_links.add(full)

                print(f"    Found {len(product_links)} product detail URLs")

                # Visit each detail page, extract JSON-LD
                for detail_url in list(product_links):
                    if len(c.products) >= 45:
                        break
                    try:
                        await page.goto(detail_url, timeout=20000, wait_until="domcontentloaded")
                        await page.wait_for_timeout(2000)

                        html = await page.content()
                        json_lds = re.findall(
                            r'<script type="application/ld\+json">(.*?)</script>',
                            html, re.DOTALL,
                        )

                        for j_text in json_lds:
                            if '"@type"' not in j_text or '"Product"' not in j_text:
                                continue
                            try:
                                data = json.loads(j_text)
                                if isinstance(data, list):
                                    data = data[0] if data else {}
                                dtype = data.get("@type", "")
                                if isinstance(dtype, list):
                                    dtype = dtype[0] if dtype else ""
                                if dtype != "Product":
                                    continue

                                name = data.get("name", "")
                                if not name or len(name) < 3:
                                    continue

                                # Price
                                offers = data.get("offers", {})
                                if isinstance(offers, list):
                                    offers = offers[0] if offers else {}
                                price = offers.get("price", offers.get("lowPrice", 0))
                                if not price:
                                    price = float(offers.get("highPrice", 0))
                                if not price:
                                    continue

                                # Description
                                desc = data.get("description", "")
                                if not desc:
                                    desc = f"{name} by Logitech."

                                # Images
                                images = data.get("image", [])
                                if isinstance(images, str):
                                    images = [images]

                                # Models (variants)
                                variants = []
                                models = data.get("model", [])
                                if isinstance(models, dict):
                                    models = [models]
                                for model in models:
                                    var_name = model.get("name", name)
                                    var_sku = model.get("sku", model.get("mpn", ""))
                                    variants.append({
                                        "name": var_name,
                                        "price": price,
                                        "sku": var_sku,
                                        "currency": "usd",
                                    })

                                print(f"      {name[:60]} | ${price} | {len(images)} imgs")

                                c.add_product(
                                    cat_id, name, desc, float(price),
                                    image_urls=images,
                                    metadata={
                                        "brand": "Logitech",
                                        "productID": data.get("productID", ""),
                                        "url": data.get("url", detail_url),
                                    },
                                    variants=variants,
                                    stock=random.randint(20, 300),
                                )
                                break  # Only process first valid Product schema
                            except (json.JSONDecodeError, KeyError, TypeError):
                                continue

                    except Exception as e:
                        continue

                await page.close()

            except Exception as e:
                print(f"    Error: {e}")

        await browser.close()

    c.save_csvs()
    return c


# ======================================================================
# Under Armour scraper (Constructor.io API)
# ======================================================================

# Under Armour uses Constructor.io with exposed API key
UA_API_KEY = "key_Gz4VzKsXbR7b7fSh"
UA_API_BASE = "https://ac.cnstrc.com"

UA_CATEGORIES = {
    "men-footwear": "Men's Footwear",
    "men-apparel": "Men's Apparel",
    "women-footwear": "Women's Footwear",
    "women-apparel": "Women's Apparel",
}


async def scrape_ua():
    print("\n[UNDER ARMOUR] Scraping via Constructor.io API ...")
    c = DataCollector("underarmour")

    async with httpx.AsyncClient(timeout=30, headers={"User-Agent": USER_AGENT}) as client:
        for group_id, cat_name in UA_CATEGORIES.items():
            if len(c.products) >= 45:
                break
            cat_id = c.add_category(cat_name)
            print(f"  Category: {cat_name} (group_id={group_id})")

            try:
                params = {
                    "c": "ciojs-client-2.65.0",
                    "key": UA_API_KEY,
                    "num_results_per_page": "30",
                    "page": "1",
                    "fmt_options[groups_max_depth]": "2",
                    "fmt_options[hidden_fields]": "test_cells",
                }
                url = f"{UA_API_BASE}/browse/group_id/{group_id}"
                resp = await client.get(url, params=params)

                if resp.status_code != 200:
                    print(f"    API returned {resp.status_code}")
                    continue

                data = resp.json()
                results = data.get("response", {}).get("results", [])
                total = data.get("response", {}).get("total_num_results", 0)
                print(f"    Found {len(results)} results (total: {total})")

                for item in results:
                    if len(c.products) >= 45:
                        break
                    try:
                        d = item.get("data", {})

                        # Product name from URL slug
                        url_path = d.get("url", "")
                        slug = url_path.strip("/").split("/")[1].replace(".html", "")
                        from urllib.parse import unquote
                        slug = unquote(slug)  # Decode %2B -> +
                        name = slug.replace("_", " ").replace("+", " ").title()
                        # Fix common issues
                        name = re.sub(r'\s+', ' ', name).strip()
                        if not name or len(name) < 5:
                            continue

                        # Price
                        price = d.get("salePriceLow") or d.get("listPriceLow") or 0
                        if not price:
                            continue

                        # Description
                        desc = d.get("description", "")
                        if not desc:
                            desc = f"{name} by Under Armour."
                        # Clean HTML tags if any
                        desc = re.sub(r"<[^>]+>", "", desc)
                        if len(desc) > 500:
                            desc = desc[:497] + "..."

                        # Sub-header as category hint
                        sub = d.get("subHeader", cat_name)

                        # Images
                        image_url = d.get("image_url", "")
                        images = [image_url] if image_url else []

                        # Variant colors
                        variants = []
                        color_value = d.get("colorValue", "")
                        if color_value:
                            variants.append({
                                "name": f"{name} - {color_value}",
                                "price": price,
                                "sku": d.get("sku", d.get("id", "")),
                                "currency": "usd",
                            })
                        # Also add variations
                        for var in d.get("variations", [])[:5]:
                            if isinstance(var, dict):
                                v_name = var.get("value", var.get("name", ""))
                                if v_name and v_name != color_value:
                                    variants.append({
                                        "name": f"{name} - {v_name}",
                                        "price": var.get("price", price),
                                        "sku": var.get("sku", var.get("id", "")),
                                        "currency": "usd",
                                    })

                        print(f"      {name[:60]} | ${price}")

                        c.add_product(
                            cat_id, name, desc, float(price),
                            image_urls=images,
                            metadata={
                                "brand": "Under Armour",
                                "subHeader": sub,
                                "url": urljoin("https://www.underarmour.com", url_path),
                            },
                            variants=variants if variants else None,
                            stock=random.randint(20, 400),
                        )
                    except Exception as e:
                        continue

            except Exception as e:
                print(f"    Error: {e}")

    c.save_csvs()
    return c


# ======================================================================
# Image downloader
# ======================================================================

async def download_all_images(collectors: list):
    print("\n[IMAGES] Downloading ...")
    async with httpx.AsyncClient(timeout=30, headers={"User-Agent": USER_AGENT}) as client:
        downloaded, failed = 0, 0
        for c in collectors:
            for url, local_name in c.image_files:
                filepath = IMAGES_DIR / local_name
                if filepath.exists():
                    continue
                try:
                    resp = await client.get(url, timeout=30)
                    if resp.status_code == 200 and len(resp.content) > 1024:
                        filepath.write_bytes(resp.content)
                        downloaded += 1
                    else:
                        failed += 1
                except Exception:
                    failed += 1
                if (downloaded + failed) % 20 == 0:
                    print(f"  Progress: {downloaded} ok, {failed} fail")
        print(f"  Done: {downloaded} downloaded, {failed} failed")


# ======================================================================
# Main
# ======================================================================

async def main():
    print("=" * 60)
    print("SCRAPER V2 - Logitech + Under Armour")
    print("=" * 60)

    collectors = []

    # Scrape Logitech
    try:
        c = await scrape_logitech()
        collectors.append(c)
    except Exception as e:
        print(f"Logitech FATAL: {e}")
        import traceback
        traceback.print_exc()

    # Scrape Under Armour
    try:
        c = await scrape_ua()
        collectors.append(c)
    except Exception as e:
        print(f"Under Armour FATAL: {e}")
        import traceback
        traceback.print_exc()

    # Download images
    try:
        await download_all_images(collectors)
    except Exception as e:
        print(f"Image download error: {e}")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for c in collectors:
        print(f"  {c.brand}: {len(c.products)} products, {len(c.categories)} categories, "
              f"{len(c.images)} images, {len(c.variants)} variants")


if __name__ == "__main__":
    asyncio.run(main())
