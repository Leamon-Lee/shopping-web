"""Seed products into the database from Amazon scraped data or hardcoded fallback.

Usage:
    python seed_products.py                     # Use amazon_products.json if available, else hardcoded
    python seed_products.py --source hardcoded  # Force hardcoded data
    python seed_products.py --source amazon     # Force Amazon data (fails if file missing)
"""
import argparse
import asyncio
import hashlib
import json
import random
import re
import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import select
from online_shopping.database import async_session
from online_shopping.models.category import ProductCategory
from online_shopping.models.product import Product
from online_shopping.models.product_image import ProductImage

# ---------------------------------------------------------------------------
# Hardcoded fallback data
# ---------------------------------------------------------------------------

CATEGORIES = [
    ("Electronics", "Electronic devices and accessories"),
    ("Clothing", "Men's and women's apparel"),
    ("Home & Kitchen", "Home decor and kitchen essentials"),
    ("Books", "Fiction, non-fiction, and educational books"),
    ("Sports & Outdoors", "Sports equipment and outdoor gear"),
    ("Beauty & Health", "Beauty products and health supplements"),
    ("Toys & Games", "Toys, board games, and puzzles"),
    ("Automotive", "Car accessories and tools"),
    ("Groceries", "Food and beverage products"),
    ("Office Supplies", "Stationery and office equipment"),
]

PRODUCTS_BY_CATEGORY = {
    "Electronics": [
        ("Wireless Bluetooth Headphones", "Noise-cancelling over-ear headphones with 30hr battery life", 299),
        ("USB-C Charging Cable 2m", "Braided fast-charging cable for all USB-C devices", 19.9),
        ("Portable Power Bank 20000mAh", "High-capacity power bank with dual USB output", 159),
        ("Bluetooth Speaker Mini", "Compact waterproof speaker with rich bass", 89),
        ("Wireless Mouse", "Ergonomic 2.4GHz wireless mouse with 6 buttons", 49),
        ("27-inch 4K Monitor", "IPS panel with HDR support and USB-C connectivity", 2499),
        ("Mechanical Keyboard", "RGB backlit mechanical keyboard with Cherry MX switches", 399),
        ("Webcam 1080p", "Full HD webcam with built-in microphone and auto-focus", 199),
        ("Smartphone Stand", "Adjustable aluminum stand for desk and bedside", 39),
        ("Laptop Sleeve 15.6 inch", "Water-resistant neoprene sleeve with extra pocket", 69),
    ],
    "Clothing": [
        ("Cotton T-Shirt Classic Fit", "100% organic cotton tee, available in 8 colors", 79),
        ("Slim Fit Jeans", "Stretch denim jeans with modern slim cut", 199),
        ("Wool Blend Sweater", "Warm crew-neck sweater for cold weather", 299),
        ("Running Shorts", "Lightweight quick-dry shorts with zipper pocket", 119),
        ("Winter Down Jacket", "800-fill goose down jacket, windproof and waterproof", 899),
        ("Linen Button-Down Shirt", "Breathable linen shirt perfect for summer", 169),
        ("Athletic Leggings", "High-waist compression leggings with side pocket", 149),
        ("Leather Belt", "Genuine leather belt with brushed metal buckle", 89),
        ("Cashmere Scarf", "Soft cashmere scarf in assorted colors", 259),
        ("Rain Jacket", "Packable waterproof jacket with hood", 349),
    ],
    "Home & Kitchen": [
        ("Stainless Steel French Press", "Double-wall insulated 1L coffee press", 129),
        ("Non-Stick Frying Pan 28cm", "Ceramic-coated pan suitable for all stovetops", 159),
        ("Bamboo Cutting Board Set", "Set of 3 organic bamboo cutting boards", 69),
        ("Scented Candle Collection", "Set of 4 soy wax candles, 40hr burn each", 99),
        ("Memory Foam Pillow", "Ergonomic contour pillow with cooling gel layer", 139),
        ("Robot Vacuum Cleaner", "Smart mapping robot vacuum with 2500Pa suction", 1499),
        ("Kitchen Knife Set 7-Piece", "Professional stainless steel knife block set", 399),
        ("Table Lamp with Dimmable LED", "Modern bedside lamp with USB charging port", 179),
        ("Food Storage Containers 12-Pack", "BPA-free stackable containers with locking lids", 89),
        ("Cotton Bath Towel Set", "Set of 6 ultra-soft 600GSM towels", 199),
    ],
    "Books": [
        ("Python Programming Fundamentals", "Comprehensive guide for beginners to Python 3", 59),
        ("The Art of Clean Code", "Practical techniques for writing maintainable software", 49),
        ("Data Structures and Algorithms", "Essential CS concepts with Python examples", 69),
        ("Machine Learning Basics", "Introduction to ML with scikit-learn and TensorFlow", 79),
        ("Modern Web Development", "Full-stack development with React and FastAPI", 65),
        ("Database Design Patterns", "Best practices for SQL and NoSQL database design", 55),
        ("Cloud Native Architecture", "Building scalable systems on AWS and GCP", 72),
        ("Cybersecurity Essentials", "Network security fundamentals for IT professionals", 68),
        ("The Startup Handbook", "From idea to IPO: a practical guide for founders", 45),
        ("Photography Masterclass", "Professional techniques for digital photography", 88),
    ],
    "Sports & Outdoors": [
        ("Yoga Mat Premium", "6mm thick non-slip TPE mat with carrying strap", 89),
        ("Resistance Bands Set", "5 levels of resistance bands with door anchor", 49),
        ("Camping Tent 2-Person", "Waterproof double-layer tent with vestibule", 459),
        ("Stainless Steel Water Bottle", "750ml vacuum insulated bottle, 24hr cold / 12hr hot", 109),
        ("Folding Camping Chair", "Lightweight aluminum chair with cup holder", 139),
        ("Trekking Poles Pair", "Adjustable carbon fiber poles with cork grip", 199),
        ("Jump Rope Speed Cable", "Adjustable steel cable with ball bearings", 29),
        ("Hiking Backpack 40L", "Waterproof daypack with hydration compartment", 299),
        ("Cycling Gloves", "Gel-padded fingerless gloves for road cycling", 59),
        ("Fishing Rod Combo", "Spinning rod and reel combo for beginners", 169),
    ],
    "Beauty & Health": [
        ("Vitamin C Serum 30ml", "20% vitamin C with hyaluronic acid and vitamin E", 79),
        ("Electric Toothbrush Sonic", "5 cleaning modes with 2-minute smart timer", 199),
        ("Facial Moisturizer SPF30", "Daily hydrating moisturizer with sun protection", 89),
        ("Hair Dryer Ionic", "Professional 2000W dryer with 3 heat settings", 249),
        ("Essential Oils Kit", "Set of 8 pure essential oils for aromatherapy", 119),
        ("Collagen Protein Powder", "500g hydrolyzed collagen peptides, unflavored", 139),
        ("Beard Grooming Kit", "Complete kit with oil, balm, brush, and scissors", 99),
        ("Sunscreen Spray SPF50", "Water-resistant broad spectrum sunscreen", 69),
        ("Nail Polish Set 12 Colors", "Quick-dry non-toxic nail polish collection", 49),
        ("Digital Bathroom Scale", "Smart scale with body fat and BMI measurement", 159),
    ],
    "Toys & Games": [
        ("Building Blocks 500-Piece", "Classic interlocking brick set with storage box", 99),
        ("Board Game Collection", "5 classic board games in one box", 129),
        ("RC Stunt Car", "4WD remote control car with 360-degree rotation", 179),
        ("Jigsaw Puzzle 1000-Piece", "Scenic landscape puzzle with poster guide", 49),
        ("Science Experiment Kit", "50 STEM experiments for kids aged 8-14", 159),
        ("Plush Bear Giant", "120cm soft plush teddy bear", 139),
        ("Magic Tricks Set", "Professional magic kit with 75 tricks and instructions", 109),
        ("Card Game Deck Premium", "Waterproof playing cards with custom artwork", 29),
        ("Musical Instrument Set", "6-piece percussion set for toddlers", 89),
        ("Drawing Tablet Kids", "LCD writing tablet, 10-inch color screen", 79),
    ],
    "Automotive": [
        ("Dash Cam 4K", "Ultra HD dash camera with night vision and GPS", 399),
        ("Car Phone Mount", "Magnetic dashboard mount for all smartphones", 49),
        ("Tire Inflator Portable", "12V digital air compressor with auto shut-off", 119),
        ("Car Vacuum Cleaner", "Handheld 8000Pa cordless vacuum for cars", 169),
        ("LED Headlight Bulbs Pair", "Super bright H7 LED bulbs, 6000K white", 99),
        ("Car Cover Waterproof", "All-season UV-protective full car cover", 199),
        ("Jump Starter 1500A", "Portable lithium battery jump starter with USB", 299),
        ("Bluetooth FM Transmitter", "Wireless audio adapter with dual USB charging", 59),
        ("Seat Cushion Memory Foam", "Ergonomic cushion for office chair and car seat", 79),
        ("Car Wax Kit", "Professional car detailing wax with applicator pads", 89),
    ],
    "Groceries": [
        ("Organic Green Tea 100 Bags", "Premium Japanese sencha green tea", 39),
        ("Trail Mix Assortment", "1.5kg mixed nuts, dried fruits, and seeds", 89),
        ("Dark Chocolate Collection", "12-bar assorted 70% cocoa chocolate gift box", 119),
        ("Instant Coffee Premium", "Freeze-dried Arabica instant coffee 200g", 69),
        ("Olive Oil Extra Virgin 1L", "Cold-pressed Italian extra virgin olive oil", 99),
        ("Protein Snack Bars 24-Pack", "Mixed flavor protein bars, 20g protein each", 79),
        ("Organic Honey 500g", "Raw unfiltered wildflower honey", 59),
        ("Ramen Noodle Variety Pack", "Assorted 12-pack Japanese instant ramen", 49),
        ("Dried Mango Slices 1kg", "Natural dried mango, no added sugar", 69),
        ("Spice Rack 20 Jars", "Complete cooking spice set with labeled jars", 149),
    ],
    "Office Supplies": [
        ("Ballpoint Pen Set 24-Pack", "Smooth-writing medium point pens in assorted colors", 29),
        ("Leather Notebook A5", "Hardcover 200-page dotted journal with pen loop", 79),
        ("Standing Desk Converter", "Adjustable height sit-stand desk riser 36 inch", 599),
        ("Wireless Presenter Remote", "2.4GHz presentation clicker with laser pointer", 89),
        ("Desk Organizer 5-Tier", "Metal mesh desktop document tray system", 119),
        ("Whiteboard Magnetic 90x60cm", "Wall-mounted dry-erase board with marker set", 149),
        ("Sticky Notes Bulk Pack", "24 pads assorted colors, 100 sheets each", 35),
        ("Shredder Cross-Cut", "10-sheet micro-cut paper shredder for home office", 259),
        ("Monitor Stand Riser", "Wooden monitor stand with storage drawer", 99),
        ("Label Maker", "Portable Bluetooth label printer with app control", 199),
    ],
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def make_hash(name: str, cat: str) -> str:
    payload = f"{name.strip().lower()}::{cat.strip().lower()}"
    return hashlib.sha256(payload.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_amazon_data() -> dict | None:
    """Load product data from amazon_products.json if it exists and is valid."""
    json_path = Path(__file__).parent / "amazon_products.json"
    if not json_path.exists():
        print(f"Amazon data file not found: {json_path}")
        return None

    try:
        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"Failed to parse amazon_products.json: {e}")
        return None

    categories_data = data.get("categories")
    if not categories_data:
        print("amazon_products.json has no categories data.")
        return None

    # Convert to the format expected by seed(): {category_name: [(name, desc, price, image_url), ...]}
    result: dict[str, list[tuple]] = {}
    for cat_name, cat_info in categories_data.items():
        products = cat_info.get("products", [])
        if not products:
            continue
        items: list[tuple] = []
        for p in products:
            name = p.get("name", "")
            desc = p.get("description", f"{cat_name} product")
            price = p.get("price")
            image_url = p.get("image_url", "")
            # Ensure price is always positive (DB constraint: price > 0)
            if price is None or price <= 0:
                price = round(random.uniform(9.99, 299.99), 2)
            if not name:
                continue
            items.append((name, desc, float(price), image_url))
        if items:
            result[cat_name] = items

    metadata = data.get("metadata", {})
    total = metadata.get("total_products", sum(len(v) for v in result.values()))
    source = metadata.get("source", "unknown")
    print(f"Loaded {total} products from Amazon data ({source}).")
    return result if result else None


def load_hardcoded_data() -> dict[str, list[tuple]]:
    """Convert hardcoded product data to the unified format."""
    result: dict[str, list[tuple]] = {}
    for cat_name, products in PRODUCTS_BY_CATEGORY.items():
        result[cat_name] = [(name, desc, float(price), "") for name, desc, price in products]
    return result


# ---------------------------------------------------------------------------
# Seed logic
# ---------------------------------------------------------------------------

async def seed(products_data: dict[str, list[tuple]]):
    """Seed the database with the given product data.

    products_data format: {category_name: [(name, description, price, image_url), ...]}
    """
    async with async_session() as db:
        # Clear existing data (order matters for FK constraints)
        from online_shopping.models.product_variant import ProductVariant
        await db.execute(ProductImage.__table__.delete())
        await db.execute(ProductVariant.__table__.delete())
        await db.execute(Product.__table__.delete())
        await db.execute(ProductCategory.__table__.delete())
        await db.flush()
        print("Cleared existing products.")

        # Insert categories
        categories = {}
        for cat_name in products_data:
            cat_desc = f"{cat_name} products"
            for c_name, c_desc in CATEGORIES:
                if c_name == cat_name:
                    cat_desc = c_desc
                    break
            cat = ProductCategory(name=cat_name, description=cat_desc)
            db.add(cat)
            await db.flush()
            categories[cat_name] = cat

        # Insert products with duplicate detection
        seen_hashes: set[str] = set()
        seen_slugs: set[str] = set()
        count = 0
        for cat_name, products in products_data.items():
            category = categories[cat_name]
            for item in products:
                name = item[0]
                desc = item[1]
                price = item[2]
                image_url = item[3] if len(item) > 3 else ""

                slug = slugify(name)
                product_hash = make_hash(name, cat_name)

                # Deduplicate: if hash or slug exists, append suffix
                suffix = 1
                original_name = name
                while product_hash in seen_hashes or slug in seen_slugs:
                    suffix += 1
                    name = f"{original_name} #{suffix}"
                    slug = slugify(name)
                    product_hash = make_hash(name, cat_name)
                seen_hashes.add(product_hash)
                seen_slugs.add(slug)
                product = Product(
                    product_hash=product_hash,
                    category_id=category.id,
                    name=name,
                    slug=slug,
                    description=desc,
                    price=price,
                    available_item_count=random.randint(5, 100),
                )
                db.add(product)
                await db.flush()

                # Generate image URLs
                if image_url:
                    # Use the Amazon image as primary, add fallback picsum images
                    db.add(ProductImage(
                        product_id=product.id,
                        image_url=image_url,
                        rank=0,
                    ))
                    for rank in range(1, random.randint(1, 3)):
                        img_seed = f"{product_hash}{rank}"
                        fb_url = f"https://picsum.photos/seed/{img_seed}/400/400"
                        db.add(ProductImage(
                            product_id=product.id,
                            image_url=fb_url,
                            rank=rank,
                        ))
                else:
                    for rank in range(random.randint(1, 4)):
                        img_seed = f"{product_hash}{rank}"
                        fb_url = f"https://picsum.photos/seed/{img_seed}/400/400"
                        db.add(ProductImage(
                            product_id=product.id,
                            image_url=fb_url,
                            rank=rank,
                        ))
                count += 1

        await db.commit()
        print(f"Seeded {count} products across {len(products_data)} categories.")


def main():
    parser = argparse.ArgumentParser(description="Seed product data into the database")
    parser.add_argument(
        "--source",
        choices=["auto", "amazon", "hardcoded"],
        default="auto",
        help="Data source: auto (try Amazon JSON first), amazon, or hardcoded",
    )
    args = parser.parse_args()

    products_data = None

    if args.source in ("auto", "amazon"):
        products_data = load_amazon_data()

    if products_data is None:
        if args.source == "amazon":
            print("ERROR: amazon_products.json not found. Run amazon_scraper.py first.")
            sys.exit(1)
        print("Falling back to hardcoded product data.")
        products_data = load_hardcoded_data()

    asyncio.run(seed(products_data))


if __name__ == "__main__":
    main()
