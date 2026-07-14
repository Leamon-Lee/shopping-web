#!/usr/bin/env python3
from __future__ import annotations

"""
Import Spark recommendation outputs into PostgreSQL.

Reads JSONL files from local or HDFS output directories,
upserts into recommendation_results, item_similarities, popular_products.

Usage:
  # Import all recommendation types for a date
  python scripts/import_recommendations.py --date 2026-07-13

  # Import from a specific directory
  python scripts/import_recommendations.py --date 2026-07-13 \
      --input-dir /tmp/recommendation

  # Dry run
  python scripts/import_recommendations.py --date 2026-07-13 --dry-run
"""

import argparse
import glob
import json
import os
import re
import sys
from datetime import datetime


UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)


def get_connection():
    try:
        import psycopg2
        import psycopg2.extras

        url = os.getenv(
            "DATABASE_URL",
            "postgresql://shopping_user:shopping_password@localhost:5432/shopping",
        )
        conn = psycopg2.connect(url)
        conn.autocommit = True
        return conn
    except ImportError:
        print("ERROR: psycopg2 required. pip install psycopg2-binary")
        sys.exit(1)


def load_jsonl(path: str) -> list[dict]:
    if not os.path.exists(path):
        directory = os.path.dirname(path)
        candidates = sorted(
            glob.glob(os.path.join(directory, "part-*.json"))
            + glob.glob(os.path.join(directory, "part-*.jsonl"))
        )
        if not candidates:
            print(f"  [SKIP] File not found: {path}")
            return []
        paths = candidates
    else:
        paths = [path]
    rows = []
    for candidate in paths:
        with open(candidate, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        rows.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
    return rows


def normalize_key(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return text.lower()


def is_uuid(value: object) -> bool:
    return bool(value and UUID_RE.match(str(value).strip()))


def load_product_lookup(conn) -> dict[str, str]:
    """Build a forgiving product lookup for UUID, slug, and display-name inputs."""
    cur = conn.cursor()
    cur.execute("SELECT id::text, name, slug FROM products WHERE available_item_count > 0")
    lookup: dict[str, str] = {}
    for product_id, name, slug in cur.fetchall():
        for raw in (product_id, name, slug):
            key = normalize_key(raw)
            if key:
                lookup[key] = product_id
    return lookup


def resolve_product_id(
    lookup: dict[str, str],
    *candidates: object,
) -> str | None:
    for candidate in candidates:
        if not candidate:
            continue
        text = str(candidate).strip()
        if is_uuid(text):
            return text
        key = normalize_key(text)
        if key and key in lookup:
            return lookup[key]
    return None


def import_popular(conn, rows: list[dict], date_str: str, dry_run: bool, lookup: dict[str, str]):
    """Upsert popular_products."""
    if not rows:
        print("[popular] no rows to import")
        return

    if dry_run:
        resolvable = sum(
            1 for r in rows
            if resolve_product_id(lookup, r.get("product_id"), r.get("product_slug"), r.get("product_name"))
        )
        print(f"[popular] DRY-RUN: would upsert {resolvable}/{len(rows)} resolvable rows")
        for r in rows[:3]:
            print(f"  rank={r.get('rank')} {r.get('product_name','?')} score={r.get('score')}")
        return

    cur = conn.cursor()
    # Clear old data for this date (simple replace strategy)
    cur.execute(
        "DELETE FROM popular_products WHERE generated_at::date = %s",
        (date_str,),
    )

    inserted = 0
    skipped = 0
    for row in rows:
        product_id = resolve_product_id(
            lookup,
            row.get("product_id"),
            row.get("product_slug"),
            row.get("product_name"),
        )
        if not product_id:
            skipped += 1
            continue
        cur.execute(
            """INSERT INTO popular_products (product_id, score, rank, scene, generated_at)
               VALUES (%s, %s, %s, %s, %s)
               ON CONFLICT DO NOTHING""",
            (product_id, row.get("score", 0), row.get("rank", 0), row.get("scene", "home"), date_str),
        )
        inserted += 1

    print(f"[popular] upserted {inserted} rows for {date_str}; skipped {skipped} unresolved rows")


def import_item_sim(conn, rows: list[dict], date_str: str, dry_run: bool, lookup: dict[str, str]):
    """Upsert item_similarities."""
    if not rows:
        print("[item_sim] no rows to import")
        return

    if dry_run:
        resolvable = sum(
            1 for r in rows
            if resolve_product_id(lookup, r.get("product_id"), r.get("product_slug"), r.get("product_name"))
            and resolve_product_id(lookup, r.get("similar_product_id"), r.get("similar_product_slug"), r.get("similar_product_name"))
        )
        print(f"[item_sim] DRY-RUN: would upsert {resolvable}/{len(rows)} resolvable rows")
        for r in rows[:3]:
            print(f"  {r.get('product_name','?')} -> {r.get('similar_product_name','?')} score={r.get('score')}")
        return

    cur = conn.cursor()
    cur.execute("DELETE FROM item_similarities WHERE generated_at::date = %s", (date_str,))

    inserted = 0
    skipped = 0
    for row in rows:
        pid = resolve_product_id(
            lookup,
            row.get("product_id"),
            row.get("product_slug"),
            row.get("product_name"),
        )
        sid = resolve_product_id(
            lookup,
            row.get("similar_product_id"),
            row.get("similar_product_slug"),
            row.get("similar_product_name"),
        )
        if not pid or not sid:
            skipped += 1
            continue
        if pid == sid:
            skipped += 1
            continue
        try:
            cur.execute(
                """INSERT INTO item_similarities (product_id, similar_product_id, score, reason, algorithm, generated_at)
                   VALUES (%s, %s, %s, %s, %s, %s)
                   ON CONFLICT DO NOTHING""",
                (pid, sid, row.get("score", 0), row.get("reason", ""), "itemcf_v1", date_str),
            )
            inserted += 1
        except Exception as exc:
            skipped += 1
            print(f"  [item_sim] skipped row: {exc}")

    print(f"[item_sim] upserted {inserted} rows for {date_str}; skipped {skipped} unresolved/invalid rows")


def import_user_recs(conn, rows: list[dict], date_str: str, dry_run: bool, lookup: dict[str, str]):
    """Import per-user recommendation results."""
    if not rows:
        print("[user_recs] no rows to import")
        return

    if dry_run:
        resolvable = 0
        total = 0
        for row in rows:
            for prod in row.get("top_products", [])[:10]:
                total += 1
                if resolve_product_id(lookup, prod.get("id"), prod.get("product_id"), prod.get("slug"), prod.get("name")):
                    resolvable += 1
        print(f"[user_recs] DRY-RUN: would upsert {resolvable * 3}/{total * 3} scene rows")
        return

    cur = conn.cursor()
    cur.execute(
        "DELETE FROM recommendation_results WHERE generated_at::date = %s",
        (date_str,),
    )

    inserted = 0
    skipped = 0
    for row in rows:
        user_key = row.get("user_key")
        if not user_key:
            skipped += 1
            continue
        for scene in ["home", "product_detail", "cart"]:
            # For user preferences, we emit top products across scenes
            for rank, prod in enumerate(row.get("top_products", [])[:10], start=1):
                pid = resolve_product_id(
                    lookup,
                    prod.get("id"),
                    prod.get("product_id"),
                    prod.get("slug"),
                    prod.get("name"),
                )
                if not pid:
                    skipped += 1
                    continue
                try:
                    cur.execute(
                        """INSERT INTO recommendation_results
                           (user_key, scene, product_id, score, rank, reason, algorithm, generated_at)
                           VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
                        (user_key, scene, pid, prod.get("score", 0), rank,
                         prod.get("reason") or f"Based on your {row.get('top_categories',[{}])[0].get('name','') if row.get('top_categories') else 'interests'}",
                         prod.get("algorithm") or "hadoop_commerce_v1", date_str),
                    )
                    inserted += 1
                except Exception as exc:
                    skipped += 1
                    print(f"  [user_recs] skipped row: {exc}")

    print(f"[user_recs] upserted {inserted} rows for {date_str}; skipped {skipped} unresolved/invalid rows")


def main():
    parser = argparse.ArgumentParser(description="Import recommendations into PostgreSQL")
    parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"))
    parser.add_argument("--input-dir", default="/tmp/recommendation")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--types", default="popular,similar,user_recs",
                        help="Comma-separated: popular,similar,user_recs")
    args = parser.parse_args()

    conn = get_connection()
    product_lookup = load_product_lookup(conn)
    types = [t.strip() for t in args.types.split(",")]
    print(f"Importing recommendations for {args.date}  types={types}")
    print(f"Loaded {len(product_lookup)} product lookup keys")

    base = args.input_dir

    if "popular" in types:
        path = os.path.join(base, "recommendations", "popular_products", f"dt={args.date}", "part-00000.jsonl")
        rows = load_jsonl(path)
        import_popular(conn, rows, args.date, args.dry_run, product_lookup)

    if "similar" in types:
        path = os.path.join(base, "recommendations", "item_similar", f"dt={args.date}", "part-00000.jsonl")
        rows = load_jsonl(path)
        import_item_sim(conn, rows, args.date, args.dry_run, product_lookup)

    if "user_recs" in types:
        path = os.path.join(base, "recommendations", "user_recommendations", f"dt={args.date}", "part-00000.jsonl")
        rows = load_jsonl(path)
        if not rows:
            legacy_path = os.path.join(base, "features", "user_preferences", f"dt={args.date}", "part-00000.jsonl")
            rows = load_jsonl(legacy_path)
        import_user_recs(conn, rows, args.date, args.dry_run, product_lookup)

    conn.close()
    print("Import complete.")


if __name__ == "__main__":
    main()
