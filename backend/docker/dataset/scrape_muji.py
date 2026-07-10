"""
MUJI scraper — Shopify products.json API.
Run: docker exec shopping-backend python docker/dataset/scrape_muji.py
"""
import asyncio, csv, hashlib, json, os, random, re, uuid, sys
from pathlib import Path
sys.path.insert(0, "/app")
import httpx

DATASET_DIR = Path(__file__).parent
IMAGES_DIR = DATASET_DIR / "imgs"
IMAGES_DIR.mkdir(parents=True, exist_ok=True)
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36"
BRAND = "muji"

def slugify(text):
    t = re.sub(r"[^\w\s-]", "", text.lower()).strip()
    return re.sub(r"[\s_]+", "-", t)[:200]

def mk_uuid(seed):
    return str(uuid.UUID(hashlib.sha256(seed.encode()).hexdigest()[:32]))

def mk_hash(content):
    return hashlib.sha256(content.encode()).hexdigest()

cats, prods, imgs, vars_list, img_files = [], [], [], [], []

def add_cat(name, desc=""):
    cid = mk_uuid(f"cat:{BRAND}:{name}")
    if not any(c["id"] == cid for c in cats):
        cats.append({"id": cid, "name": name, "description": desc or f"{name} from MUJI"})
    return cid

def add_prod(cid, name, desc, price, img_urls, stock=100):
    name = name.strip()
    if len(name) < 3 or any(p["name"] == name for p in prods):
        return
    pid = mk_uuid(f"prod:{BRAND}:{name}")
    prods.append({"id": pid, "product_hash": mk_hash(f"{BRAND}:{name}"),
                   "category_id": cid, "name": name, "slug": slugify(f"{BRAND}-{name}"),
                   "description": desc[:500], "price": round(float(price), 2),
                   "available_item_count": stock,
                   "metadata_json": json.dumps({"brand": "MUJI"}, ensure_ascii=False)})
    for rank, u in enumerate(img_urls):
        if not u or not u.strip(): continue
        iid = mk_uuid(f"img:{pid}:{rank}")
        imgs.append({"id": iid, "product_id": pid, "image_url": u, "rank": rank})
        ext = ".jpg"
        if u.split("?")[0].lower().endswith((".png", ".webp", ".gif", ".jpeg")):
            ext = os.path.splitext(u.split("?")[0])[1]
        img_files.append((u, f"{slugify(BRAND)}-{slugify(name)[:40]}-{rank}{ext}"))

def save_csvs():
    for data, fn in [(cats, "product_categories"), (prods, "products"),
                     (imgs, "product_images"), (vars_list, "product_variants")]:
        if not data: continue
        path = DATASET_DIR / f"{BRAND}_{fn}.csv"
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=data[0].keys())
            w.writeheader(); w.writerows(data)
        print(f"  {fn}: {len(data)} rows")


async def main():
    print(f"[{BRAND.upper()}] Scraping muji.us/products.json ...")
    async with httpx.AsyncClient(timeout=30, headers={"User-Agent": UA}, follow_redirects=True) as client:
        page = 1
        while len(prods) < 60 and page <= 10:
            try:
                resp = await client.get(f"https://muji.us/products.json?page={page}&limit=50")
                if resp.status_code != 200:
                    print(f"  Page {page}: HTTP {resp.status_code}")
                    break
                data = resp.json()
                products = data.get("products", [])
                if not products:
                    print(f"  Page {page}: empty, done")
                    break
                print(f"  Page {page}: {len(products)} products")

                for p in products:
                    if len(prods) >= 60: break
                    title = p.get("title", "").strip()
                    if not title or len(title) < 2: continue
                    ptype = p.get("product_type") or "General"
                    cid = add_cat(ptype)

                    # Description
                    desc = title
                    body = p.get("body_html", "")
                    if body:
                        from bs4 import BeautifulSoup
                        desc = BeautifulSoup(body, "html.parser").get_text()[:500]

                    # Price from first variant
                    variants = p.get("variants", [])
                    price = 0.0
                    for v in variants:
                        vprice = float(v.get("price", "0"))
                        if vprice > 0 and (price == 0 or vprice < price):
                            price = vprice
                    if price <= 0: continue

                    # Images
                    img_urls = []
                    for img in p.get("images", []):
                        src = img.get("src", "")
                        if src:
                            if src.startswith("//"): src = "https:" + src
                            if "?" in src: src = src.split("?")[0]
                            img_urls.append(src)

                    print(f"    {title[:55]} | ${price} | {len(img_urls)} imgs | {ptype}")
                    add_prod(cid, title, desc, price, img_urls, stock=random.randint(15, 150))

            except Exception as e:
                print(f"  Page {page} error: {e}")
                break
            page += 1

    save_csvs()

    # Download images
    print(f"\n[IMAGES] Downloading {len(img_files)} files...")
    ok, fail = 0, 0
    async with httpx.AsyncClient(timeout=30, headers={"User-Agent": UA}) as client:
        for url, fname in img_files:
            fp = IMAGES_DIR / fname
            if fp.exists() and fp.stat().st_size > 1000:
                ok += 1; continue
            try:
                r = await client.get(url)
                if r.status_code == 200 and len(r.content) > 1024:
                    fp.write_bytes(r.content); ok += 1
                else: fail += 1
            except: fail += 1
            if (ok + fail) % 20 == 0: print(f"  {ok} ok, {fail} fail")
    print(f"  Done: {ok} downloaded, {fail} failed")
    print(f"\nSUMMARY: {len(prods)} products, {len(cats)} categories, {len(imgs)} images")


if __name__ == "__main__":
    asyncio.run(main())
