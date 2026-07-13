#!/usr/bin/env python3
"""
Export user_behavior_events from PostgreSQL to local JSONL files.

Designed to run:
  - Inside the shopping-backend container (which has psycopg2 installed
    or can reach PostgreSQL via DATABASE_URL)
  - On the Docker host (with a port-forwarded PostgreSQL)

Output layout:
  /tmp/recommendation/events/dt=YYYY-MM-DD/events.jsonl
  /tmp/recommendation/events/dt=YYYY-MM-DD/_SUCCESS
  /tmp/recommendation/events/dt=YYYY-MM-DD/_METADATA.json

Usage:
  python scripts/export_recommendation_events.py --date 2026-07-13

Then upload to HDFS:
  docker exec master hdfs dfs -mkdir -p /data/raw/events/dt=2026-07-13
  docker exec -i master hdfs dfs -put /tmp/recommendation/events/dt=2026-07-13/events.jsonl /data/raw/events/dt=2026-07-13/

  Or use the convenience wrapper:
  bash scripts/hdfs_upload.sh 2026-07-13

TODO:
  - Add Parquet support (pyarrow/pandas) for columnar compression
  - Add incremental export mode (only new events since last run)
  - Add partition-aware table creation in Hive metastore
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from typing import Any


# ── PostgreSQL connection (works in Docker and on host) ──────────

def get_db_url() -> str:
    """Resolve DATABASE_URL from environment, with Docker/host fallback."""
    url = os.getenv("DATABASE_URL", "")
    if url:
        return url

    # Fallback: construct from individual env vars
    host = os.getenv("PGHOST", os.getenv("POSTGRES_HOST", "localhost"))
    port = os.getenv("PGPORT", os.getenv("POSTGRES_PORT", "5432"))
    user = os.getenv("PGUSER", os.getenv("POSTGRES_USER", "shopping_user"))
    password = os.getenv("PGPASSWORD", os.getenv("POSTGRES_PASSWORD", "shopping_password"))
    database = os.getenv("PGDATABASE", os.getenv("POSTGRES_DB", "shopping"))

    return f"postgresql://{user}:{password}@{host}:{port}/{database}"


def get_connection():
    """Get a psycopg2 connection. Falls back to asyncpg if psycopg2 unavailable."""
    try:
        import psycopg2
        import psycopg2.extras
        conn = psycopg2.connect(get_db_url())
        conn.set_session(autocommit=True)
        return conn, "psycopg2"
    except ImportError:
        pass

    # Fallback to sync-wrapper around asyncpg
    try:
        import asyncpg
        import asyncio

        async def _connect():
            url = get_db_url()
            return await asyncpg.connect(
                url.replace("postgresql+asyncpg://", "postgresql://")
            )

        try:
            loop = asyncio.get_running_loop()
            # Already in an async context — create task
            conn = loop.run_until_complete(_connect())
        except RuntimeError:
            # No running loop — create one
            conn = asyncio.run(_connect())
        return conn, "asyncpg"
    except ImportError:
        print("ERROR: Neither psycopg2 nor asyncpg available. Install one:")
        print("  pip install psycopg2-binary")
        print("  or: pip install asyncpg")
        sys.exit(1)


def fetch_events(conn, driver: str, date_str: str, limit: int) -> list[dict[str, Any]]:
    """Fetch events for the given date."""
    columns = [
        "id", "event_type",
        "account_id", "user_email", "anonymous_id", "session_id",
        "product_id", "product_name", "product_slug",
        "shop_id", "shop_name",
        "category_id", "category_name",
        "query", "quantity", "price", "source_page",
        "metadata_json", "created_at",
    ]
    col_str = ", ".join(columns)

    sql = f"""
        SELECT {col_str}
        FROM user_behavior_events
        WHERE created_at::date = %(date)s
        ORDER BY created_at
        LIMIT %(limit)s
    """

    if driver == "psycopg2":
        import psycopg2.extras
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, {"date": date_str, "limit": limit})
            rows = cur.fetchall()
        return [dict(r) for r in rows]
    else:
        # asyncpg
        import asyncio

        async def _fetch():
            records = await conn.fetch(sql, date_str, limit)
            return [dict(r) for r in records]

        try:
            loop = asyncio.get_running_loop()
            return loop.run_until_complete(_fetch())
        except RuntimeError:
            return asyncio.run(_fetch())


def serialize_value(val: Any) -> Any:
    """Convert PostgreSQL types to JSON-serializable values."""
    if val is None:
        return None
    if isinstance(val, datetime):
        return val.isoformat()
    if hasattr(val, "isoformat"):
        return val.isoformat()
    return val


# ── Main export logic ────────────────────────────────────────────

def export(
    date_str: str,
    output_dir: str = "/tmp/recommendation",
    limit: int = 1_000_000,
    format: str = "jsonl",
) -> dict:
    """Export events for a single date partition."""
    print(f"[export] date={date_str}  format={format}  limit={limit}")

    conn, driver = get_connection()
    print(f"[export] connected via {driver}")

    events = fetch_events(conn, driver, date_str, limit)
    print(f"[export] fetched {len(events)} events")

    # Output directory: /tmp/recommendation/events/dt=YYYY-MM-DD/
    partition_dir = os.path.join(output_dir, "events", f"dt={date_str}")
    os.makedirs(partition_dir, exist_ok=True)

    # Write JSONL (one JSON object per line — easy for Spark to read)
    jsonl_path = os.path.join(partition_dir, "events.jsonl")
    with open(jsonl_path, "w", encoding="utf-8") as f:
        for event in events:
            # Serialize all values
            record = {k: serialize_value(v) for k, v in event.items()}
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"[export] wrote {jsonl_path} ({os.path.getsize(jsonl_path)} bytes)")

    # Write _SUCCESS marker (Spark convention)
    success_path = os.path.join(partition_dir, "_SUCCESS")
    with open(success_path, "w") as f:
        f.write("")

    # Write _METADATA.json
    meta = {
        "exported_at": datetime.utcnow().isoformat() + "Z",
        "date": date_str,
        "event_count": len(events),
        "format": format,
        "columns": [
            "id", "event_type", "account_id", "user_email",
            "anonymous_id", "session_id", "product_id", "product_name",
            "product_slug", "shop_id", "shop_name", "category_id",
            "category_name", "query", "quantity", "price",
            "source_page", "metadata_json", "created_at",
        ],
    }
    meta_path = os.path.join(partition_dir, "_METADATA.json")
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)

    print(f"[export] done — {len(events)} events in {partition_dir}/")

    if conn and driver == "psycopg2":
        conn.close()

    return {
        "date": date_str,
        "event_count": len(events),
        "partition_dir": partition_dir,
        "file": jsonl_path,
        "file_size_bytes": os.path.getsize(jsonl_path),
    }


def main():
    parser = argparse.ArgumentParser(
        description="Export user_behavior_events to JSONL for HDFS ingestion"
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
        help="Max events to export (default: 1,000,000)",
    )
    parser.add_argument(
        "--format",
        choices=["jsonl"],
        default="jsonl",
        help="Output format (parquet is TODO)",
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
