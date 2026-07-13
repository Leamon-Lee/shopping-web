"""
Shared Spark context and data loading utilities.

Supports:
  --mode local  : pandas/numpy from local JSONL files
  --mode spark  : PySpark from HDFS
"""

import argparse
import json
import math
import os
from datetime import datetime, timedelta
from typing import Any

# ── Event weights (used by all recommendation jobs) ──────────────

EVENT_WEIGHTS = {
    "product_view": 1,
    "search": 2,
    "add_to_cart": 5,
    "favorite_product": 6,
    "order_created": 8,
    "order_paid": 10,
    "recommendation_click": 3,
    "recommendation_add_to_cart": 4,
}

# ── Time decay ───────────────────────────────────────────────────

def time_decay(event_date: datetime, reference_date: datetime, half_life_days: int = 30) -> float:
    """Exponential decay: exp(-days / half_life)."""
    if isinstance(event_date, str):
        event_date = datetime.fromisoformat(event_date.replace("Z", "+00:00"))
    days = (reference_date - event_date.replace(tzinfo=None)).total_seconds() / 86400.0
    if days < 0:
        days = 0
    return math.exp(-days / half_life_days)


def weighted_score(event_type: str, event_date: Any, reference_date: datetime) -> float:
    """Combined weight = base_weight * time_decay."""
    weight = EVENT_WEIGHTS.get(event_type, 0.5)
    if event_date:
        if isinstance(event_date, str):
            try:
                event_date = datetime.fromisoformat(event_date.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                event_date = reference_date
        return weight * time_decay(event_date, reference_date)
    return weight


# ── Data loading ──────────────────────────────────────────────────

def add_common_args(parser: argparse.ArgumentParser):
    parser.add_argument("--mode", choices=["local", "spark"], default="local",
                        help="Execution mode (default: local)")
    parser.add_argument("--date", default=(datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),
                        help="Reference date for partition output (default: yesterday)")
    parser.add_argument("--days", type=int, default=30,
                        help="Lookback window in days (default: 30)")
    parser.add_argument("--top-n", type=int, default=50,
                        help="Number of recommendations to output (default: 50)")
    parser.add_argument("--input-dir", default="/tmp/recommendation",
                        help="Local input base dir in --mode local")
    parser.add_argument("--output-dir", default="/tmp/recommendation",
                        help="Local output base dir in --mode local")
    parser.add_argument("--hdfs-input", default="hdfs://master:9000/data/raw",
                        help="HDFS input base path")
    parser.add_argument("--hdfs-output", default="hdfs://master:9000/data",
                        help="HDFS output base path")


def load_events_local(input_dir: str, days: int, reference_date: str) -> list[dict]:
    """Load events from local JSONL files for the given date range."""
    all_events = []
    ref_dt = datetime.fromisoformat(reference_date)

    for i in range(days):
        day = (ref_dt - timedelta(days=i)).strftime("%Y-%m-%d")
        path = os.path.join(input_dir, "events", f"dt={day}", "events.jsonl")
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        event = json.loads(line)
                        event["_weighted_score"] = weighted_score(
                            event.get("event_type", ""),
                            event.get("created_at"),
                            ref_dt,
                        )
                        all_events.append(event)
                    except json.JSONDecodeError:
                        continue
    return all_events


def load_events_spark(spark, hdfs_input: str, days: int, reference_date: str):
    """Load events from HDFS Parquet/JSONL using PySpark."""
    from pyspark.sql import functions as F
    from pyspark.sql.types import FloatType

    paths = []
    ref_dt = datetime.fromisoformat(reference_date)
    for i in range(days):
        day = (ref_dt - timedelta(days=i)).strftime("%Y-%m-%d")
        paths.append(f"{hdfs_input}/events/dt={day}/events.jsonl")

    df = spark.read.json(paths)

    # Add weighted score column
    weight_map = F.create_map([F.lit(x) for k, v in EVENT_WEIGHTS.items() for x in (k, float(v))])
    df = df.withColumn("_base_weight", F.coalesce(weight_map[F.col("event_type")], F.lit(0.5)))

    # Time decay
    days_col = F.datediff(F.lit(reference_date), F.to_date(F.col("created_at")))
    df = df.withColumn("_decay", F.exp(-F.greatest(days_col, F.lit(0)) / F.lit(30.0)))
    df = df.withColumn("_weighted_score", (F.col("_base_weight") * F.col("_decay")).cast(FloatType()))

    return df


def write_output_local(rows: list[dict], output_dir: str, sub_path: str):
    """Write list-of-dict rows as JSONL to a local partition directory."""
    full_dir = os.path.join(output_dir, sub_path)
    os.makedirs(full_dir, exist_ok=True)
    path = os.path.join(full_dir, "part-00000.jsonl")
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    # _SUCCESS marker
    with open(os.path.join(full_dir, "_SUCCESS"), "w") as f:
        f.write("")
    print(f"  wrote {len(rows)} rows → {path}")


def write_output_spark(df, hdfs_output: str, sub_path: str):
    """Write a Spark DataFrame as JSONL to HDFS."""
    full_path = f"{hdfs_output}/{sub_path}"
    df.coalesce(1).write.mode("overwrite").json(full_path)
    print(f"  wrote to {full_path}")
