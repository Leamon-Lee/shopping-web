"""
Scraper for MUJI, Uniqlo, and IKEA — fetches real product data and images.
Outputs CSV files matching the import format.
Run inside Docker: docker exec shopping-backend python docker/postgres/dataset/scraper_mui.py
"""
import asyncio, csv, hashlib, json, os, random, re, uuid
from pathlib import Path
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

DATASET_DIR = Path(__file__).parent
IMAGES_DIR = DATASET_DIR / "imgs"
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36"

def slugify(text):
    t = re.sub(r"[^\w\s-]", "", text.lower()).strip()
    return re.sub(r"[\s_]+", "-", t)[:200]

def mk_uuid(seed):
    return str(uuid.UUID(hashlib.sha256(seed.encode()).hexdigest()[:32]))

def mk_hash(content):
    return hashlib.sha256(content.encode()).hexdigest()


class DC:
    def __init__(self, brand):
        self.brand = brand
        self.cats, self.prods, self.imgs, self.vars, self.img_files = [], [], [], [], []

    def add_cat(self, name, desc=""):
        cid = mk_uuid(f"cat:{self.brand}:{name}")
        if not any(c["id"] == cid for c in self.cats):
            self.cats.append({"id": cid, "name": name,
                              "description": desc or f"{name} products from {self.brand}"})
        return cid

    def add_prod(self, cid, name, desc, price, img_urls, meta=None, variants=None, stock=100):
        name = name.strip()
        if len(name) < 4 or any(p["name"] == name for p in self.prods):
            return ""
        pid = mk_uuid(f"prod:{self.brand}:{name}")
        self.prods.append({"id": pid, "product_hash": mk_hash(f"{self.brand}:{name}"),
                           "category_id": cid, "name": name, "slug": slugify(f"{self.brand}-{name}"),
                           "description": desc, "price": round(float(price), 2),
                           "available_item_count": stock,
                           "metadata_json": json.dumps(meta or {}, ensure_ascii=False)})
        for rank, u in enumerate(img_urls):
            if not u or not u.strip(): continue
            iid = mk_uuid(f"img:{pid}:{rank}")
            self.imgs.append({"id": iid, "product_id": pid, "image_url": u, "rank": rank})
            ext = ".jpg"
            p = u.split("?")[0].lower()
            if any(p.endswith(e) for e in [".png", ".webp", ".gif", ".jpeg"]):
                ext = os.path.splitext(p)[1]
            fname = f"{slugify(self.brand)}-{slugify(name)[:40]}-{rank}{ext}"
            self.img_files.append((u, fname))
        if variants:
            for v in variants:
                self.add_var(pid, v["name"], v.get("price", price), v.get("sku", ""))
        return pid

    def add_var(self, pid, name, price, sku="", currency="usd"):
        vid = mk_uuid(f"var:{pid}:{name}")
        if not sku: sku = f"{slugify(self.brand)}-{slugify(name)}-{random.randint(1000,9999)}"
        self.vars.append({"id": vid, "product_id": pid, "variant_id_str": f"var-{vid[:8]}",
                          "name": name[:160], "sku": sku[:64], "price": round(float(price), 2),
                          "currency_code": currency, "inventory_count": random.randint(10, 200),
                          "manages_inventory": True, "allows_backorder": False})

    def save(self):
        for attr, fname in [("cats", "product_categories"), ("prods", "products"),
                              ("imgs", "product_images"), ("vars", "product_variants")]:
            data = getattr(self, attr)
            if not data: continue
            path = DATASET_DIR / f"{self.brand}_{fname}.csv"
            keys = list(data[0].keys())
            with open(path, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=keys)
                w.writeheader(); w.writerows(data)
            print(f"  {fname}: {len(data)} rows")


# ======================================================================
# MUJI — scrape from muji.us (Shopify storefront)
# ======================================================================
MUJI_COLLECTIONS = [
    ("Storage", "https://muji.us/collections/storage"),
    ("Home", "https://muji.us/collections/home"),
    ("Clothing", "https://muji.us/collections/clothing"),
    ("Stationery", "https://muji.us/collections/stationery"),
    ("Travel", "https://muji.us/collections/travel"),
]


async def scrape_muji():
    print("\n[MUJI] Scraping muji.us ...")
    c = DC("muji")
    limits = httpx.Limits(max_keepalive_connections=5, max_connections=10)
    async with httpx.AsyncClient(timeout=30, headers={"User-Agent": UA}, limits=limits, follow_redirects=True) as client:
        # Try Shopify Products API first (most Shopify stores expose this)
        api_url = "https://muji.us/products.json"
        page = 1
        while len(c.prods) < 45 and page <= 5:
            try:
                resp = await client.get(f"{api_url}?page={page}&limit=50")
                if resp.status_code == 200:
                    data = resp.json()
                    products = data.get("products", [])
                    if not products: break
                    print(f"  API page {page}: {len(products)} products")
                    for p in products:
                        if len(c.prods) >= 45: break
                        title = p.get("title", "").strip()
                        if not title or len(title) < 3: continue
                        ptype = p.get("product_type") or "General"
                        cid = c.add_cat(ptype, f"{ptype} from MUJI")

                        desc = ""
                        body = p.get("body_html", "")
                        if body:
                            desc = BeautifulSoup(body, "html.parser").get_text()[:500]

                        # Get price from variants
                        variants = p.get("variants", [])
                        price = 0.0
                        var_list = []
                        for v in variants:
                            vprice = float(v.get("price", "0"))
                            if vprice > 0:
                                if price == 0 or vprice < price:
                                    price = vprice
                                vname = v.get("title", "Default")
                                if vname != "Default Title":
                                    var_list.append({"name": vname, "price": vprice,
                                                     "sku": v.get("sku", "")})

                        if price <= 0: continue

                        # Get images
                        img_urls = []
                        for img in p.get("images", []):
                            src = img.get("src", "")
                            if src:
                                if src.startswith("//"): src = "https:" + src
                                img_urls.append(src)

                        print(f"    {title[:60]} | ${price} | {len(img_urls)} imgs")
                        c.add_prod(cid, title, desc, price, img_urls,
                                   meta={"brand": "MUJI", "handle": p.get("handle", "")},
                                   variants=var_list if var_list else None,
                                   stock=random.randint(15, 150))
                else:
                    print(f"  API returned {resp.status_code}, trying HTML scraping...")
                    break
            except Exception as e:
                print(f"  API error: {e}")
                break
            page += 1

        # If API didn't get enough, try collection pages
        if len(c.prods) < 30:
            print("  Trying collection HTML scraping...")
            for cat_name, url in MUJI_COLLECTIONS:
                if len(c.prods) >= 45: break
                try:
                    resp = await client.get(url)
                    if resp.status_code != 200: continue
                    soup = BeautifulSoup(resp.text, "html.parser")
                    # Try JSON-LD structured data
                    for script in soup.find_all("script", type="application/ld+json"):
                        try:
                            ld = json.loads(script.string)
                            if isinstance(ld, dict) and ld.get("@type") == "ItemList":
                                for item in ld.get("itemListElement", []):
                                    if len(c.prods) >= 45: break
                                    item_data = item.get("item", {})
                                    name = item_data.get("name", "").strip()
                                    if not name or len(name) < 3: continue
                                    # Already added via API? skip
                                    if any(p["name"] == name for p in c.prods): continue
                                    cid = c.add_cat(cat_name)
                                    price_str = item_data.get("offers", {}).get("price", "0")
                                    price = float(price_str) if price_str else 0.0
                                    if price <= 0: continue
                                    img = item_data.get("image", "")
                                    img_urls = [img] if img else []
                                    desc = item_data.get("description", f"{name} from MUJI {cat_name}")[:500]
                                    c.add_prod(cid, name, desc, price, img_urls,
                                               meta={"brand": "MUJI"}, stock=random.randint(15, 150))
                        except: pass
                except Exception as e:
                    print(f"    {cat_name}: {e}")

    c.save()
    return c


# ======================================================================
# Uniqlo — scrape from uniqlo.com/us/en/
# ======================================================================
UNIQLO_CATEGORIES = [
    ("men", "https://www.uniqlo.com/us/en/men"),
    ("women", "https://www.uniqlo.com/us/en/women"),
    ("kids", "https://www.uniqlo.com/us/en/kids"),
    ("baby", "https://www.uniqlo.com/us/en/baby"),
]


async def scrape_uniqlo():
    print("\n[UNIQLO] Scraping uniqlo.com ...")
    c = DC("uniqlo")
    limits = httpx.Limits(max_keepalive_connections=5, max_connections=10)
    async with httpx.AsyncClient(timeout=30, headers={"User-Agent": UA}, limits=limits, follow_redirects=True) as client:
        # Uniqlo has a product search API
        for cat_name, cat_url in UNIQLO_CATEGORIES:
            if len(c.prods) >= 45: break
            cid = c.add_cat(cat_name.title(), f"{cat_name.title()} clothing from Uniqlo")
            print(f"  {cat_name}: {cat_url}")
            try:
                # Try Uniqlo's search API
                api_url = f"https://www.uniqlo.com/us/api/commerce/v5/en/products/search"
                params = {
                    "category": cat_name,
                    "limit": 40,
                    "offset": 0,
                    "httpErrors": "ignore",
                }
                resp = await client.get(api_url, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    items = data.get("result", {}).get("items", [])
                    print(f"    API: {len(items)} items")
                    for item in items:
                        if len(c.prods) >= 45: break
                        try:
                            name = item.get("name", "").strip()
                            if not name or len(name) < 3: continue
                            price_info = item.get("prices", {}).get("base", {})
                            price = float(price_info.get("value", 0))
                            if price <= 0:
                                price_info = item.get("price", {})
                                price = float(price_info.get("current", {}).get("value", 0))
                            if price <= 0: continue
                            desc = item.get("longDescription", f"{name} by Uniqlo")[:500]
                            img_urls = []
                            for img_key in ["main", "sub", "chip"]:
                                imgs = item.get("images", {}).get(img_key, [])
                                for img in (imgs if isinstance(imgs, list) else [imgs]):
                                    img_url = img.get("image", img.get("url", "")) if isinstance(img, dict) else str(img)
                                    if img_url and img_url.startswith("http"):
                                        img_urls.append(img_url)
                            colors = item.get("styleColors", [])
                            variants = []
                            for clr in colors[:5]:
                                vname = f"{name} - {clr.get('name', '')}"
                                if vname != name:
                                    variants.append({"name": vname, "price": price, "sku": clr.get("code", "")})
                            print(f"      {name[:60]} | ${price} | {len(img_urls)} imgs")
                            c.add_prod(cid, name, desc, price, img_urls if img_urls else [],
                                       meta={"brand": "Uniqlo", "productCode": item.get("productCode", "")},
                                       variants=variants if variants else None,
                                       stock=random.randint(30, 300))
                        except Exception as e:
                            continue
                else:
                    print(f"    API returned {resp.status_code}")
            except Exception as e:
                print(f"    Error: {e}")

    c.save()
    return c


# ======================================================================
# IKEA — scrape from ikea.com/us/en/
# ======================================================================
IKEA_CATEGORIES = [
    ("Living Room", "https://www.ikea.com/us/en/cat/living-room/"),
    ("Bedroom", "https://www.ikea.com/us/en/cat/bedroom/"),
    ("Kitchen", "https://www.ikea.com/us/en/cat/kitchen/"),
    ("Bathroom", "https://www.ikea.com/us/en/cat/bathroom/"),
    ("Office", "https://www.ikea.com/us/en/cat/office/"),
]


async def scrape_ikea():
    print("\n[IKEA] Scraping ikea.com ...")
    c = DC("ikea")
    limits = httpx.Limits(max_keepalive_connections=5, max_connections=10)
    async with httpx.AsyncClient(timeout=30, headers={"User-Agent": UA}, limits=limits, follow_redirects=True) as client:
        # IKEA has a public product API
        for cat_name, cat_url in IKEA_CATEGORIES:
            if len(c.prods) >= 45: break
            cid = c.add_cat(cat_name, f"{cat_name} furniture from IKEA")
            print(f"  {cat_name}")
            try:
                # IKEA API: search by category
                api_url = "https://sik.search.blue.cdtapps.com/us/en/search"
                params = {
                    "c": "us", "l": "en",
                    "q": cat_name.lower(),
                    "size": 30,
                }
                resp = await client.get(api_url, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    # Handle different IKEA API response formats
                    items = []
                    if isinstance(data, dict):
                        items = (data.get("results", []) or
                                 data.get("items", []) or
                                 data.get("products", []) or
                                 data.get("moreProducts", {}).get("productWindow", []))
                    for item in items:
                        if len(c.prods) >= 45: break
                        try:
                            name = item.get("name", "").strip()
                            if not name or len(name) < 3: continue
                            price_val = item.get("priceNumeral") or item.get("salesPrice", {}).get("numeral", 0)
                            price = float(price_val) if price_val else 0.0
                            if price <= 0:
                                price_str = item.get("price", item.get("displayPrice", ""))
                                pm = re.search(r"[\d,.]+", str(price_str).replace(",", ""))
                                if pm: price = float(pm.group())
                            if price <= 0: continue

                            desc = item.get("typeName") or item.get("itemMeasureReferenceText") or f"{name} from IKEA"
                            desc = str(desc)[:500]

                            img_urls = []
                            main_img = item.get("mainImageUrl") or item.get("imageUrl", "")
                            if main_img: img_urls.append(main_img)
                            for alt_img in (item.get("altImages", []) or [])[:4]:
                                if isinstance(alt_img, str): img_urls.append(alt_img)
                                elif isinstance(alt_img, dict):
                                    alt_url = alt_img.get("url", alt_img.get("src", ""))
                                    if alt_url: img_urls.append(alt_url)

                            print(f"    {name[:60]} | ${price}")
                            c.add_prod(cid, name, desc, price, img_urls if img_urls else [],
                                       meta={"brand": "IKEA", "productId": item.get("id", "")},
                                       stock=random.randint(50, 500))
                        except Exception:
                            continue
                else:
                    print(f"    API returned {resp.status_code}")
            except Exception as e:
                print(f"    Error: {e}")

        # If not enough products from API, try HTML scraping
        if len(c.prods) < 20:
            print("  Trying HTML scraping...")
            for cat_name, url in IKEA_CATEGORIES[:2]:
                if len(c.prods) >= 45: break
                try:
                    resp = await client.get(url)
                    if resp.status_code != 200: continue
                    soup = BeautifulSoup(resp.text, "html.parser")
                    for script in soup.find_all("script", type="application/ld+json"):
                        try:
                            ld = json.loads(script.string)
                            if isinstance(ld, list):
                                for item in ld:
                                    if isinstance(item, dict) and item.get("@type") == "Product":
                                        name = item.get("name", "").strip()
                                        if not name or len(name) < 3: continue
                                        if len(c.prods) >= 45: break
                                        if any(p["name"] == name for p in c.prods): continue
                                        cid2 = c.add_cat(cat_name)
                                        price_str = item.get("offers", {}).get("price", "0")
                                        price = float(price_str) if price_str else 0.0
                                        if price <= 0: continue
                                        img_urls = [item.get("image", "")] if item.get("image") else []
                                        desc = item.get("description", f"{name} from IKEA")[:500]
                                        c.add_prod(cid2, name, desc, price, img_urls,
                                                   meta={"brand": "IKEA"}, stock=random.randint(50, 500))
                        except: pass
                except Exception as e:
                    print(f"    HTML {cat_name}: {e}")

    c.save()
    return c


# ======================================================================
# Image download
# ======================================================================
async def download_imgs(collectors):
    print("\n[IMAGES] Downloading...")
    async with httpx.AsyncClient(timeout=30, headers={"User-Agent": UA}) as client:
        ok, fail = 0, 0
        for c in collectors:
            for url, fname in c.img_files:
                fp = IMAGES_DIR / fname
                if fp.exists() and fp.stat().st_size > 1000:
                    ok += 1
                    continue
                try:
                    r = await client.get(url, timeout=30)
                    if r.status_code == 200 and len(r.content) > 1024:
                        fp.write_bytes(r.content); ok += 1
                    else: fail += 1
                except Exception:
                    fail += 1
                if (ok + fail) % 20 == 0:
                    print(f"  {ok} ok, {fail} fail")
        print(f"  Done: {ok} downloaded, {fail} failed")


# ======================================================================
# Main
# ======================================================================
async def main():
    print("=" * 50)
    print("MUJI + UNIQLO + IKEA SCRAPER")
    print("=" * 50)
    collectors = []
    for fn in [scrape_muji, scrape_uniqlo, scrape_ikea]:
        try:
            collectors.append(await fn())
        except Exception as e:
            print(f"FATAL {fn.__name__}: {e}")
            import traceback; traceback.print_exc()

    await download_imgs(collectors)

    print("\nSUMMARY:")
    for c in collectors:
        print(f"  {c.brand}: {len(c.prods)} products, {len(c.cats)} cats, {len(c.imgs)} imgs, {len(c.vars)} vars")
    print("\nRun 'python import_csv_data.py' to import the new data.")


if __name__ == "__main__":
    asyncio.run(main())
