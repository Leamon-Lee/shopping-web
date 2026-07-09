"""Scrape publicly visible Amazon product listings for database seeding.

Searches Amazon for products in each category, extracts name/price/description/image,
and saves the results to amazon_products.json.

Usage:
    python amazon_scraper.py                    # Scrape all categories, 10 products each
    python amazon_scraper.py --max 5            # Scrape 5 products per category
    python amazon_scraper.py --category "Books" # Scrape only one category
    python amazon_scraper.py --domain amazon.cn # Use Amazon China

Environment variables:
    AMAZON_DOMAIN  - Amazon domain to use (default: www.amazon.com)
    HTTP_PROXY     - Proxy URL for requests
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import random
import re
import sys
import time
from pathlib import Path
from typing import Optional

import httpx
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

AMAZON_DOMAIN = os.environ.get("AMAZON_DOMAIN", "www.amazon.com")
AMAZON_BASE = f"https://{AMAZON_DOMAIN}"
OUTPUT_PATH = Path(__file__).parent / "amazon_products.json"
PRODUCTS_PER_CATEGORY = 10
MIN_DELAY = 2.0
MAX_DELAY = 5.0
REQUEST_TIMEOUT = 30.0
MAX_RETRIES = 3

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
]

# Maps our internal category name -> Amazon search query
CATEGORY_SEARCH_QUERIES = {
    "Electronics": "electronics gadgets",
    "Clothing": "clothing fashion men women",
    "Home & Kitchen": "home kitchen essentials",
    "Books": "best selling books",
    "Sports & Outdoors": "sports outdoors equipment",
    "Beauty & Health": "beauty health personal care",
    "Toys & Games": "toys games puzzles",
    "Automotive": "car accessories automotive tools",
    "Groceries": "grocery food snacks beverages",
    "Office Supplies": "office supplies stationery",
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def build_headers() -> dict[str, str]:
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
    }


def parse_price(price_text: str) -> float | None:
    """Extract a numeric price from an Amazon price string like '$29.99' or '1,299.00'."""
    if not price_text:
        return None
    cleaned = price_text.replace("$", "").replace(",", "").strip()
    match = re.search(r"(\d+\.?\d*)", cleaned)
    if match:
        try:
            return round(float(match.group(1)), 2)
        except ValueError:
            return None
    return None


def parse_rating(rating_text: str) -> float | None:
    """Extract numeric rating from '4.5 out of 5 stars'."""
    if not rating_text:
        return None
    match = re.search(r"(\d+\.?\d*)", rating_text)
    if match:
        try:
            return round(float(match.group(1)), 1)
        except ValueError:
            return None
    return None


def build_description(raw_title: str, category: str, price: float | None) -> str:
    """Generate a short product description from available data."""
    title = raw_title.strip()
    if len(title) > 100:
        # Trim very long Amazon titles for use as description
        short = title[:120].rsplit(" ", 1)[0]
        return f"High-quality {category.lower()} item. {short}."
    price_str = f" Priced at ${price:.2f}." if price else ""
    return f"Premium {category.lower()} product.{price_str} {title}."


def clean_title(title: str) -> str:
    """Clean and shorten an Amazon product title for display."""
    title = title.strip()
    if len(title) > 120:
        title = title[:120].rsplit(" ", 1)[0]
    return title


# ---------------------------------------------------------------------------
# Core scraping logic
# ---------------------------------------------------------------------------


async def fetch_page(
    client: httpx.AsyncClient, url: str, retries: int = MAX_RETRIES
) -> str | None:
    """Fetch a page with retry logic and exponential backoff."""
    for attempt in range(retries):
        try:
            headers = build_headers()
            response = await client.get(
                url, headers=headers, timeout=REQUEST_TIMEOUT, follow_redirects=True
            )
            if response.status_code == 200:
                text = response.text
                if _is_blocked(text):
                    print(f"  [!] Request blocked (CAPTCHA/bot detection) for: {url}")
                    return None
                return text
            elif response.status_code == 503:
                wait = (attempt + 1) * 10
                print(f"  [!] 503 Service Unavailable, waiting {wait}s...")
                await asyncio.sleep(wait)
            elif response.status_code == 429:
                wait = (attempt + 1) * 15
                print(f"  [!] 429 Too Many Requests, waiting {wait}s...")
                await asyncio.sleep(wait)
            else:
                print(f"  [!] HTTP {response.status_code} for: {url}")
                if attempt < retries - 1:
                    await asyncio.sleep(5)
        except httpx.TimeoutException:
            print(f"  [!] Timeout (attempt {attempt + 1}/{retries})")
            if attempt < retries - 1:
                await asyncio.sleep(5)
        except Exception as exc:
            print(f"  [!] Error: {exc}")
            if attempt < retries - 1:
                await asyncio.sleep(5)
    return None


def _is_blocked(html: str) -> bool:
    """Check if the response is a CAPTCHA or bot-detection page."""
    lower = html.lower()
    blocked_markers = [
        "captcha",
        "robot check",
        "type the characters you see",
        "to discuss automated access",
        "api-services-support",
        "sorry, we just need to make sure you're not a robot",
    ]
    return any(marker in lower for marker in blocked_markers)


def parse_search_results(html: str) -> list[dict]:
    """Parse Amazon search results page and extract product info."""
    soup = BeautifulSoup(html, "lxml")
    products: list[dict] = []

    # Amazon search result cards
    cards = soup.select('div[data-component-type="s-search-result"]')
    if not cards:
        # Fallback: try alternative selectors
        cards = soup.select(".s-result-item[data-asin]")
    if not cards:
        cards = soup.select(".s-result-item")

    for card in cards:
        asin = card.get("data-asin", "")
        if not asin or asin == "":  # skip non-product rows
            # Some rows have data-asin but are separators; filter by presence of title
            pass

        product = _extract_product_from_card(card, asin)
        if product and product.get("name"):
            products.append(product)

    return products


def _extract_product_from_card(card, asin: str) -> dict | None:
    """Extract product details from a single search result card."""

    # --- Title ---
    title_el = card.select_one("h2 a span") or card.select_one("h2 .a-text-normal")
    if not title_el:
        title_el = card.select_one(".a-size-medium.a-text-normal") or card.select_one(
            ".a-size-base-plus.a-text-normal"
        )
    if not title_el:
        return None
    raw_title = title_el.get_text(strip=True)

    # --- Price ---
    price = None
    price_whole = card.select_one(".a-price-whole")
    price_fraction = card.select_one(".a-price-fraction")
    price_offscreen = card.select_one(".a-price .a-offscreen")
    if price_offscreen:
        price = parse_price(price_offscreen.get_text(strip=True))
    elif price_whole:
        whole = price_whole.get_text(strip=True).replace(",", "")
        frac = price_fraction.get_text(strip=True) if price_fraction else "00"
        try:
            price = round(float(f"{whole}.{frac}"), 2)
        except ValueError:
            price = None

    # --- Image ---
    image_url = ""
    img_el = card.select_one(".s-image")
    if img_el:
        image_url = img_el.get("src", "") or ""

    # --- Rating ---
    rating = None
    rating_el = card.select_one(".a-icon-alt")
    if not rating_el:
        rating_el = card.select_one(".a-icon-star-small ~ .a-icon-alt")
    if rating_el:
        rating = parse_rating(rating_el.get_text(strip=True))

    # --- Reviews count ---
    reviews_count = None
    reviews_el = card.select_one(".a-size-base.s-underline-text")
    if not reviews_el:
        reviews_el = card.select_one('span[aria-label*="stars"] + span')
        if reviews_el:
            reviews_count = parse_rating(reviews_el.get_text(strip=True))
    if reviews_el and reviews_count is None:
        text = reviews_el.get_text(strip=True).replace(",", "")
        match = re.search(r"(\d+)", text)
        if match:
            reviews_count = int(match.group(1))

    # --- Product URL ---
    product_url = ""
    link_el = card.select_one("h2 a") or card.select_one("a.a-link-normal[href*='/dp/']")
    if not link_el:
        link_el = card.select_one(".s-title-instructions-style a") or card.select_one(".a-link-normal.s-line-clamp-2")
    if link_el:
        href = link_el.get("href", "")
        if href and href.startswith("/"):
            product_url = f"{AMAZON_BASE}{href.split('?')[0]}"
        elif href and "amazon" in href:
            product_url = href.split("?")[0]

    return {
        "name": clean_title(raw_title),
        "price": price,
        "image_url": image_url,
        "rating": rating,
        "reviews_count": reviews_count,
        "product_url": product_url,
        "asin": asin,
    }


async def search_category(
    client: httpx.AsyncClient, category: str, max_products: int
) -> list[dict]:
    """Search Amazon for products in a category and return parsed results."""
    query = CATEGORY_SEARCH_QUERIES.get(category, category)
    all_products: list[dict] = []
    seen_asins: set[str] = set()

    for page in range(1, 4):  # up to 3 pages
        if len(all_products) >= max_products:
            break

        url = f"{AMAZON_BASE}/s?k={query.replace(' ', '+')}&page={page}"
        if page > 1:
            await asyncio.sleep(random.uniform(MIN_DELAY, MAX_DELAY))

        print(f"  Fetching page {page}: {url}")
        html = await fetch_page(client, url)
        if html is None:
            print(f"  [!] Failed to fetch page {page} for '{category}', stopping.")
            break

        products = parse_search_results(html)
        new_products = 0
        for p in products:
            asin = p.get("asin", "")
            if asin and asin not in seen_asins:
                seen_asins.add(asin)
                all_products.append(p)
                new_products += 1
                if len(all_products) >= max_products:
                    break

        print(f"    Parsed {len(products)} results, {new_products} new (total: {len(all_products)})")

        if len(products) == 0:
            break

    return all_products[:max_products]


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


async def scrape_all_categories(max_per_category: int, target_categories: list[str] | None = None):
    """Scrape products for all (or selected) categories and save to JSON."""
    categories = target_categories or list(CATEGORY_SEARCH_QUERIES.keys())

    print(f"Target: {AMAZON_BASE}")
    print(f"Categories: {len(categories)}, {max_per_category} products each")
    print(f"Total expected: {len(categories) * max_per_category} products")
    print("-" * 50)

    all_data: dict[str, list[dict]] = {}
    total = 0

    # Configure proxy if set
    proxy = os.environ.get("HTTP_PROXY") or os.environ.get("HTTPS_PROXY") or None

    async with httpx.AsyncClient(
        http2=True,
        proxy=proxy,
        limits=httpx.Limits(max_connections=5),
    ) as client:
        for i, category in enumerate(categories, 1):
            print(f"\n[{i}/{len(categories)}] Searching: {category}")
            products = await search_category(client, category, max_per_category)

            # Fill in descriptions
            for p in products:
                p["description"] = build_description(
                    p["name"], category, p.get("price")
                )

            all_data[category] = products
            total += len(products)
            print(f"  -> Got {len(products)} products for '{category}'")

            # Delay between categories
            if i < len(categories):
                delay = random.uniform(3.0, 6.0)
                print(f"  Sleeping {delay:.1f}s before next category...")
                await asyncio.sleep(delay)

    print(f"\n{'=' * 50}")
    print(f"Done! Scraped {total} products across {len(categories)} categories.")

    # Save to JSON
    output = {
        "metadata": {
            "source": AMAZON_BASE,
            "scraped_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "total_products": total,
            "categories_count": len(categories),
        },
        "categories": {
            cat: {
                "name": cat,
                "description": f"{cat} products from Amazon",
                "products": products,
            }
            for cat, products in all_data.items()
        },
    }

    OUTPUT_PATH.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved to: {OUTPUT_PATH}")

    # Summary
    for cat, products in all_data.items():
        with_prices = [p for p in products if p.get("price")]
        with_images = [p for p in products if p.get("image_url")]
        print(f"  {cat}: {len(products)} products, "
              f"{len(with_prices)} with prices, "
              f"{len(with_images)} with images")


def main():
    parser = argparse.ArgumentParser(description="Scrape Amazon product listings")
    parser.add_argument("--max", type=int, default=PRODUCTS_PER_CATEGORY,
                        help=f"Max products per category (default: {PRODUCTS_PER_CATEGORY})")
    parser.add_argument("--category", type=str, default=None,
                        help="Scrape only a single category")
    parser.add_argument("--domain", type=str, default=None,
                        help="Amazon domain (default: www.amazon.com)")
    args = parser.parse_args()

    if args.domain:
        global AMAZON_BASE, AMAZON_DOMAIN
        AMAZON_DOMAIN = args.domain
        AMAZON_BASE = f"https://{AMAZON_DOMAIN}"

    target = [args.category] if args.category else None

    asyncio.run(scrape_all_categories(args.max, target))


if __name__ == "__main__":
    main()
