#!/usr/bin/env python3
from __future__ import annotations

"""
Export recommendation inputs from PostgreSQL to local JSONL files.

Output layout:
  /tmp/recommendation/events/dt=YYYY-MM-DD/events.jsonl
  /tmp/recommendation/events/dt=YYYY-MM-DD/_SUCCESS
  /tmp/recommendation/events/dt=YYYY-MM-DD/_METADATA.json
  /tmp/recommendation/reviews/dt=YYYY-MM-DD/reviews.jsonl
  /tmp/recommendation/reviews/dt=YYYY-MM-DD/_SUCCESS
  /tmp/recommendation/reviews/dt=YYYY-MM-DD/_METADATA.json
"""

import argparse
import json
import os
import sys
from datetime import date, datetime, timedelta
from typing import Any


EVENT_COLUMNS = [
    "id", "event_type",
    "account_id", "user_email", "anonymous_id", "session_id",
    "product_id", "product_name", "product_slug",
    "shop_id", "shop_name",
    "category_id", "category_name",
    "query", "quantity", "price", "source_page",
    "metadata_json", "created_at",
]

REVIEW_COLUMNS = [
    "review_id", "account_id", "product_id", "rating", "title",
    "content", "created_at", "updated_at",
    "product_name", "product_slug", "price", "category_id",
    "category_name", "shop_id", "shop_name",
]

PRODUCT_COLUMNS = [
    "product_id", "product_name", "product_slug", "price",
    "category_id", "category_name", "shop_id", "shop_name",
    "available_item_count", "created_at", "updated_at",
]


def get_db_url() -> str:
    url = os.getenv("DATABASE_URL", "")
    if url:
        return url

    host = os.getenv("PGHOST", os.getenv("POSTGRES_HOST", "localhost"))
    port = os.getenv("PGPORT", os.getenv("POSTGRES_PORT", "5432"))
    user = os.getenv("PGUSER", os.getenv("POSTGRES_USER", "shopping_user"))
    password = os.getenv("PGPASSWORD", os.getenv("POSTGRES_PASSWORD", "shopping_password"))
    database = os.getenv("PGDATABASE", os.getenv("POSTGRES_DB", "shopping"))
    return f"postgresql://{user}:{password}@{host}:{port}/{database}"


def get_connection():
    try:
        import psycopg2

        conn = psycopg2.connect(get_db_url().replace("postgresql+asyncpg://", "postgresql://"))
        conn.set_session(autocommit=True)
        return conn, "psycopg2"
    except ImportError:
        pass

    try:
        import asyncpg

        return get_db_url().replace("postgresql+asyncpg://", "postgresql://"), "asyncpg"
    except ImportError:
        print("ERROR: psycopg2 or asyncpg required.")
        sys.exit(1)


def fetch_dicts(conn, sql: str, params: dict[str, Any]) -> list[dict[str, Any]]:
    import psycopg2.extras

    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(sql, params)
        return [dict(row) for row in cur.fetchall()]


def fetch_async_dicts(conn, sql: str, *params: Any) -> list[dict[str, Any]]:
    import asyncio
    import asyncpg

    async def _fetch():
        db = await asyncpg.connect(conn)
        try:
            records = await db.fetch(sql, *params)
            return [dict(row) for row in records]
        finally:
            await db.close()

    return asyncio.run(_fetch())


def fetch_events(conn, driver: str, date_str: str, limit: int) -> list[dict[str, Any]]:
    col_str = ", ".join(EVENT_COLUMNS)
    if driver == "psycopg2":
        return fetch_dicts(
            conn,
            f"""
        SELECT {col_str}
        FROM user_behavior_events
        WHERE created_at::date = %(date)s
        ORDER BY created_at
        LIMIT %(limit)s
        """,
            {"date": date_str, "limit": limit},
        )
    return fetch_async_dicts(
        conn,
        f"""
        SELECT {col_str}
        FROM user_behavior_events
        WHERE created_at::date = $1
        ORDER BY created_at
        LIMIT $2
        """,
        date.fromisoformat(date_str),
        limit,
    )


def fetch_reviews(conn, driver: str, date_str: str, limit: int) -> list[dict[str, Any]]:
    psycopg_sql = """
        SELECT
            r.id AS review_id,
            r.account_id,
            r.product_id,
            r.rating,
            r.title,
            r.content,
            r.created_at,
            r.updated_at,
            p.name AS product_name,
            p.slug AS product_slug,
            p.price,
            p.category_id,
            c.name AS category_name,
            s.id AS shop_id,
            s.name AS shop_name
        FROM reviews r
        JOIN products p ON p.id = r.product_id
        LEFT JOIN product_categories c ON c.id = p.category_id
        LEFT JOIN shop_products sp ON sp.product_id = p.id
        LEFT JOIN shops s ON s.id = sp.shop_id
        WHERE r.created_at::date = %(date)s
        ORDER BY r.created_at
        LIMIT %(limit)s
        """
    asyncpg_sql = psycopg_sql.replace("%(date)s", "$1").replace("%(limit)s", "$2")
    if driver == "psycopg2":
        return fetch_dicts(
            conn,
            psycopg_sql,
            {"date": date_str, "limit": limit},
        )
    return fetch_async_dicts(
        conn,
        asyncpg_sql,
        date.fromisoformat(date_str),
        limit,
    )


def fetch_products(conn, driver: str, _date_str: str, limit: int) -> list[dict[str, Any]]:
    psycopg_sql = """
        SELECT DISTINCT ON (p.id)
            p.id AS product_id,
            p.name AS product_name,
            p.slug AS product_slug,
            p.price,
            p.category_id,
            c.name AS category_name,
            s.id AS shop_id,
            s.name AS shop_name,
            p.available_item_count,
            p.created_at,
            p.updated_at
        FROM products p
        LEFT JOIN product_categories c ON c.id = p.category_id
        LEFT JOIN shop_products sp ON sp.product_id = p.id
        LEFT JOIN shops s ON s.id = sp.shop_id
        WHERE p.available_item_count > 0
        ORDER BY p.id, s.name NULLS LAST
        LIMIT %(limit)s
        """
    asyncpg_sql = psycopg_sql.replace("%(limit)s", "$1")
    if driver == "psycopg2":
        return fetch_dicts(
            conn,
            psycopg_sql,
            {"limit": limit},
        )
    return fetch_async_dicts(
        conn,
        asyncpg_sql,
        limit,
    )


def serialize_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def write_partition(
    rows: list[dict[str, Any]],
    output_dir: str,
    kind: str,
    date_str: str,
    filename: str,
    count_key: str,
    columns: list[str],
) -> dict[str, Any]:
    partition_dir = os.path.join(output_dir, kind, f"dt={date_str}")
    os.makedirs(partition_dir, exist_ok=True)

    jsonl_path = os.path.join(partition_dir, filename)
    with open(jsonl_path, "w", encoding="utf-8") as f:
        for row in rows:
            record = {key: serialize_value(value) for key, value in row.items()}
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    with open(os.path.join(partition_dir, "_SUCCESS"), "w", encoding="utf-8") as f:
        f.write("")

    meta = {
        "exported_at": datetime.utcnow().isoformat() + "Z",
        "date": date_str,
        count_key: len(rows),
        "format": "jsonl",
        "columns": columns,
    }
    with open(os.path.join(partition_dir, "_METADATA.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)

    print(f"[export] wrote {len(rows)} {kind} rows to {jsonl_path}")
    return {
        f"{kind}_partition_dir": partition_dir,
        f"{kind}_file": jsonl_path,
        f"{kind}_file_size_bytes": os.path.getsize(jsonl_path),
        count_key: len(rows),
    }


def export(
    date_str: str,
    output_dir: str = "/tmp/recommendation",
    limit: int = 1_000_000,
    format: str = "jsonl",
) -> dict[str, Any]:
    if format != "jsonl":
        raise ValueError("Only jsonl export is supported.")

    print(f"[export] date={date_str} format={format} limit={limit}")
    conn, driver = get_connection()
    try:
        events = fetch_events(conn, driver, date_str, limit)
        reviews = fetch_reviews(conn, driver, date_str, limit)
        products = fetch_products(conn, driver, date_str, limit)
    finally:
        if driver == "psycopg2":
            conn.close()

    result: dict[str, Any] = {"date": date_str}
    result.update(write_partition(
        events, output_dir, "events", date_str, "events.jsonl",
        "event_count", EVENT_COLUMNS,
    ))
    result.update(write_partition(
        reviews, output_dir, "reviews", date_str, "reviews.jsonl",
        "review_count", REVIEW_COLUMNS,
    ))
    result.update(write_partition(
        products, output_dir, "products", date_str, "products.jsonl",
        "product_count", PRODUCT_COLUMNS,
    ))

    result["partition_dir"] = result["events_partition_dir"]
    result["file"] = result["events_file"]
    result["file_size_bytes"] = result["events_file_size_bytes"]
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Export recommendation events and reviews to JSONL for HDFS ingestion"
    )
    parser.add_argument(
        "--date",
        default=(datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d"),
        help="Export date (default: yesterday)",
    )
    parser.add_argument(
        "--output-dir",
        default="/tmp/recommendation",
        help="Base output directory (default: /tmp/recommendation)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=1_000_000,
        help="Max rows per input type to export (default: 1,000,000)",
    )
    parser.add_argument(
        "--format",
        choices=["jsonl"],
        default="jsonl",
        help="Output format",
    )
    args = parser.parse_args()
    result = export(
        date_str=args.date,
        output_dir=args.output_dir,
        limit=args.limit,
        format=args.format,
    )
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
