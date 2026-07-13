#!/usr/bin/env python3
"""
Build user preference profiles from weighted event history.

For each user (identified by account_id or anonymous_id), aggregate:
  - category affinity scores
  - shop affinity scores
  - product interest scores
  - price range preference (min/max observed)

Time decay: score = event_weight * exp(-days_since_event / 30)

Output: /data/features/user_preferences/dt=YYYY-MM-DD/

Usage:
  python build_user_preferences.py --mode local --days 30
"""

import argparse
import json
from collections import defaultdict
from context import add_common_args, load_events_local


def build_user_prefs_local(events: list[dict], dt: str) -> list[dict]:
    """Aggregate per-user preferences locally."""
    users: dict[str, dict] = defaultdict(lambda: {
        "category_scores": defaultdict(float),
        "shop_scores": defaultdict(float),
        "product_scores": defaultdict(float),
        "price_min": None,
        "price_max": None,
        "total_score": 0.0,
        "event_count": 0,
    })

    for ev in events:
        user_key = ev.get("account_id") or ev.get("anonymous_id") or ev.get("session_id")
        if not user_key:
            continue

        score = ev.get("_weighted_score", 0)
        prefs = users[user_key]
        prefs["total_score"] += score
        prefs["event_count"] += 1

        cat = ev.get("category_name")
        if cat:
            prefs["category_scores"][cat] += score

        shop = ev.get("shop_name")
        if shop:
            prefs["shop_scores"][shop] += score

        # Keep product affinities importable by using only real catalog UUIDs.
        # Search terms and legacy name-only events still contribute to category
        # and shop affinity when present, but not to product recommendations.
        pid = ev.get("product_id")
        if pid:
            prefs["product_scores"][pid] += score

        price = ev.get("price")
        if price is not None and price > 0:
            if prefs["price_min"] is None or price < prefs["price_min"]:
                prefs["price_min"] = price
            if prefs["price_max"] is None or price > prefs["price_max"]:
                prefs["price_max"] = price

    result = []
    for user_key, prefs in users.items():
        # Sort and take top
        top_cats = sorted(prefs["category_scores"].items(), key=lambda x: x[1], reverse=True)[:5]
        top_shops = sorted(prefs["shop_scores"].items(), key=lambda x: x[1], reverse=True)[:5]
        top_products = sorted(prefs["product_scores"].items(), key=lambda x: x[1], reverse=True)[:10]

        result.append({
            "user_key": user_key,
            "dt": dt,
            "total_score": round(prefs["total_score"], 4),
            "event_count": prefs["event_count"],
            "top_categories": [{"name": c, "score": round(s, 4)} for c, s in top_cats],
            "top_shops": [{"name": s, "score": round(sc, 4)} for s, sc in top_shops],
            "top_products": [{"id": p, "score": round(sp, 4)} for p, sp in top_products],
            "price_range": {
                "min": prefs["price_min"],
                "max": prefs["price_max"],
            },
        })

    # Sort by total_score desc
    result.sort(key=lambda x: x["total_score"], reverse=True)
    return result


def main():
    parser = argparse.ArgumentParser(description="Build user preferences")
    add_common_args(parser)
    args = parser.parse_args()

    print(f"[user_preferences] mode={args.mode}  days={args.days}  date={args.date}")

    output_subpath = f"features/user_preferences/dt={args.date}"

    if args.mode == "local":
        events = load_events_local(args.input_dir, args.days, args.date)
        print(f"[user_preferences] loaded {len(events)} events")
        rows = build_user_prefs_local(events, args.date)

        from context import write_output_local
        write_output_local(rows, args.output_dir, output_subpath)
    else:
        print("[user_preferences] Spark mode requires PySpark. Install: pip install pyspark")
        print("[user_preferences] Falling back to local mode...")
        events = load_events_local(args.input_dir, args.days, args.date)
        rows = build_user_prefs_local(events, args.date)
        from context import write_output_local
        write_output_local(rows, args.output_dir, output_subpath)

    print(f"\nBuilt preferences for {len(rows)} users")
    if rows:
        print(f"  Top user: {rows[0]['user_key'][:20]}... score={rows[0]['total_score']}")
        print(f"  Categories: {json.dumps(rows[0]['top_categories'][:3])}")
    print(f"\nOutput → {args.output_dir}/{output_subpath}/")


if __name__ == "__main__":
    main()
