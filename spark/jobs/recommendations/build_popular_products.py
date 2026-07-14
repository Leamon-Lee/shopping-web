#!/usr/bin/env python3
from __future__ import annotations

"""
Build popular/hot products based on weighted user behavior events.

Algorithm:
  For each product, sum weighted scores (event_weight * time_decay)
  across all events in the lookback window. Rank by total score.

Weights:
  product_view = 1    search = 2    add_to_cart = 5
  favorite_product = 6    order_created = 8    order_paid = 10
  recommendation_click = 3

Output: /data/recommendations/popular_products/dt=YYYY-MM-DD/

Usage:
  python build_popular_products.py --mode local --days 7 --top-n 20
  spark-submit build_popular_products.py --mode spark --days 7
"""

import argparse
from collections import defaultdict
from context import (
    add_common_args, load_events_local, load_events_spark,
    write_output_local, write_output_spark,
)


def compute_popular_local(events: list[dict], top_n: int, dt: str) -> list[dict]:
    """Local pandas-less aggregation."""
    product_scores: dict[str, float] = defaultdict(float)
    product_meta: dict[str, dict] = {}

    for ev in events:
        # Product recommendations must be keyed by real catalog UUIDs. Name-only
        # legacy events and search terms are useful analytics signals, but they
        # cannot be safely imported into UUID-backed recommendation tables.
        pid = ev.get("product_id")
        if not pid:
            continue
        score = ev.get("_weighted_score", 0)
        product_scores[pid] += score
        if pid not in product_meta:
            product_meta[pid] = {
                "product_id": ev.get("product_id"),
                "product_name": ev.get("product_name", ""),
                "product_slug": ev.get("product_slug", ""),
                "category_id": ev.get("category_id"),
                "category_name": ev.get("category_name", ""),
                "shop_id": ev.get("shop_id"),
                "shop_name": ev.get("shop_name", ""),
            }

    # Sort and rank
    ranked = [
        item for item in sorted(product_scores.items(), key=lambda x: x[1], reverse=True)
        if item[1] > 0
    ][:top_n]
    result = []
    for rank, (pid, total_score) in enumerate(ranked, start=1):
        meta = product_meta.get(pid, {})
        result.append({
            "product_id": meta.get("product_id"),
            "product_name": meta.get("product_name", ""),
            "product_slug": meta.get("product_slug", ""),
            "category_id": meta.get("category_id"),
            "category_name": meta.get("category_name", ""),
            "shop_id": meta.get("shop_id"),
            "shop_name": meta.get("shop_name", ""),
            "score": round(total_score, 4),
            "rank": rank,
            "dt": dt,
        })
    return result


def compute_popular_spark(spark, hdfs_input: str, days: int, top_n: int, dt: str):
    """PySpark aggregation with weighted scores."""
    from pyspark.sql import functions as F
    import datetime as _dt

    # This import is conditional — only called in spark mode
    df = load_events_spark(spark, hdfs_input, days, dt)

    product_col = F.col("product_id")

    agg = (
        df.filter(product_col.isNotNull())
        .groupBy(
            product_col.alias("product_id"),
            F.first("product_name", ignorenulls=True).alias("product_name"),
            F.first("product_slug", ignorenulls=True).alias("product_slug"),
            F.first("category_id", ignorenulls=True).alias("category_id"),
            F.first("category_name", ignorenulls=True).alias("category_name"),
            F.first("shop_id", ignorenulls=True).alias("shop_id"),
            F.first("shop_name", ignorenulls=True).alias("shop_name"),
        )
        .agg(F.sum("_weighted_score").alias("score"))
        .where(F.col("score") > 0)
        .orderBy(F.desc("score"))
        .limit(top_n)
    )

    result = agg.withColumn("rank", F.row_number().over(
        __import__("pyspark.sql.window", fromlist=["Window"]).Window.orderBy(F.desc("score"))
    )).withColumn("dt", F.lit(dt))

    return result


def main():
    parser = argparse.ArgumentParser(description="Build popular products")
    add_common_args(parser)
    args = parser.parse_args()

    print(f"[popular_products] mode={args.mode}  days={args.days}  top_n={args.top_n}  date={args.date}")

    output_subpath = f"recommendations/popular_products/dt={args.date}"

    if args.mode == "local":
        events = load_events_local(args.input_dir, args.days, args.date)
        print(f"[popular_products] loaded {len(events)} events")
        rows = compute_popular_local(events, args.top_n, args.date)
        write_output_local(rows, args.output_dir, output_subpath)
    else:
        from pyspark.sql import SparkSession
        spark = SparkSession.builder \
            .appName("popular_products") \
            .config("spark.hadoop.fs.defaultFS", "hdfs://master:9000") \
            .getOrCreate()
        try:
            rows_df = compute_popular_spark(spark, args.hdfs_input, args.days, args.top_n, args.date)
            write_output_spark(rows_df, args.hdfs_output, output_subpath)
        finally:
            spark.stop()

    # Print top 5
    print("\nTop 5 popular products:")
    if args.mode == "local":
        for r in rows[:5]:
            print(f"  #{r['rank']} {r.get('product_name','?')} score={r['score']}")
    print(f"\nOutput → {args.output_dir}/{output_subpath}/")


if __name__ == "__main__":
    main()
