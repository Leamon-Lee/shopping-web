from __future__ import annotations

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
    "product_review": 1,
    "product_rating": 1,
}

RATING_WEIGHTS = {
    5: 8,
    4: 5,
    3: 1,
    2: -4,
    1: -8,
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


def rating_score(rating: Any, has_content: Any = False) -> float:
    """Map a 1-5 rating into a signed recommendation score."""
    try:
        normalized_rating = int(rating)
    except (TypeError, ValueError):
        return 0.0
    score = float(RATING_WEIGHTS.get(normalized_rating, 0))
    if score > 0 and bool(has_content):
        score += 1.0
    return score


def event_weighted_score(event: dict, reference_date: datetime) -> float:
    """Compute local score for normal events and rating/review events."""
    event_type = event.get("event_type", "")
    metadata = event.get("metadata_json") or event.get("metadata") or {}
    if event_type in {"product_review", "product_rating"}:
        return rating_score(
            metadata.get("rating") if isinstance(metadata, dict) else event.get("rating"),
            metadata.get("has_content") if isinstance(metadata, dict) else bool(event.get("content")),
        ) * time_decay(event.get("created_at") or event.get("updated_at") or reference_date, reference_date)
    return weighted_score(event_type, event.get("created_at"), reference_date)


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
    seen_review_ids = set()
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
                        event["_weighted_score"] = event_weighted_score(event, ref_dt)
                        metadata = event.get("metadata_json") or {}
                        if event.get("event_type") == "product_review" and isinstance(metadata, dict):
                            review_id = metadata.get("review_id")
                            if review_id:
                                seen_review_ids.add(str(review_id))
                        all_events.append(event)
                    except json.JSONDecodeError:
                        continue
        reviews_path = os.path.join(input_dir, "reviews", f"dt={day}", "reviews.jsonl")
        if os.path.exists(reviews_path):
            with open(reviews_path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        review = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    content = review.get("content") or ""
                    review_id = review.get("review_id")
                    if review_id and str(review_id) in seen_review_ids:
                        continue
                    event = {
                        "id": review_id,
                        "event_type": "product_rating",
                        "account_id": review.get("account_id"),
                        "anonymous_id": None,
                        "session_id": None,
                        "product_id": review.get("product_id"),
                        "product_name": review.get("product_name", ""),
                        "product_slug": review.get("product_slug", ""),
                        "category_id": review.get("category_id"),
                        "category_name": review.get("category_name", ""),
                        "shop_id": review.get("shop_id"),
                        "shop_name": review.get("shop_name", ""),
                        "price": review.get("price"),
                        "created_at": review.get("created_at") or review.get("updated_at"),
                        "metadata_json": {
                            "rating": review.get("rating"),
                            "review_id": review.get("review_id"),
                            "has_content": bool(str(content).strip()),
                            "content_length": len(str(content).strip()),
                        },
                    }
                    event["_weighted_score"] = event_weighted_score(event, ref_dt)
                    all_events.append(event)
    return all_events


def load_events_spark(spark, hdfs_input: str, days: int, reference_date: str):
    """Load events from HDFS Parquet/JSONL using PySpark."""
    from pyspark.sql import functions as F
    from pyspark.sql.types import FloatType

    event_paths = []
    review_paths = []
    ref_dt = datetime.fromisoformat(reference_date)
    for i in range(days):
        day = (ref_dt - timedelta(days=i)).strftime("%Y-%m-%d")
        event_paths.append(f"{hdfs_input}/events/dt={day}/events.jsonl")
        review_paths.append(f"{hdfs_input}/reviews/dt={day}/reviews.jsonl")

    df = spark.read.option("mode", "PERMISSIVE").json(event_paths)

    try:
        reviews = spark.read.option("mode", "PERMISSIVE").json(review_paths)
        if "review_id" not in reviews.columns or "product_id" not in reviews.columns:
            raise ValueError("empty or incompatible review partitions")
        reviews = reviews.select(
            F.col("review_id").alias("id"),
            F.lit("product_rating").alias("event_type"),
            "account_id",
            F.lit(None).cast("string").alias("user_email"),
            F.lit(None).cast("string").alias("anonymous_id"),
            F.lit(None).cast("string").alias("session_id"),
            "product_id",
            F.col("product_name") if "product_name" in reviews.columns else F.lit("").alias("product_name"),
            F.col("product_slug") if "product_slug" in reviews.columns else F.lit("").alias("product_slug"),
            F.col("shop_id") if "shop_id" in reviews.columns else F.lit(None).cast("string").alias("shop_id"),
            F.col("shop_name") if "shop_name" in reviews.columns else F.lit("").alias("shop_name"),
            F.col("category_id") if "category_id" in reviews.columns else F.lit(None).cast("string").alias("category_id"),
            F.col("category_name") if "category_name" in reviews.columns else F.lit("").alias("category_name"),
            F.lit(None).cast("string").alias("query"),
            F.lit(None).cast("int").alias("quantity"),
            F.col("price") if "price" in reviews.columns else F.lit(None).cast("double").alias("price"),
            F.lit(None).cast("string").alias("source_page"),
            F.struct(
                F.col("rating").alias("rating"),
                F.col("review_id").alias("review_id"),
                (F.length(F.coalesce(F.col("content"), F.lit(""))) > 0).alias("has_content"),
                F.length(F.coalesce(F.col("content"), F.lit(""))).alias("content_length"),
            ).alias("metadata_json"),
            F.coalesce(F.col("created_at"), F.col("updated_at")).alias("created_at"),
        )
        event_review_ids = (
            df
            .filter(F.col("event_type") == F.lit("product_review"))
            .select(F.col("metadata_json.review_id").cast("string").alias("_review_id"))
            .where(F.col("_review_id").isNotNull())
            .distinct()
        )
        reviews = (
            reviews
            .join(event_review_ids, reviews["id"].cast("string") == event_review_ids["_review_id"], "left_anti")
        )
        df = df.unionByName(reviews, allowMissingColumns=True)
    except Exception as exc:
        print(f"[load_events_spark] reviews not loaded: {exc}")

    # Add weighted score column
    weight_map = F.create_map([F.lit(x) for k, v in EVENT_WEIGHTS.items() for x in (k, float(v))])
    df = df.withColumn("_base_weight", F.coalesce(weight_map[F.col("event_type")], F.lit(0.5)))
    rating_map = F.create_map([F.lit(x) for k, v in RATING_WEIGHTS.items() for x in (k, float(v))])
    metadata_fields = []
    try:
        metadata_fields = df.schema["metadata_json"].dataType.fieldNames()
    except Exception:
        metadata_fields = []
    rating = (
        F.col("metadata_json.rating").cast("int")
        if "rating" in metadata_fields
        else F.lit(None).cast("int")
    )
    has_content = (
        F.col("metadata_json.has_content")
        if "has_content" in metadata_fields
        else F.lit(False)
    )
    review_score = F.coalesce(rating_map[rating], F.lit(0.0))
    review_score = F.when(
        (review_score > 0) & (has_content == F.lit(True)),
        review_score + F.lit(1.0),
    ).otherwise(review_score)
    df = df.withColumn(
        "_base_weight",
        F.when(F.col("event_type").isin("product_review", "product_rating"), review_score)
        .otherwise(F.col("_base_weight")),
    )

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
