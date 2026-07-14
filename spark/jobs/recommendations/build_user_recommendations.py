#!/usr/bin/env python3
from __future__ import annotations

"""
Build commercial per-user recommendations from Hadoop/Spark event history.

This job is the batch counterpart of the online mixer:
  HDFS events/reviews -> user intent profile -> candidate scoring -> top products

Output: /data/recommendations/user_recommendations/dt=YYYY-MM-DD/
"""

import argparse
import json
import math
import os
from collections import defaultdict
from typing import Optional

from context import add_common_args, load_events_local, load_events_spark, write_output_spark


def price_band(price) -> str | None:
    try:
        value = float(price)
    except (TypeError, ValueError):
        return None
    if value < 25:
        return "Under $25"
    if value < 50:
        return "$25-$50"
    if value < 100:
        return "$50-$100"
    return "$100+"


def user_key_for_event(ev: dict) -> str | None:
    return ev.get("account_id") or ev.get("user_email") or ev.get("anonymous_id") or ev.get("session_id")


def load_catalog_local(input_dir: str, dt: str) -> list[dict]:
    path = os.path.join(input_dir, "products", f"dt={dt}", "products.jsonl")
    if not os.path.exists(path):
        return []
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def normalize_catalog_product(row: dict) -> dict:
    return {
        "product_id": row.get("product_id") or row.get("id"),
        "product_name": row.get("product_name") or row.get("name") or "",
        "product_slug": row.get("product_slug") or row.get("slug") or "",
        "category_name": row.get("category_name") or "",
        "shop_name": row.get("shop_name") or "",
        "price": row.get("price"),
    }


def build_user_recs_local(events: list[dict], top_n: int, dt: str, catalog: Optional[list[dict]] = None) -> list[dict]:
    product_meta: dict[str, dict] = {}
    product_popularity: dict[str, float] = defaultdict(float)
    product_rating_sum: dict[str, float] = defaultdict(float)
    product_rating_count: dict[str, int] = defaultdict(int)
    user_product_scores: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    user_category_scores: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    user_shop_scores: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    user_price_scores: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    category_products: dict[str, set[str]] = defaultdict(set)
    shop_products: dict[str, set[str]] = defaultdict(set)
    user_products_for_cooccur: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))

    for row in catalog or []:
        product = normalize_catalog_product(row)
        pid = product.get("product_id")
        if not pid:
            continue
        product_meta[pid] = product
        category = product.get("category_name") or ""
        shop = product.get("shop_name") or ""
        if category:
            category_products[category].add(pid)
        if shop:
            shop_products[shop].add(pid)

    for ev in events:
        pid = ev.get("product_id")
        if not pid:
            continue
        score = float(ev.get("_weighted_score") or 0)
        if score == 0:
            continue

        category = ev.get("category_name") or ""
        shop = ev.get("shop_name") or ""
        band = price_band(ev.get("price"))
        user_key = user_key_for_event(ev)

        product_popularity[pid] += max(score, 0)
        if pid not in product_meta:
            product_meta[pid] = {
                "product_id": pid,
                "product_name": ev.get("product_name", ""),
                "product_slug": ev.get("product_slug", ""),
                "category_name": category,
                "shop_name": shop,
                "price": ev.get("price"),
            }
        if category:
            category_products[category].add(pid)
        if shop:
            shop_products[shop].add(pid)

        event_type = ev.get("event_type")
        metadata = ev.get("metadata_json") or ev.get("metadata") or {}
        if event_type in {"product_review", "product_rating"}:
            try:
                rating = int(metadata.get("rating") if isinstance(metadata, dict) else ev.get("rating"))
            except (TypeError, ValueError):
                rating = None
            if rating:
                product_rating_sum[pid] += rating
                product_rating_count[pid] += 1

        if not user_key:
            continue
        user_product_scores[user_key][pid] += score
        if category:
            user_category_scores[user_key][category] += score
        if shop:
            user_shop_scores[user_key][shop] += score
        if band:
            user_price_scores[user_key][band] += score
        if score > 0:
            user_products_for_cooccur[user_key][pid] += score

    cooccur: dict[tuple[str, str], float] = defaultdict(float)
    for _user, product_scores in user_products_for_cooccur.items():
        product_ids = list(product_scores.keys())
        for i, left in enumerate(product_ids):
            for right in product_ids[i + 1:]:
                pair = tuple(sorted((left, right)))
                cooccur[pair] += min(product_scores[left], product_scores[right])

    max_popularity = max(product_popularity.values(), default=1.0)
    rows: list[dict] = []

    for user_key, seed_scores in user_product_scores.items():
        positive_seed_ids = {pid for pid, score in seed_scores.items() if score > 0}
        if not positive_seed_ids:
            continue

        user_candidates: dict[str, dict] = {}
        max_cat = max(user_category_scores[user_key].values(), default=1.0)
        max_shop = max(user_shop_scores[user_key].values(), default=1.0)
        max_price = max(user_price_scores[user_key].values(), default=1.0)

        def add_candidate(pid: str, score: float, source: str):
            if pid in positive_seed_ids or pid not in product_meta:
                return
            current = user_candidates.setdefault(pid, {
                "id": pid,
                "product_id": pid,
                "name": product_meta[pid].get("product_name", ""),
                "slug": product_meta[pid].get("product_slug", ""),
                "score": 0.0,
                "sources": set(),
            })
            current["score"] += score
            current["sources"].add(source)

        for category, affinity in user_category_scores[user_key].items():
            for pid in category_products.get(category, []):
                add_candidate(pid, 58.0 * (affinity / max_cat), "category")

        for shop, affinity in user_shop_scores[user_key].items():
            for pid in shop_products.get(shop, []):
                add_candidate(pid, 20.0 * (affinity / max_shop), "shop")

        for pid, meta in product_meta.items():
            band = price_band(meta.get("price"))
            price_affinity = (user_price_scores[user_key].get(band, 0.0) / max_price) if band else 0.0
            popularity = product_popularity.get(pid, 0.0) / max_popularity
            add_candidate(pid, 10.0 * price_affinity + 14.0 * popularity, "commercial_explore")

        for (left, right), pair_score in cooccur.items():
            if left in positive_seed_ids:
                add_candidate(right, 26.0 * math.log1p(pair_score), "itemcf")
            if right in positive_seed_ids:
                add_candidate(left, 26.0 * math.log1p(pair_score), "itemcf")

        ranked = []
        for pid, candidate in user_candidates.items():
            rating_count = product_rating_count.get(pid, 0)
            if rating_count:
                avg_rating = product_rating_sum[pid] / rating_count
                candidate["score"] += max(avg_rating - 3.0, 0.0) * min(rating_count, 20) * 0.8
            ranked.append(candidate)

        ranked.sort(key=lambda item: item["score"], reverse=True)

        selected = []
        category_counts: dict[str, int] = defaultdict(int)
        for candidate in ranked:
            category = product_meta[candidate["id"]].get("category_name", "")
            penalty = category_counts[category] * 8.0
            candidate["_rerank_score"] = candidate["score"] - penalty
        for candidate in sorted(ranked, key=lambda item: item["_rerank_score"], reverse=True):
            category = product_meta[candidate["id"]].get("category_name", "")
            if category_counts[category] >= 8 and len(selected) < top_n:
                continue
            selected.append(candidate)
            category_counts[category] += 1
            if len(selected) >= top_n:
                break

        top_categories = sorted(
            user_category_scores[user_key].items(),
            key=lambda item: item[1],
            reverse=True,
        )[:5]

        rows.append({
            "user_key": user_key,
            "dt": dt,
            "total_score": round(sum(max(v, 0) for v in seed_scores.values()), 4),
            "event_count": len(seed_scores),
            "top_categories": [{"name": name, "score": round(score, 4)} for name, score in top_categories],
            "top_products": [
                {
                    "id": item["id"],
                    "product_id": item["product_id"],
                    "name": item["name"],
                    "slug": item["slug"],
                    "score": round(item["score"], 4),
                    "algorithm": "hadoop_commerce_v1",
                    "reason": f"Based on your interest in {top_categories[0][0]}" if top_categories else "Recommended for you",
                }
                for item in selected
            ],
        })

    rows.sort(key=lambda item: item["total_score"], reverse=True)
    return rows


def main():
    parser = argparse.ArgumentParser(description="Build Hadoop commerce user recommendations")
    add_common_args(parser)
    args = parser.parse_args()
    output_subpath = f"recommendations/user_recommendations/dt={args.date}"

    print(f"[user_recommendations] mode={args.mode} days={args.days} top_n={args.top_n} date={args.date}")
    if args.mode == "local":
        events = load_events_local(args.input_dir, args.days, args.date)
        catalog = load_catalog_local(args.input_dir, args.date)
        rows = build_user_recs_local(events, args.top_n, args.date, catalog)
        from context import write_output_local
        write_output_local(rows, args.output_dir, output_subpath)
    else:
        from pyspark.sql import SparkSession

        spark = SparkSession.builder \
            .appName("user_recommendations") \
            .config("spark.hadoop.fs.defaultFS", "hdfs://master:9000") \
            .getOrCreate()
        try:
            events_df = load_events_spark(spark, args.hdfs_input, args.days, args.date)
            events = [row.asDict(recursive=True) for row in events_df.collect()]
            try:
                catalog_df = spark.read.option("mode", "PERMISSIVE").json(
                    f"{args.hdfs_input}/products/dt={args.date}/products.jsonl"
                )
                catalog = [row.asDict(recursive=True) for row in catalog_df.collect()]
            except Exception as exc:
                print(f"[user_recommendations] product catalog not loaded: {exc}")
                catalog = []
            rows = build_user_recs_local(events, args.top_n, args.date, catalog)
            if rows:
                write_output_spark(spark.createDataFrame(rows), args.hdfs_output, output_subpath)
            else:
                from pyspark.sql.types import ArrayType, DoubleType, IntegerType, StringType, StructField, StructType
                schema = StructType([
                    StructField("user_key", StringType(), True),
                    StructField("dt", StringType(), True),
                    StructField("total_score", DoubleType(), True),
                    StructField("event_count", IntegerType(), True),
                    StructField("top_categories", ArrayType(StructType([
                        StructField("name", StringType(), True),
                        StructField("score", DoubleType(), True),
                    ])), True),
                    StructField("top_products", ArrayType(StructType([
                        StructField("id", StringType(), True),
                        StructField("product_id", StringType(), True),
                        StructField("name", StringType(), True),
                        StructField("slug", StringType(), True),
                        StructField("score", DoubleType(), True),
                        StructField("algorithm", StringType(), True),
                        StructField("reason", StringType(), True),
                    ])), True),
                ])
                write_output_spark(spark.createDataFrame([], schema), args.hdfs_output, output_subpath)
        finally:
            spark.stop()

    print(f"Built Hadoop commerce recommendations for {len(rows)} users")
    if rows:
        print(f"  Top user: {rows[0]['user_key']} recs={len(rows[0]['top_products'])}")


if __name__ == "__main__":
    main()
