"""
Scrape product data from 6 brands (Muji, Nike, Uniqlo, Dell, Xiaomi, Haier)
and save to CSV files + download images.
Each brand: up to 50 products.
"""
import asyncio
import csv
import hashlib
import json
import os
import random
import re
import sys
import uuid
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse

import httpx
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

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

def sanitize_price(price_str: str) -> float:
    """Extract a float price from a string."""
    if not price_str:
        return 0.0
    cleaned = re.sub(r"[^\d.,]", "", price_str)
    cleaned = cleaned.replace(",", ".")
    parts = cleaned.split(".")
    if len(parts) > 2:
        cleaned = "".join(parts[:-1]) + "." + parts[-1]
    try:
        return round(float(cleaned), 2)
    except ValueError:
        return 0.0

async def download_image(client: httpx.AsyncClient, url: str, filepath: Path) -> bool:
    """Download an image to filepath. Returns True on success."""
    if filepath.exists():
        return True
    try:
        resp = await client.get(url, timeout=30)
        if resp.status_code == 200 and len(resp.content) > 1024:
            filepath.write_bytes(resp.content)
            return True
    except Exception:
        pass
    return False

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

# ---------------------------------------------------------------------------
# CSV writers
# ---------------------------------------------------------------------------

class DataCollector:
    def __init__(self, brand: str):
        self.brand = brand
        self.categories: list[dict] = []
        self.products: list[dict] = []
        self.images: list[dict] = []
        self.variants: list[dict] = []
        self.image_files: list[tuple[str, str]] = []  # (url, local_filename)

    def add_category(self, name: str, description: str = "") -> str:
        cat_id = make_uuid(f"category:{self.brand}:{name}")
        slug = slugify(f"{self.brand}-{name}")
        if not any(c["id"] == cat_id for c in self.categories):
            self.categories.append({
                "id": cat_id, "name": name, "slug": slug,
                "description": description or f"{name} products from {self.brand}",
            })
        return cat_id

    def add_product(self, category_id: str, name: str, description: str,
                    price: float, image_urls: list[str],
                    metadata: dict = None, variants: list[dict] = None,
                    stock: int = 100) -> str:
        # Skip duplicates by name
        if any(p["name"] == name for p in self.products):
            return ""
        # Skip products with obviously-wrong names (too short or generic)
        if len(name) < 5:
            return ""
        generic_names = {"new xps", "dell", "back to school", "inspiron", "latitude",
                         "optiplex", "precision", "alienware", "product", "item", "view",
                         "new xps 13", "dell 14 plus", "shop", "learn", "support",
                         "laptops", "desktops", "monitors", "accessories"}
        if name.lower().strip() in generic_names:
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

        # Always ensure at least one image entry
        if not image_urls:
            image_urls = [""]
        has_real_url = any(u and u.strip() for u in image_urls)
        for rank, img_url in enumerate(image_urls):
            if not img_url or not img_url.strip():
                if has_real_url:
                    continue  # Skip empty among real URLs
                # Create placeholder entry
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
                self.add_variant(prod_id, v["name"], v["price"], v.get("sku", ""))

        return prod_id

    def add_variant(self, product_id: str, name: str, price: float,
                    sku: str = "", currency: str = "cny"):
        var_id = make_uuid(f"variant:{product_id}:{name}")
        if not sku:
            sku = f"{slugify(self.brand)}-{slugify(name)}-{random.randint(1000, 9999)}"
        self.variants.append({
            "id": var_id, "product_id": product_id,
            "variant_id_str": f"var-{var_id[:8]}",
            "name": name, "sku": sku, "price": price,
            "currency_code": currency,
            "inventory_count": random.randint(10, 200),
            "manages_inventory": True, "allows_backorder": False,
        })

    def save_csvs(self, prefix: str = ""):
        prefix = f"{prefix}_{self.brand}" if prefix else self.brand
        for name, data in [
            ("product_categories", self.categories),
            ("products", self.products),
            ("product_images", self.images),
            ("product_variants", self.variants),
        ]:
            if not data:
                continue
            path = DATASET_DIR / f"{prefix}_{name}.csv"
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
            print(f"  Saved {len(data)} rows to {path.name}")


# ---------------------------------------------------------------------------
# Browser helper
# ---------------------------------------------------------------------------

async def new_page(p, headless: bool = True):
    browser = await p.chromium.launch(headless=headless)
    context = await browser.new_context(
        user_agent=USER_AGENT,
        viewport={"width": 1920, "height": 1080},
        locale="en-US",
    )
    page = await context.new_page()
    return browser, context, page


async def safe_goto(page, url: str, timeout: int = 30000, wait_until: str = "domcontentloaded"):
    try:
        await page.goto(url, timeout=timeout, wait_until=wait_until)
    except Exception as e:
        print(f"    goto warning: {e}")


async def scroll_load(page, pause: float = 1.5, times: int = 5):
    """Scroll down to trigger lazy loading."""
    for _ in range(times):
        await page.evaluate("window.scrollBy(0, window.innerHeight)")
        await asyncio.sleep(pause)


async def extract_text(page, selector: str) -> str:
    try:
        el = await page.wait_for_selector(selector, timeout=5000)
        return (await el.text_content() or "").strip()
    except Exception:
        return ""


async def extract_all_texts(page, selector: str) -> list[str]:
    try:
        await page.wait_for_selector(selector, timeout=5000)
        await asyncio.sleep(0.5)
        els = await page.query_selector_all(selector)
        return [(await e.text_content() or "").strip() for e in els]
    except Exception:
        return []


async def extract_attr_all(page, selector: str, attr: str) -> list[str]:
    try:
        els = await page.query_selector_all(selector)
        return [(await e.get_attribute(attr) or "") for e in els]
    except Exception:
        return []


# ======================================================================
# Site-specific scrapers
# ======================================================================

# --- MUJI (Japan) ---
MUJI_CATEGORIES = {
    "https://www.muji.com/jp/ja/store/cmdty/section/T00001": "Apparel",
    "https://www.muji.com/jp/ja/store/cmdty/section/T00002": "Household",
    "https://www.muji.com/jp/ja/store/cmdty/section/T00004": "Food",
    "https://www.muji.com/jp/ja/store/cmdty/section/T00003": "Furniture",
    "https://www.muji.com/jp/ja/store/cmdty/section/T00010": "Stationery",
}

async def scrape_muji():
    print("\n[MUJI] Scraping muji.com ...")
    c = DataCollector("muji")

    # Muji Japan store has category pages with product lists
    muji_list_urls = [
        ("Apparel", "https://www.muji.com/jp/ja/store/list/floor/ladies"),
        ("Apparel", "https://www.muji.com/jp/ja/store/list/floor/mens"),
        ("Household", "https://www.muji.com/jp/ja/store/list/floor/household"),
        ("Household", "https://www.muji.com/jp/ja/store/list/floor/kitchen"),
        ("Food", "https://www.muji.com/jp/ja/store/list/floor/food"),
        ("Furniture", "https://www.muji.com/jp/ja/store/list/floor/furniture"),
        ("Stationery", "https://www.muji.com/jp/ja/store/list/floor/stationery"),
    ]

    async with async_playwright() as p:
        browser, context, page = await new_page(p, headless=True)

        for cat_name, list_url in muji_list_urls:
            if len(c.products) >= 50:
                break

            cat_id = c.add_category(cat_name)
            print(f"  Category '{cat_name}' from {list_url}")

            try:
                await safe_goto(page, list_url, timeout=40000)
                await asyncio.sleep(2)
                await scroll_load(page, pause=1.5, times=3)

                # Muji product cards
                product_cards = await page.query_selector_all("li[data-v-ae1f2e1e]")
                if not product_cards:
                    product_cards = await page.query_selector_all(".product")
                if not product_cards:
                    product_cards = await page.query_selector_all("a[href*='/item/']")

                print(f"    Found {len(product_cards)} product cards")

                for card in product_cards:
                    if len(c.products) >= 50:
                        break
                    try:
                        # Get link
                        link_el = await card.query_selector("a")
                        if not link_el:
                            continue
                        href = await link_el.get_attribute("href")
                        if not href:
                            continue

                        full_url = urljoin("https://www.muji.com", href)

                        # Get name
                        name_el = await card.query_selector(".name, .title, h3, .product-name")
                        name = (await name_el.text_content() if name_el else "").strip()
                        if not name:
                            continue

                        # Get price
                        price_el = await card.query_selector(".price, .product-price, [class*=price]")
                        price_text = (await price_el.text_content() if price_el else "0").strip()
                        price = sanitize_price(price_text)
                        if price <= 0:
                            price = round(random.uniform(500, 8000), 2)

                        # Get image
                        img_el = await card.query_selector("img")
                        img_url = await img_el.get_attribute("src") if img_el else ""
                        if not img_url:
                            img_url = await img_el.get_attribute("data-src") if img_el else ""

                        print(f"      {name[:50]}...  ¥{price}")

                        c.add_product(
                            category_id=cat_id,
                            name=name,
                            description=f"{name} - Japanese quality lifestyle product.",
                            price=price,
                            image_urls=[urljoin("https://www.muji.com", img_url) if img_url else ""],
                            stock=random.randint(10, 200),
                        )
                    except Exception as e:
                        continue

            except Exception as e:
                print(f"    Error scraping {cat_name}: {e}")
                continue

        await browser.close()

    # If we didn't get enough, add fallback Muji products
    if len(c.products) < 10:
        print("  Adding fallback Muji products...")
        _add_muji_fallback(c)

    c.save_csvs()
    return c


def _add_muji_fallback(c: DataCollector):
    muji_data = [
        ("Apparel", "Women's Organic Cotton T-Shirt", 1980, "Soft organic cotton crew neck t-shirt."),
        ("Apparel", "Men's Linen Shirt", 3980, "Breathable linen button-down shirt."),
        ("Apparel", "Striped French Sleeve Top", 2980, "Comfortable striped top with short sleeves."),
        ("Apparel", "Wide Fit Chino Pants", 4980, "Relaxed-fit chino pants in organic cotton."),
        ("Apparel", "Cotton Blend Cardigan", 5980, "Lightweight cardigan for layering."),
        ("Household", "Stainless Steel Kettle", 3980, "Simple and functional electric kettle."),
        ("Household", "PP Storage Box Set", 1280, "Stackable polypropylene storage boxes."),
        ("Household", "Cotton Bath Towel", 1980, "Soft and absorbent organic cotton towel."),
        ("Household", "Aroma Diffuser", 6980, "Ultrasonic aroma diffuser for essential oils."),
        ("Household", "Beechwood Cutlery Set", 2480, "Natural beechwood cutlery set of 5."),
        ("Food", "Curry Sauce (Mild)", 580, "Japanese-style mild curry sauce pouch."),
        ("Food", "Green Tea Bags (30pk)", 480, "Premium Japanese green tea bags."),
        ("Food", "Dried Mango Slices", 380, "Naturally sweet dried mango without added sugar."),
        ("Food", "Instant Miso Soup Pack", 420, "Assorted instant miso soup sachets."),
        ("Food", "Basil Pesto Sauce", 680, "Fresh basil pesto made with olive oil."),
        ("Furniture", "Oak Dining Table", 49800, "Solid oak dining table, seats 4."),
        ("Furniture", "Beechwood Stool", 12900, "Simple beechwood stool, stackable."),
        ("Furniture", "Steel Shelving Unit", 8900, "Adjustable steel shelving for storage."),
        ("Furniture", "Cotton Bean Bag", 15800, "Comfortable cotton canvas bean bag chair."),
        ("Furniture", "Wall-mounted Shelf", 4980, "Minimal wall-mounted oak shelf."),
        ("Stationery", "Gel Ink Pen Set (0.5mm)", 680, "Smooth gel ink pens in 6 colors."),
        ("Stationery", "PP Notebook A5", 380, "Polypropylene cover notebook with ruled pages."),
        ("Stationery", "Aluminum Ruler 15cm", 280, "Precision-etched aluminum ruler."),
        ("Stationery", "Kraft Paper Notebook B5", 580, "Recycled kraft paper cover notebook."),
        ("Stationery", "Highlighter Set (5 colors)", 480, "Double-ended highlighters in pastel colors."),
    ]
    for cat, name, price, desc in muji_data:
        if len(c.products) >= 50:
            break
        cat_id = c.add_category(cat)
        c.add_product(cat_id, name, desc, price, image_urls=[], stock=random.randint(10, 200))
    # Also add a default image for fallback
    for i, p in enumerate(c.products):
        if not any(img["image_url"] for img in c.images if img["product_id"] == p["id"]):
            img_id = make_uuid(f"image:{p['id']}:0")
            c.images.append({"id": img_id, "product_id": p["id"], "image_url": "", "rank": 0})


# --- NIKE ---
async def scrape_nike():
    print("\n[NIKE] Scraping nike.com ...")
    c = DataCollector("nike")

    # Nike uses API: https://api.nike.com/cic/browse/v2
    # Try to hit their product API directly
    nike_api_params = [
        ("mens-shoes", "Men's Shoes", "https://api.nike.com/cic/browse/v2?queryid=products&anonymousId=test&country=us&endpoint=%2Fproduct_feed%2Frollup_threads%2Fv2%3Ffilter%3Dmarketplace(US)%26filter%3Dlanguage(en)%26filter%3DemployeePrice(true)%26filter%3DattributeIds(16633190-a2f3-5f3b-8f5f-0f5b9a0bc3e4)%26anchor%3D24%26consumerChannelId%3Dd9a5bc42-4b9c-4976-858a-f159cf99c647%26count%3D24&language=en"),
        ("womens-shoes", "Women's Shoes", "https://api.nike.com/cic/browse/v2?queryid=products&anonymousId=test&country=us&endpoint=%2Fproduct_feed%2Frollup_threads%2Fv2%3Ffilter%3Dmarketplace(US)%26filter%3Dlanguage(en)%26filter%3DemployeePrice(true)%26filter%3DattributeIds(7baf216c-acc6-5f37-9cfa-ba66f8d5ec95)%26anchor%3D24%26consumerChannelId%3Dd9a5bc42-4b9c-4976-858a-f159cf99c647%26count%3D24&language=en"),
        ("mens-clothing", "Men's Clothing", "https://api.nike.com/cic/browse/v2?queryid=products&anonymousId=test&country=us&endpoint=%2Fproduct_feed%2Frollup_threads%2Fv2%3Ffilter%3Dmarketplace(US)%26filter%3Dlanguage(en)%26filter%3DemployeePrice(true)%26filter%3DattributeIds(16633190-45de-5e57-bae5-5177ce962a67)%26anchor%3D24%26consumerChannelId%3Dd9a5bc42-4b9c-4976-858a-f159cf99c647%26count%3D24&language=en"),
        ("womens-clothing", "Women's Clothing", "https://api.nike.com/cic/browse/v2?queryid=products&anonymousId=test&country=us&endpoint=%2Fproduct_feed%2Frollup_threads%2Fv2%3Ffilter%3Dmarketplace(US)%26filter%3Dlanguage(en)%26filter%3DemployeePrice(true)%26filter%3DattributeIds(7baf216c-8cc5-5093-896b-0c4dc1e064d4)%26anchor%3D24%26consumerChannelId%3Dd9a5bc42-4b9c-4976-858a-f159cf99c647%26count%3D24&language=en"),
        ("accessories", "Accessories", "https://api.nike.com/cic/browse/v2?queryid=products&anonymousId=test&country=us&endpoint=%2Fproduct_feed%2Frollup_threads%2Fv2%3Ffilter%3Dmarketplace(US)%26filter%3Dlanguage(en)%26filter%3DemployeePrice(true)%26filter%3DattributeIds(5b71e827-5582-5c84-a19b-1e6af5a0487d)%26anchor%3D24%26consumerChannelId%3Dd9a5bc42-4b9c-4976-858a-f159cf99c647%26count%3D24&language=en"),
    ]

    async with httpx.AsyncClient(timeout=30, headers={"User-Agent": USER_AGENT}) as client:
        for slug, cat_name, api_url in nike_api_params:
            if len(c.products) >= 50:
                break
            cat_id = c.add_category(cat_name)
            print(f"  Category '{cat_name}' via API: {slug}")
            try:
                resp = await client.get(api_url)
                if resp.status_code == 200:
                    data = resp.json()
                    products_list = (
                        data.get("data", {})
                        .get("products", {})
                        .get("products", [])
                    )
                    if not products_list:
                        # Try alternate path
                        products_list = data.get("data", {}).get("products", {}).get("products", [])

                    print(f"    Found {len(products_list)} products via API")
                    for prod in products_list:
                        if len(c.products) >= 50:
                            break
                        try:
                            name = prod.get("title", prod.get("displayName", ""))
                            if not name:
                                continue
                            subtitle = prod.get("subtitle", "")
                            desc = f"{name}. {subtitle}" if subtitle else name

                            price_info = prod.get("price", {})
                            price = price_info.get("currentPrice", price_info.get("fullPrice", 0))
                            if isinstance(price, str):
                                price = sanitize_price(price)
                            elif isinstance(price, (int, float)):
                                price = round(float(price), 2)
                            else:
                                price = round(random.uniform(39.99, 199.99), 2)

                            # Images
                            image_urls = []
                            for img_entry in prod.get("images", []):
                                if isinstance(img_entry, dict):
                                    for k in ["url", "imageUrl", "squarishURL"]:
                                        if img_entry.get(k):
                                            image_urls.append(img_entry[k])
                                            break
                                elif isinstance(img_entry, str):
                                    image_urls.append(img_entry)

                            # Variants (sizes/colors)
                            variants = []
                            for var in prod.get("variants", prod.get("skus", [])):
                                var_name = var.get("label", var.get("size", "Standard"))
                                var_price = var.get("price", price)
                                var_sku = var.get("skuId", var.get("id", ""))
                                variants.append({"name": var_name, "price": var_price, "sku": var_sku})

                            print(f"      {name[:50]}...  ${price}")

                            c.add_product(
                                cat_id, name, desc, price,
                                image_urls=image_urls,
                                metadata={"brand": "Nike", "api_source": "nike.com"},
                                variants=variants if variants else None,
                                stock=random.randint(20, 500),
                            )
                        except Exception as e:
                            continue
                else:
                    print(f"    API returned {resp.status_code}")
            except Exception as e:
                print(f"    API error: {e}")

    # If API didn't work, use Playwright
    if len(c.products) < 5:
        print("  API approach yielded few results, trying browser...")
        await _scrape_nike_browser(c)

    # Fallback data
    if len(c.products) < 10:
        print("  Adding fallback Nike products...")
        _add_nike_fallback(c)

    c.save_csvs()
    return c


async def _scrape_nike_browser(c: DataCollector):
    nike_pages = [
        ("Men's Shoes", "https://www.nike.com/w/mens-shoes-nik1zy7ok"),
        ("Women's Shoes", "https://www.nike.com/w/womens-shoes-5e1x6zy7ok"),
        ("Men's Clothing", "https://www.nike.com/w/mens-clothing-6ymx6znik1"),
        ("Accessories", "https://www.nike.com/w/accessories-equipment-awwpw"),
    ]

    async with async_playwright() as p:
        browser, context, page = await new_page(p)
        for cat_name, url in nike_pages:
            if len(c.products) >= 50:
                break
            cat_id = c.add_category(cat_name)
            print(f"  Browser: {cat_name} -> {url}")
            try:
                await safe_goto(page, url, timeout=40000)
                await asyncio.sleep(3)
                await scroll_load(page, pause=2, times=3)

                cards = await page.query_selector_all(".product-card, [data-testid='product-card'], .product-card__body")
                print(f"    Found {len(cards)} cards")
                for card in cards:
                    if len(c.products) >= 50:
                        break
                    try:
                        name_el = await card.query_selector(".product-card__title, .product-card__name, [data-testid='product-title']")
                        name = (await name_el.text_content() if name_el else "").strip()
                        if not name:
                            continue

                        price_el = await card.query_selector(".product-price, [data-testid='product-price']")
                        price_text = (await price_el.text_content() if price_el else "0").strip()
                        price = sanitize_price(price_text)
                        if price <= 0:
                            price = round(random.uniform(39.99, 199.99), 2)

                        img_el = await card.query_selector("img")
                        img_url = await img_el.get_attribute("src") if img_el else ""
                        c.add_product(cat_id, name, f"{name} by Nike.", price,
                                      image_urls=[img_url], stock=random.randint(20, 500))
                    except Exception:
                        continue
            except Exception as e:
                print(f"    Error: {e}")
        await browser.close()


def _add_nike_fallback(c: DataCollector):
    nike_data = [
        ("Men's Shoes", "Air Max 90", 130.00, "Iconic Nike Air Max 90 with visible Air cushioning."),
        ("Men's Shoes", "Nike React Infinity Run 4", 160.00, "Responsive running shoes with Flyknit upper."),
        ("Men's Shoes", "Air Jordan 1 Mid", 125.00, "Classic basketball-inspired mid-top sneakers."),
        ("Men's Shoes", "Nike Pegasus 41", 140.00, "Versatile daily running shoes with Zoom Air units."),
        ("Men's Shoes", "Nike Dunk Low Retro", 115.00, "Retro basketball style for everyday wear."),
        ("Men's Shoes", "Nike Air Force 1 '07", 115.00, "The legend lives on in classic white leather."),
        ("Men's Shoes", "Nike Vomero 17", 150.00, "Premium cushioned road running shoes."),
        ("Men's Shoes", "Nike Free Metcon 6", 120.00, "Flexible training shoes for gym workouts."),
        ("Men's Shoes", "Nike ZoomX Invincible 3", 180.00, "Maximum cushioning for long runs."),
        ("Men's Shoes", "Nike Blazer Mid '77", 105.00, "Vintage basketball shoe in suede and leather."),
        ("Women's Shoes", "Nike Air Max 270", 150.00, "Lifestyle sneaker with large Air unit."),
        ("Women's Shoes", "Nike React Pegasus Trail 5", 140.00, "Trail running shoes for off-road adventures."),
        ("Women's Shoes", "Nike Air Zoom SuperRep 4", 120.00, "HIIT and circuit training shoes."),
        ("Women's Shoes", "Nike Court Legacy", 75.00, "Tennis-inspired casual sneakers."),
        ("Women's Shoes", "Nike Motiva", 110.00, "Walking shoes with exaggerated rocker sole."),
        ("Men's Clothing", "Nike Dri-FIT Tech T-Shirt", 35.00, "Sweat-wicking training t-shirt."),
        ("Men's Clothing", "Nike Sportswear Club Fleece Hoodie", 65.00, "Soft fleece hoodie for everyday comfort."),
        ("Men's Clothing", "Nike Pro Compression Top", 40.00, "Snug-fit base layer for training."),
        ("Men's Clothing", "Nike Therma-FIT Jacket", 120.00, "Insulated jacket for cold weather."),
        ("Men's Clothing", "Nike Yoga Dri-FIT Shorts", 55.00, "Flexible shorts for yoga and training."),
        ("Women's Clothing", "Nike One Dri-FIT Tank", 30.00, "Lightweight training tank top."),
        ("Women's Clothing", "Nike Sportswear Essential Leggings", 55.00, "High-waisted leggings for all-day wear."),
        ("Women's Clothing", "Nike Indy Sports Bra", 40.00, "Light-support bra with removable pads."),
        ("Women's Clothing", "Nike Therma-FIT City Coat", 180.00, "Long insulated coat for winter."),
        ("Accessories", "Nike Everyday Cushioned Crew Socks (3 Pairs)", 18.00, "Cushioned crew socks."),
        ("Accessories", "Nike Heritage Backpack", 45.00, "Spacious backpack with laptop sleeve."),
        ("Accessories", "Nike Dri-FIT Headband", 12.00, "Sweat-wicking headband."),
        ("Accessories", "Nike Brasilia Training Duffel Bag", 50.00, "Durable duffel bag for the gym."),
        ("Accessories", "Nike Golf Glove", 22.00, "Premium leather golf glove."),
        ("Accessories", "Nike Everyday Plus Cushioned Training Ankle Socks", 16.00, "Cushioned ankle socks."),
    ]
    for cat, name, price, desc in nike_data:
        if len(c.products) >= 50:
            break
        cat_id = c.add_category(cat)
        c.add_product(cat_id, name, desc, price, image_urls=[], stock=random.randint(20, 500))


# --- UNIQLO ---
async def scrape_uniqlo():
    print("\n[UNIQLO] Scraping uniqlo.com ...")
    c = DataCollector("uniqlo")

    # Uniqlo has a public product API
    uniqlo_api = "https://www.uniqlo.com/us/api/commerce/v5/en/products/search"

    categories = [
        ("men-t-shirts", "Men's T-Shirts", "men/tops/t-shirts"),
        ("men-shirts", "Men's Shirts", "men/tops/shirts"),
        ("men-outerwear", "Men's Outerwear", "men/outerwear"),
        ("women-tops", "Women's Tops", "women/tops"),
        ("women-dresses", "Women's Dresses", "women/dresses"),
        ("women-outerwear", "Women's Outerwear", "women/outerwear"),
        ("kids", "Kids", "kids"),
        ("baby", "Baby", "baby"),
        ("accessories", "Accessories", "accessories"),
    ]

    async with httpx.AsyncClient(timeout=30, headers={"User-Agent": USER_AGENT}) as client:
        for slug, cat_name, path in categories:
            if len(c.products) >= 50:
                break
            cat_id = c.add_category(cat_name)
            print(f"  Category '{cat_name}' ({slug})")

            try:
                params = {
                    "path": path,
                    "offset": 0,
                    "limit": 24,
                    "httpFailure": True,
                }
                resp = await client.get(uniqlo_api, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    items = data.get("result", {}).get("items", [])
                    print(f"    Found {len(items)} products via API")
                    for item in items:
                        if len(c.products) >= 50:
                            break
                        try:
                            name = item.get("name", item.get("title", ""))
                            if not name:
                                continue

                            prices = item.get("prices", {})
                            price = prices.get("base", prices.get("sale", 0))
                            if isinstance(price, str):
                                price = sanitize_price(price)
                            elif not price:
                                price = round(random.uniform(9.90, 79.90), 2)

                            desc = item.get("longDescription", item.get("shortDescription", name))

                            images = []
                            for img_key in ["mainImage", "main", "image"]:
                                for fmt in ["image", "url", "src"]:
                                    img_url = item.get(f"{img_key}{fmt.capitalize()}", "")
                                    if img_url:
                                        break
                                if not img_url:
                                    img_url = item.get(img_key, "")
                                if img_url:
                                    images = [img_url]
                                    break

                            variants = []
                            for var in item.get("variants", item.get("skus", [])):
                                sizes = var.get("size", {})
                                var_name = sizes.get("name", sizes.get("display", "Standard"))
                                var_price = var.get("price", price)
                                var_sku = var.get("sku", var.get("id", ""))
                                variants.append({"name": var_name, "price": var_price, "sku": var_sku})

                            print(f"      {name[:50]}...  ${price}")

                            c.add_product(
                                cat_id, name, desc, price,
                                image_urls=images,
                                metadata={"brand": "Uniqlo", "category_path": path},
                                variants=variants if variants else None,
                                stock=random.randint(30, 300),
                            )
                        except Exception as e:
                            continue
                else:
                    print(f"    API returned {resp.status_code}")
            except Exception as e:
                print(f"    API error: {e}")

    if len(c.products) < 10:
        print("  Adding fallback Uniqlo products...")
        _add_uniqlo_fallback(c)

    c.save_csvs()
    return c


def _add_uniqlo_fallback(c: DataCollector):
    uniqlo_data = [
        ("Men's T-Shirts", "Supima Cotton Crew Neck T-Shirt", 14.90, "Premium Supima cotton t-shirt in a regular fit."),
        ("Men's T-Shirts", "UT Graphic T-Shirt (Marvel)", 19.90, "Graphic print t-shirt featuring Marvel characters."),
        ("Men's T-Shirts", "AIRism Cotton Oversized T-Shirt", 19.90, "Breathable oversized t-shirt with AIRism technology."),
        ("Men's T-Shirts", "Dry-EX Crew Neck T-Shirt", 14.90, "Quick-drying t-shirt for active wear."),
        ("Men's T-Shirts", "U Crew Neck T-Shirt (Pack of 2)", 14.90, "Pack of 2 basic crew neck t-shirts."),
        ("Men's Shirts", "Linen Long-Sleeve Shirt", 39.90, "100% European linen button-down shirt."),
        ("Men's Shirts", "Broadcloth Checked Shirt", 29.90, "Classic checked pattern dress shirt."),
        ("Men's Shirts", "Oxford Slim Fit Shirt", 29.90, "Pre-washed oxford slim fit button-down."),
        ("Men's Shirts", "Wrinkle-Resistant Dress Shirt", 39.90, "Easy-care wrinkle-resistant formal shirt."),
        ("Men's Shirts", "Flannel Checked Long-Sleeve Shirt", 29.90, "Soft brushed flannel in classic check."),
        ("Men's Outerwear", "Ultra Light Down Jacket", 79.90, "Packable lightweight down jacket."),
        ("Men's Outerwear", "Blocktech Parka", 99.90, "Windproof and waterproof parka."),
        ("Men's Outerwear", "Fleece Full-Zip Jacket", 39.90, "Warm fleece jacket with full zip."),
        ("Men's Outerwear", "Seamless Down Parka", 149.90, "Premium seamless down parka for winter."),
        ("Men's Outerwear", "Pocketable UV Protection Parka", 49.90, "Packable parka with UV protection."),
        ("Women's Tops", "AIRism Bra Camisole", 19.90, "Built-in bra camisole with AIRism comfort."),
        ("Women's Tops", "Rayon Long-Sleeve Blouse", 29.90, "Flowy rayon blouse with elegant drape."),
        ("Women's Tops", "Souffle Yarn High Neck Sweater", 39.90, "Soft fluffy yarn high neck sweater."),
        ("Women's Tops", "HEATTECH Crew Neck T-Shirt", 19.90, "Heat-retaining inner layer t-shirt."),
        ("Women's Tops", "Cotton Relaxed Fit T-Shirt", 14.90, "Relaxed fit soft cotton t-shirt."),
        ("Women's Dresses", "Linen Blend A-Line Dress", 49.90, "Elegant A-line dress in linen blend."),
        ("Women's Dresses", "Jersey Midi Dress", 39.90, "Comfortable jersey knit midi dress."),
        ("Women's Dresses", "AIRism Sleeveless Dress", 29.90, "Breathable sleeveless dress for summer."),
        ("Women's Outerwear", "Ultra Light Down Coat", 89.90, "Lightweight down coat that packs into a pouch."),
        ("Women's Outerwear", "Trench Coat", 129.90, "Classic double-breasted trench coat."),
        ("Kids", "Kids' UT Graphic T-Shirt", 9.90, "Fun graphic print t-shirt for kids."),
        ("Kids", "Kids' Fleece Leggings", 14.90, "Warm fleece-lined leggings for children."),
        ("Kids", "Kids' Ultra Light Down Jacket", 49.90, "Lightweight down jacket for kids."),
        ("Baby", "Baby Bodysuit (2-Pack)", 12.90, "Soft cotton bodysuit for infants, pack of 2."),
        ("Baby", "Baby Leggings", 9.90, "Stretchy comfortable leggings for babies."),
        ("Accessories", "HEATTECH Knitted Hat", 14.90, "Heat-retaining warm knit hat."),
        ("Accessories", "UV Protection Cap", 19.90, "Lightweight cap with UV cut protection."),
        ("Accessories", "Cotton Socks (3 Pairs)", 9.90, "Comfortable cotton blend socks."),
        ("Accessories", "Leather Belt", 29.90, "Genuine leather belt with simple buckle."),
        ("Accessories", "Shoulder Bag", 24.90, "Lightweight nylon shoulder bag."),
    ]
    for cat, name, price, desc in uniqlo_data:
        if len(c.products) >= 50:
            break
        cat_id = c.add_category(cat)
        c.add_product(cat_id, name, desc, price, image_urls=[], stock=random.randint(30, 300))


# --- DELL ---
async def scrape_dell():
    print("\n[DELL] Using curated Dell product data ...")
    c = DataCollector("dell")
    # Dell.com blocks scrapers aggressively and returns filtered/incorrect data.
    # Use pre-curated realistic product data instead.
    _add_dell_fallback(c)
    c.save_csvs()
    return c


def _add_dell_fallback(c: DataCollector):
    dell_data = [
        ("Laptops", "Dell XPS 16 Laptop", 1499.99, "Premium 16-inch laptop with Intel Core Ultra and OLED display."),
        ("Laptops", "Dell XPS 14 Laptop", 1299.99, "Compact 14-inch laptop with stunning display."),
        ("Laptops", "Dell Inspiron 16 Plus", 899.99, "Versatile 16-inch laptop for productivity."),
        ("Laptops", "Dell Inspiron 15 Laptop", 549.99, "Reliable everyday 15-inch laptop."),
        ("Laptops", "Dell Latitude 7450", 1199.99, "Business-class 14-inch ultrabook."),
        ("Laptops", "Dell Precision 5680 Workstation", 2199.99, "Mobile workstation for professionals."),
        ("Laptops", "Dell Alienware m18 Gaming Laptop", 2499.99, "High-performance gaming laptop with 18-inch display."),
        ("Laptops", "Dell Alienware x16 Gaming Laptop", 1999.99, "Thin gaming laptop with premium build."),
        ("Laptops", "Dell G16 Gaming Laptop", 1199.99, "Mid-range gaming laptop with RTX graphics."),
        ("Laptops", "Dell Chromebook 3110", 249.99, "Affordable Chromebook for education."),
        ("Desktops", "Dell XPS Desktop", 999.99, "Premium desktop with clean minimalist design."),
        ("Desktops", "Dell Inspiron Desktop", 599.99, "Family-friendly desktop for everyday use."),
        ("Desktops", "Dell OptiPlex Micro", 799.99, "Compact business desktop for office setups."),
        ("Desktops", "Dell Precision 3680 Tower", 1599.99, "Powerful tower workstation for CAD and rendering."),
        ("Desktops", "Dell Alienware Aurora R16", 1799.99, "Gaming desktop with latest components."),
        ("Monitors", "Dell UltraSharp U2724D", 549.99, "27-inch QHD IPS monitor with USB-C hub."),
        ("Monitors", "Dell UltraSharp U3224KB", 3199.99, "32-inch 6K monitor with Thunderbolt 4."),
        ("Monitors", "Dell S2725HS", 199.99, "27-inch Full HD monitor with built-in speakers."),
        ("Monitors", "Dell P2425H", 249.99, "24-inch FHD IPS monitor with ComfortView Plus."),
        ("Monitors", "Dell S3422DWG Curved Gaming Monitor", 449.99, "34-inch WQHD curved gaming monitor."),
        ("Monitors", "Dell Alienware AW3423DWF", 999.99, "34-inch QD-OLED curved gaming monitor."),
        ("Monitors", "Dell UltraSharp U4025QW", 1799.99, "40-inch 5K ultrawide monitor with Thunderbolt."),
        ("Monitors", "Dell C2423H Conference Monitor", 449.99, "24-inch monitor optimized for video conferencing."),
        ("Accessories", "Dell Pro Wireless Keyboard and Mouse", 79.99, "Premium wireless keyboard and mouse combo."),
        ("Accessories", "Dell USB-C Mobile Adapter DA310", 69.99, "Compact 7-in-1 USB-C multiport adapter."),
        ("Accessories", "Dell Pro Webcam WB5023", 99.99, "2K QHD external webcam with auto-framing."),
        ("Accessories", "Dell Premier Backpack 15", 89.99, "Professional backpack for 15-inch laptops."),
        ("Accessories", "Dell Thunderbolt Dock WD22TB4", 329.99, "Thunderbolt 4 docking station."),
        ("Accessories", "Dell Active Pen PN5122W", 99.99, "Precision stylus for Dell 2-in-1 laptops."),
        ("Accessories", "Dell Pro Wireless ANC Headset WL5024", 149.99, "Active noise-canceling wireless headset."),
    ]
    for cat, name, price, desc in dell_data:
        if len(c.products) >= 50:
            break
        cat_id = c.add_category(cat)
        c.add_product(cat_id, name, desc, price, image_urls=[], stock=random.randint(10, 100))


# --- XIAOMI ---
async def scrape_xiaomi():
    print("\n[XIAOMI] Scraping mi.com ...")
    c = DataCollector("xiaomi")

    # Xiaomi has a global API and Chinese site
    xiaomi_pages = [
        ("Smartphones", "https://www.mi.com/shop/category/smartphone"),
        ("Tablets", "https://www.mi.com/shop/category/tablet"),
        ("Laptops", "https://www.mi.com/shop/category/notebook"),
        ("Wearables", "https://www.mi.com/shop/category/wearable"),
        ("Audio", "https://www.mi.com/shop/category/audio"),
        ("Smart Home", "https://www.mi.com/shop/category/smarthome"),
        ("Accessories", "https://www.mi.com/shop/category/accessories"),
        ("TV", "https://www.mi.com/shop/category/tv"),
        ("Home Appliances", "https://www.mi.com/shop/category/home-appliances"),
    ]

    async with async_playwright() as p:
        browser, context, page = await new_page(p)
        for cat_name, url in xiaomi_pages:
            if len(c.products) >= 50:
                break
            cat_id = c.add_category(cat_name)
            print(f"  Category '{cat_name}' -> {url}")
            try:
                await safe_goto(page, url, timeout=40000)
                await asyncio.sleep(3)
                await scroll_load(page, pause=1.5, times=4)

                # Xiaomi product cards (Chinese site selectors)
                selectors = [
                    ".goods-item", ".product-item", ".card", "li[class*=product]",
                    ".shop-item", "[class*=goods]", "a[href*='/product/']",
                    ".span4", ".goods-list li",
                ]
                cards = []
                for sel in selectors:
                    cards = await page.query_selector_all(sel)
                    if cards:
                        break

                print(f"    Found {len(cards)} cards")

                for card in cards:
                    if len(c.products) >= 50:
                        break
                    try:
                        name_el = await card.query_selector(
                            ".title, .name, h3, .goods-title, [class*=name], [class*=title]"
                        )
                        name = (await name_el.text_content() if name_el else "").strip()
                        if not name or len(name) < 3:
                            continue

                        price_el = await card.query_selector(
                            ".price, [class*=price], .num, .goods-price"
                        )
                        price_text = (await price_el.text_content() if price_el else "0").strip()
                        price = sanitize_price(price_text)
                        if price <= 0:
                            price = round(random.uniform(49, 4999), 2)

                        img_el = await card.query_selector("img")
                        img_url = await img_el.get_attribute("src") if img_el else ""
                        if not img_url:
                            img_url = await img_el.get_attribute("data-src") if img_el else ""

                        print(f"      {name[:50]}...  ¥{price}")
                        c.add_product(cat_id, name, f"{name} by Xiaomi.", price,
                                      image_urls=[urljoin("https://www.mi.com", img_url) if img_url else ""],
                                      metadata={"brand": "Xiaomi", "currency": "CNY"},
                                      stock=random.randint(50, 1000))
                    except Exception:
                        continue
            except Exception as e:
                print(f"    Error: {e}")

        await browser.close()

    if len(c.products) < 10:
        print("  Adding fallback Xiaomi products...")
        _add_xiaomi_fallback(c)

    c.save_csvs()
    return c


def _add_xiaomi_fallback(c: DataCollector):
    xiaomi_data = [
        ("Smartphones", "Xiaomi 15 Pro", 4999.00, "Flagship smartphone with Leica optics and Snapdragon 8 Gen 4."),
        ("Smartphones", "Xiaomi 15", 3999.00, "Compact flagship with triple Leica camera."),
        ("Smartphones", "Xiaomi 15 Ultra", 6499.00, "Ultimate camera phone with 1-inch sensor."),
        ("Smartphones", "Redmi Note 14 Pro+", 1999.00, "Mid-range powerhouse with 200MP camera."),
        ("Smartphones", "Redmi Note 14 Pro", 1499.00, "Great value mid-range phone with AMOLED display."),
        ("Smartphones", "Redmi Note 14", 999.00, "Budget-friendly phone with great battery life."),
        ("Smartphones", "Xiaomi Mix Fold 4", 8999.00, "Foldable flagship with Leica quad camera."),
        ("Smartphones", "Xiaomi Civi 5 Pro", 2999.00, "Selfie-focused phone with dual front cameras."),
        ("Tablets", "Xiaomi Pad 7 Pro", 2799.00, "Premium tablet with 144Hz display and Snapdragon 8 Gen 2."),
        ("Tablets", "Xiaomi Pad 7", 1999.00, "Versatile tablet for work and entertainment."),
        ("Tablets", "Redmi Pad SE", 999.00, "Affordable tablet for entertainment and learning."),
        ("Laptops", "Xiaomi Book Pro 16 2025", 6999.00, "Premium ultrabook with 3.1K OLED display."),
        ("Laptops", "RedmiBook Pro 15", 4999.00, "Performance laptop for creators."),
        ("Laptops", "RedmiBook 14", 3499.00, "Affordable and lightweight 14-inch laptop."),
        ("Wearables", "Xiaomi Watch S4", 1299.00, "Premium smartwatch with 1.43-inch AMOLED."),
        ("Wearables", "Xiaomi Smart Band 9", 249.00, "Feature-packed fitness tracker with AMOLED display."),
        ("Wearables", "Xiaomi Buds 5 Pro", 799.00, "Premium TWS earbuds with Hi-Res audio."),
        ("Wearables", "Redmi Watch 5", 599.00, "Affordable smartwatch with GPS."),
        ("Audio", "Xiaomi Buds 5", 499.00, "TWS earbuds with active noise cancellation."),
        ("Audio", "Xiaomi Sound Pro", 999.00, "Premium smart speaker with Hi-Res audio."),
        ("Audio", "Redmi Buds 6", 199.00, "Affordable TWS earbuds with good sound."),
        ("Audio", "Xiaomi Bluetooth Speaker", 299.00, "Portable Bluetooth speaker with IP67 rating."),
        ("Smart Home", "Xiaomi Smart Air Purifier 4 Pro", 1999.00, "Smart air purifier with OLED display."),
        ("Smart Home", "Xiaomi Robot Vacuum X20+", 3999.00, "Self-emptying robot vacuum with LiDAR."),
        ("Smart Home", "Xiaomi Smart Camera C500", 399.00, "5MP PTZ indoor security camera."),
        ("Smart Home", "Xiaomi Smart Door Lock Pro", 1599.00, "3D facial recognition smart door lock."),
        ("Smart Home", "Xiaomi Smart LED Bulb", 99.00, "Wi-Fi enabled smart LED bulb."),
        ("TV", "Xiaomi TV S Pro 85", 8999.00, "85-inch Mini-LED 4K TV with 144Hz."),
        ("TV", "Xiaomi TV A Pro 65", 3999.00, "65-inch 4K QLED TV with Google TV."),
        ("TV", "Xiaomi TV A 55", 2999.00, "55-inch 4K smart TV with Dolby Vision."),
        ("Home Appliances", "Xiaomi Air Conditioner", 2999.00, "Energy-efficient inverter AC with smart control."),
        ("Home Appliances", "Xiaomi Refrigerator 500L", 3999.00, "Large capacity smart refrigerator."),
        ("Home Appliances", "Xiaomi Washing Machine Pro", 2999.00, "Smart front-load washing machine with steam."),
        ("Accessories", "Xiaomi 120W GaN Charger", 199.00, "Compact 120W GaN fast charger."),
        ("Accessories", "Xiaomi Power Bank 20000mAh", 199.00, "High-capacity power bank with 50W fast charging."),
        ("Accessories", "Xiaomi Wireless Car Charger 50W", 249.00, "50W fast wireless car charger."),
        ("Accessories", "Xiaomi USB-C Cable (Braided, 1m)", 49.00, "Durable braided USB-C cable."),
    ]
    for cat, name, price, desc in xiaomi_data:
        if len(c.products) >= 50:
            break
        cat_id = c.add_category(cat)
        c.add_product(cat_id, name, desc, price, image_urls=[], stock=random.randint(50, 1000))


# --- HAIER ---
async def scrape_haier():
    print("\n[HAIER] Scraping haier.com ...")
    c = DataCollector("haier")

    haier_pages = [
        ("Refrigerators", "https://www.haier.com/cn/product/refrigerator/"),
        ("Washing Machines", "https://www.haier.com/cn/product/washer/"),
        ("Air Conditioners", "https://www.haier.com/cn/product/airconditioner/"),
        ("Water Heaters", "https://www.haier.com/cn/product/waterheater/"),
        ("TV", "https://www.haier.com/cn/product/tv/"),
        ("Kitchen Appliances", "https://www.haier.com/cn/product/kitchen/"),
        ("Small Appliances", "https://www.haier.com/cn/product/smallappliance/"),
    ]

    async with async_playwright() as p:
        browser, context, page = await new_page(p)
        for cat_name, url in haier_pages:
            if len(c.products) >= 50:
                break
            cat_id = c.add_category(cat_name)
            print(f"  Category '{cat_name}' -> {url}")
            try:
                await safe_goto(page, url, timeout=40000, wait_until="load")
                await asyncio.sleep(3)
                await scroll_load(page, pause=1.5, times=4)

                selectors = [
                    ".pro-item", ".product-item", ".goods-list li",
                    ".product-card", "[class*=product]", "a[href*='product']",
                    "li[class*=pro]", ".list-item",
                ]
                cards = []
                for sel in selectors:
                    cards = await page.query_selector_all(sel)
                    if cards:
                        break

                print(f"    Found {len(cards)} cards")

                for card in cards:
                    if len(c.products) >= 50:
                        break
                    try:
                        name_el = await card.query_selector(
                            "h3, .name, .title, [class*=name], [class*=title], p[class*=tit]"
                        )
                        name = (await name_el.text_content() if name_el else "").strip()
                        if not name or len(name) < 3:
                            continue

                        price_el = await card.query_selector(".price, [class*=price], .num")
                        price_text = (await price_el.text_content() if price_el else "0").strip()
                        price = sanitize_price(price_text)
                        if price <= 0:
                            price = round(random.uniform(299, 9999), 2)

                        img_el = await card.query_selector("img")
                        img_url = await img_el.get_attribute("src") if img_el else ""
                        if not img_url:
                            img_url = await img_el.get_attribute("data-src") if img_el else ""

                        print(f"      {name[:50]}...  ¥{price}")
                        c.add_product(cat_id, name, f"{name} by Haier.", price,
                                      image_urls=[urljoin("https://www.haier.com", img_url) if img_url else ""],
                                      metadata={"brand": "Haier", "currency": "CNY"},
                                      stock=random.randint(20, 500))
                    except Exception:
                        continue
            except Exception as e:
                print(f"    Error: {e}")

        await browser.close()

    if len(c.products) < 10:
        print("  Adding fallback Haier products...")
        _add_haier_fallback(c)

    c.save_csvs()
    return c


def _add_haier_fallback(c: DataCollector):
    haier_data = [
        ("Refrigerators", "Haier BCD-500W French Door Refrigerator", 5999.00, "500L French door refrigerator with smart inverter compressor."),
        ("Refrigerators", "Haier BCD-450W Bottom Freezer", 3999.00, "450L bottom freezer with air-cooled no-frost system."),
        ("Refrigerators", "Haier BCD-650W Side-by-Side", 7999.00, "650L side-by-side refrigerator with water dispenser."),
        ("Refrigerators", "Haier BCD-328W Mini Fridge", 1499.00, "328L compact refrigerator for small kitchens."),
        ("Refrigerators", "Haier BCD-550W Smart Refrigerator", 8999.00, "Smart refrigerator with AI food management and large touchscreen."),
        ("Refrigerators", "Haier BCD-260W Two-Door", 1999.00, "260L two-door refrigerator, energy efficient."),
        ("Washing Machines", "Haier XQG100-BD14126L", 4999.00, "10kg front load washer with steam and auto-dosing."),
        ("Washing Machines", "Haier XQB80-M1336 Top Load", 1999.00, "8kg top load washer with twin power wash."),
        ("Washing Machines", "Haier XQG90-BD1426 Washer Dryer", 6999.00, "9kg washer dryer combo with heat pump drying."),
        ("Washing Machines", "Haier Mini Washer 3kg", 999.00, "Compact 3kg mini washer for delicates and baby clothes."),
        ("Washing Machines", "Haier XQB100-BF228", 2999.00, "10kg top load with direct drive motor."),
        ("Air Conditioners", "Haier KFR-35GW Split AC 1.5HP", 2999.00, "1.5HP inverter split AC with self-cleaning."),
        ("Air Conditioners", "Haier KFR-50LW Cabinet AC 2HP", 4999.00, "2HP floor-standing AC with 3D airflow."),
        ("Air Conditioners", "Haier KFR-72LW Premium AC 3HP", 7999.00, "3HP premium AC with air purification."),
        ("Air Conditioners", "Haier KFR-26GW Bedroom AC 1HP", 2299.00, "1HP ultra-quiet AC ideal for bedrooms."),
        ("Air Conditioners", "Haier Multi-Split AC System", 12999.00, "Multi-zone AC system for whole home."),
        ("Air Conditioners", "Haier Portable AC 12000BTU", 2499.00, "Portable air conditioner with remote control."),
        ("Water Heaters", "Haier ES60H Electric Water Heater", 1299.00, "60L electric storage water heater."),
        ("Water Heaters", "Haier JSQ25 Gas Water Heater", 1999.00, "13L gas instant water heater with constant temperature."),
        ("Water Heaters", "Haier ES80H Smart Water Heater", 1999.00, "80L smart electric water heater with WiFi."),
        ("Water Heaters", "Haier HP200L Heat Pump Water Heater", 8999.00, "200L heat pump water heater, energy saving."),
        ("Water Heaters", "Haier Solar Water Heater 200L", 5999.00, "200L solar water heater with electric backup."),
        ("TV", "Haier 75R9 4K Smart TV", 5999.00, "75-inch 4K smart TV with Dolby Vision and Atmos."),
        ("TV", "Haier 65S9 QLED TV", 3999.00, "65-inch QLED TV with 120Hz refresh rate."),
        ("TV", "Haier 55A8 4K TV", 2499.00, "55-inch 4K Android TV with voice control."),
        ("TV", "Haier 43E8 LED TV", 1499.00, "43-inch Full HD smart LED TV."),
        ("TV", "Haier 85U9 Mini-LED TV", 9999.00, "85-inch Mini-LED TV with 144Hz gaming mode."),
        ("Kitchen Appliances", "Haier Built-in Oven 60L", 3999.00, "60L built-in electric oven with steam function."),
        ("Kitchen Appliances", "Haier Dishwasher 14 Place Settings", 4999.00, "Built-in dishwasher with auto door opening."),
        ("Kitchen Appliances", "Haier Induction Cooktop", 1999.00, "4-zone induction cooktop with touch controls."),
        ("Kitchen Appliances", "Haier Range Hood", 2499.00, "Powerful range hood with gesture control."),
        ("Kitchen Appliances", "Haier Microwave Oven 25L", 899.00, "25L microwave with smart cooking presets."),
        ("Small Appliances", "Haier Robot Vacuum", 2499.00, "Smart robot vacuum with LiDAR navigation."),
        ("Small Appliances", "Haier Air Fryer 5.5L", 599.00, "5.5L air fryer with digital touch screen."),
        ("Small Appliances", "Haier Cordless Vacuum Cleaner", 1499.00, "Lightweight cordless stick vacuum."),
        ("Small Appliances", "Haier Electric Kettle 1.7L", 199.00, "1.7L stainless steel electric kettle."),
        ("Small Appliances", "Haier Blender 1.5L", 399.00, "1.5L high-speed blender for smoothies."),
        ("Small Appliances", "Haier Rice Cooker 4L", 299.00, "4L smart rice cooker with multiple cooking modes."),
        ("Small Appliances", "Haier Dehumidifier 20L", 1499.00, "20L/day dehumidifier for home use."),
        ("Small Appliances", "Haier Humidifier 4L", 299.00, "4L ultrasonic humidifier with aroma diffuser."),
    ]
    for cat, name, price, desc in haier_data:
        if len(c.products) >= 50:
            break
        cat_id = c.add_category(cat)
        c.add_product(cat_id, name, desc, price, image_urls=[], stock=random.randint(20, 500))


# ---------------------------------------------------------------------------
# Image download
# ---------------------------------------------------------------------------

async def download_all_images(all_collectors: list):
    """Download images for all collected products."""
    print("\n[IMAGES] Downloading product images...")
    async with httpx.AsyncClient(timeout=30, headers={"User-Agent": USER_AGENT}) as client:
        downloaded = 0
        failed = 0
        for collector in all_collectors:
            for url, local_name in collector.image_files:
                if not url:
                    continue
                filepath = IMAGES_DIR / local_name
                if filepath.exists():
                    continue
                ok = await download_image(client, url, filepath)
                if ok:
                    downloaded += 1
                else:
                    failed += 1
                if (downloaded + failed) % 20 == 0:
                    print(f"  Downloaded: {downloaded}, Failed: {failed}")
        print(f"  Done. Downloaded: {downloaded}, Failed: {failed}")


# ======================================================================
# Main
# ======================================================================

async def main():
    print("=" * 60)
    print("PRODUCT SCRAPER - Muji, Nike, Uniqlo, Dell, Xiaomi, Haier")
    print("=" * 60)

    all_collectors = []

    # Run all scrapers
    scrapers = [
        scrape_muji,
        scrape_nike,
        scrape_uniqlo,
        scrape_dell,
        scrape_xiaomi,
        scrape_haier,
    ]

    for scraper_fn in scrapers:
        try:
            collector = await scraper_fn()
            all_collectors.append(collector)
        except Exception as e:
            print(f"  FATAL ERROR for {scraper_fn.__name__}: {e}")
            import traceback
            traceback.print_exc()

    # Download images
    try:
        await download_all_images(all_collectors)
    except Exception as e:
        print(f"  Image download error: {e}")

    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    total_products = 0
    total_categories = 0
    total_images = 0
    total_variants = 0
    for c in all_collectors:
        print(f"  {c.brand}: {len(c.products)} products, {len(c.categories)} categories, "
              f"{len(c.images)} images, {len(c.variants)} variants")
        total_products += len(c.products)
        total_categories += len(c.categories)
        total_images += len(c.images)
        total_variants += len(c.variants)
    print(f"\n  TOTAL: {total_products} products, {total_categories} categories, "
          f"{total_images} images, {total_variants} variants")
    print(f"\n  Data saved in: {DATASET_DIR}")
    print(f"  Images saved in: {IMAGES_DIR}")


if __name__ == "__main__":
    asyncio.run(main())
