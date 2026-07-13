#!/usr/bin/env python3
"""
Build item-item similarity based on user co-occurrence.

Algorithm:
  For each user (account_id or anonymous_id), collect the set of products
  they interacted with. Each pair of products in the same user's history
  gets a co-occurrence score. Normalize by sum of individual product scores.

  similarity(A, B) = sum(user_weights for users who viewed both A and B)
                     / sqrt(sum(A_scores) * sum(B_scores))

  This is a simplified cosine similarity on the user-product weighted matrix.

Output: /data/recommendations/item_similar/dt=YYYY-MM-DD/

Usage:
  python build_item_similarity.py --mode local --days 30 --top-n 20
"""

import argparse
import math
from collections import defaultdict
from context import add_common_args, load_events_local


def build_item_sim_local(events: list[dict], top_n: int, dt: str) -> list[dict]:
    """Local item-item co-occurrence computation."""

    # Step 1: Build user → {product: score} map
    user_products: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    product_total: dict[str, float] = defaultdict(float)
    product_meta: dict[str, dict] = {}

    for ev in events:
        user_key = ev.get("account_id") or ev.get("anonymous_id") or ev.get("session_id")
        # Item similarity must use stable catalog UUIDs. Name-only events and
        # search terms would produce rows that cannot be imported safely.
        pid = ev.get("product_id")
        if not user_key or not pid:
            continue
        score = ev.get("_weighted_score", 0)
        user_products[user_key][pid] += score
        product_total[pid] += score
        if pid not in product_meta:
            product_meta[pid] = {
                "product_id": ev.get("product_id"),
                "product_name": ev.get("product_name", ""),
                "product_slug": ev.get("product_slug", ""),
            }

    # Step 2: Count co-occurrences
    co_occur: dict[tuple, float] = defaultdict(float)

    for user_key, prods in user_products.items():
        pids = list(prods.keys())
        for i in range(len(pids)):
            for j in range(i + 1, len(pids)):
                a, b = pids[i], pids[j]
                pair_score = min(prods[a], prods[b])  # co-occurrence strength
                key = tuple(sorted([a, b]))
                co_occur[key] += pair_score

    # Step 3: Normalize → similarity scores
    product_sims: dict[str, list[dict]] = defaultdict(list)

    for (a, b), pair_score in co_occur.items():
        norm = math.sqrt(product_total.get(a, 1) * product_total.get(b, 1))
        if norm <= 0:
            continue
        sim = round(pair_score / norm, 4)
        if sim < 0.01:
            continue

        product_sims[a].append({"similar_product_id": b, "score": sim})
        product_sims[b].append({"similar_product_id": a, "score": sim})

    # Step 4: Keep top-N per product
    result = []
    for pid, sims in product_sims.items():
        sims.sort(key=lambda x: x["score"], reverse=True)
        top_sims = sims[:top_n]
        meta = product_meta.get(pid, {})
        for s in top_sims:
            sim_meta = product_meta.get(s["similar_product_id"], {})
            result.append({
                "product_id": meta.get("product_id", pid),
                "product_name": meta.get("product_name", ""),
                "product_slug": meta.get("product_slug", ""),
                "similar_product_id": s["similar_product_id"],
                "similar_product_name": sim_meta.get("product_name", ""),
                "score": s["score"],
                "reason": "Customers who viewed this also viewed",
                "dt": dt,
            })

    # Sort by score desc
    result.sort(key=lambda x: x["score"], reverse=True)
    return result


def main():
    parser = argparse.ArgumentParser(description="Build item-item similarity")
    add_common_args(parser)
    args = parser.parse_args()

    print(f"[item_similarity] mode={args.mode}  days={args.days}  top_n={args.top_n}  date={args.date}")

    output_subpath = f"recommendations/item_similar/dt={args.date}"

    if args.mode == "local":
        events = load_events_local(args.input_dir, args.days, args.date)
        print(f"[item_similarity] loaded {len(events)} events")
        rows = build_item_sim_local(events, args.top_n, args.date)

        from context import write_output_local
        write_output_local(rows, args.output_dir, output_subpath)
    else:
        print("[item_similarity] Spark mode requires PySpark. Install: pip install pyspark")
        print("[item_similarity] Falling back to local mode...")
        events = load_events_local(args.input_dir, args.days, args.date)
        rows = build_item_sim_local(events, args.top_n, args.date)
        from context import write_output_local
        write_output_local(rows, args.output_dir, output_subpath)

    # Summary
    unique_products = len(set(r["product_id"] for r in rows))
    print(f"\nBuilt {len(rows)} similarity pairs for {unique_products} products")
    if rows:
        top = rows[0]
        print(f"  Top pair: {top.get('product_name')} <-> {top.get('similar_product_name')} (score={top['score']})")
    print(f"\nOutput → {args.output_dir}/{output_subpath}/")


if __name__ == "__main__":
    main()
