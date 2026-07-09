"""
Final scraper: Skechers + Under Armour (replaces Nike-only + SVG placeholders).

Output: CSV files for import
"""
import asyncio, csv, hashlib, json, os, random, re, uuid
from pathlib import Path
from urllib.parse import urljoin, urlparse, unquote

import httpx
from playwright.async_api import async_playwright

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
            self.cats.append({"id": cid, "name": name, "slug": slugify(f"{self.brand}-{name}"),
                              "description": desc or f"{name} from {self.brand}"})
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
        if not img_urls:
            img_urls = [""]
        has_real = any(u and u.strip() for u in img_urls)
        for rank, u in enumerate(img_urls):
            if not u or not u.strip():
                if has_real: continue
                u = ""
            iid = mk_uuid(f"img:{pid}:{rank}")
            self.imgs.append({"id": iid, "product_id": pid, "image_url": u, "rank": rank})
            if u:
                ext = ".jpg"
                p = urlparse(u).path.lower()
                if p.endswith((".png", ".webp", ".gif")): ext = os.path.splitext(p)[1]
                self.img_files.append((u, f"{slugify(self.brand)}-{slugify(name)}-{rank}{ext}"))
        if variants:
            for v in variants:
                self.add_var(pid, v["name"], v.get("price", price), v.get("sku", ""), v.get("currency", "usd"))
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
            with open(path, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=data[0].keys())
                w.writeheader(); w.writerows(data)
            print(f"  {fname}: {len(data)} rows")


# ======================================================================
# Skechers (Playwright)
# ======================================================================
SKECHERS_URLS = [
    ("Men's Shoes", "https://www.skechers.com/men/shoes/"),
    ("Women's Shoes", "https://www.skechers.com/women/shoes/"),
]


async def scrape_skechers():
    print("\n[SKECHERS] Playwright scrape ...")
    c = DC("skechers")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        for cat_name, url in SKECHERS_URLS:
            if len(c.prods) >= 45: break
            cid = c.add_cat(cat_name)
            print(f"  {cat_name}: {url}")
            try:
                page = await browser.new_page()
                await page.goto(url, timeout=30000, wait_until="domcontentloaded")
                await page.wait_for_timeout(5000)
                for _ in range(4):
                    await page.evaluate("window.scrollBy(0, window.innerHeight)")
                    await page.wait_for_timeout(1500)

                cards = await page.query_selector_all("[class*=product-card]")
                print(f"    Found {len(cards)} product cards")

                for card in cards:
                    if len(c.prods) >= 45: break
                    try:
                        name_el = await card.query_selector("[class*=name], [class*=title], h3, h4")
                        price_el = await card.query_selector("[class*=price]")
                        img_el = await card.query_selector("img")

                        name = (await name_el.text_content() if name_el else "").strip()
                        price_text = (await price_el.text_content() if price_el else "$0").strip()
                        img_url = (await img_el.get_attribute("src") if img_el else "")

                        if not name or len(name) < 4: continue

                        # Parse price
                        price = 0.0
                        pm = re.search(r"[\d,]+\.?\d*", price_text.replace(",", ""))
                        if pm: price = float(pm.group())

                        if price <= 0: continue

                        # Keep original image URL, just decode %2C back to ,
                        img_url = re.sub(r"%2C", ",", img_url)

                        # Get description from product card text
                        all_text = (await card.text_content()).strip()
                        desc = name
                        if len(all_text) > len(name) + 10:
                            desc = all_text[:300].replace("\n", " ")

                        print(f"      {name[:60]} | ${price}")

                        c.add_prod(cid, name, desc, price, [img_url],
                                   meta={"brand": "Skechers"},
                                   stock=random.randint(20, 400))
                    except Exception as e:
                        continue

                await page.close()
            except Exception as e:
                print(f"    Error: {e}")

        await browser.close()
    c.save()
    return c


# ======================================================================
# Under Armour (Constructor.io API)
# ======================================================================
UA_CATS = {"men-footwear": "Men's Footwear", "women-footwear": "Women's Footwear"}


async def scrape_ua():
    print("\n[UNDER ARMOUR] Constructor.io API ...")
    c = DC("underarmour")
    async with httpx.AsyncClient(timeout=30, headers={"User-Agent": UA}) as client:
        for gid, cat_name in UA_CATS.items():
            if len(c.prods) >= 45: break
            cid = c.add_cat(cat_name)
            print(f"  {cat_name}")
            try:
                params = {"c": "ciojs-client-2.65.0", "key": "key_Gz4VzKsXbR7b7fSh",
                          "num_results_per_page": "30", "page": "1",
                          "fmt_options[groups_max_depth]": "2", "fmt_options[hidden_fields]": "test_cells"}
                resp = await client.get(f"https://ac.cnstrc.com/browse/group_id/{gid}", params=params)
                if resp.status_code != 200: continue
                data = resp.json()
                results = data.get("response", {}).get("results", [])
                print(f"    {len(results)} results")

                for item in results:
                    if len(c.prods) >= 45: break
                    try:
                        d = item.get("data", {})
                        url_p = d.get("url", "")
                        slug = unquote(url_p.strip("/").split("/")[1].replace(".html", ""))
                        name = slug.replace("_", " ").replace("+", " ").title()
                        name = re.sub(r"\s+", " ", name).strip()
                        if len(name) < 5: continue
                        if any(p["name"] == name for p in c.prods): continue

                        price = d.get("salePriceLow") or d.get("listPriceLow") or 0
                        if not price: continue

                        desc = d.get("description", f"{name} by Under Armour.")
                        desc = re.sub(r"<[^>]+>", "", desc)[:500]

                        img_url = d.get("image_url", "")
                        color = d.get("colorValue", "")
                        variants = [{"name": f"{name} - {color}", "price": price,
                                      "sku": d.get("sku", d.get("id", "")), "currency": "usd"}] if color else None

                        c.add_prod(cid, name, desc, float(price), [img_url] if img_url else [],
                                   meta={"brand": "Under Armour", "subHeader": d.get("subHeader", "")},
                                   variants=variants, stock=random.randint(20, 400))
                        print(f"      {name[:60]} | ${price}")
                    except Exception as e:
                        continue
            except Exception as e:
                print(f"    Error: {e}")
    c.save()
    return c


async def download_imgs(collectors):
    print("\n[IMAGES]")
    async with httpx.AsyncClient(timeout=30, headers={"User-Agent": UA}) as client:
        ok, fail = 0, 0
        for c in collectors:
            for url, fname in c.img_files:
                fp = IMAGES_DIR / fname
                if fp.exists(): continue
                try:
                    r = await client.get(url, timeout=30)
                    if r.status_code == 200 and len(r.content) > 1024:
                        fp.write_bytes(r.content); ok += 1
                    else: fail += 1
                except: fail += 1
                if (ok + fail) % 20 == 0: print(f"  {ok} ok, {fail} fail")
        print(f"  Done: {ok} downloaded, {fail} failed")


async def main():
    print("=" * 50)
    print("FINAL SCRAPER: Skechers + Under Armour")
    print("=" * 50)
    collectors = []
    for fn in [scrape_skechers, scrape_ua]:
        try:
            collectors.append(await fn())
        except Exception as e:
            print(f"FATAL {fn.__name__}: {e}")
            import traceback; traceback.print_exc()
    await download_imgs(collectors)
    print("\nSUMMARY:")
    for c in collectors:
        print(f"  {c.brand}: {len(c.prods)} products, {len(c.cats)} cats, {len(c.imgs)} imgs, {len(c.vars)} vars")


if __name__ == "__main__":
    asyncio.run(main())
