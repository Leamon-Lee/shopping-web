#!/usr/bin/env python3
"""
Orchestrate the full recommendation pipeline.

Pipeline stages:
  1. build_popular_products   → global trending/hot products
  2. build_user_preferences   → per-user category/shop/product affinities
  3. build_item_similarity    → co-occurrence based item-item similarity

Usage:
  # Local mode (development/testing — works without Spark)
  python run_all.py --mode local --days 7 --top-n 20 --date 2026-07-13

  # Spark mode (production — HDFS input/output)
  spark-submit --master yarn --deploy-mode cluster \
      run_all.py --mode spark --days 30 --top-n 50

  # Stage selection
  python run_all.py --stages popular,similar --mode local
"""

import argparse
import subprocess
import sys
import os
from datetime import datetime


STAGES = {
    "popular": "build_popular_products.py",
    "preferences": "build_user_preferences.py",
    "similar": "build_item_similarity.py",
}


def run_stage(stage_name: str, script_name: str, args: argparse.Namespace) -> bool:
    """Run a single stage and return success/failure."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(script_dir, script_name)

    cmd = [
        sys.executable, script_path,
        "--mode", args.mode,
        "--date", args.date,
        "--days", str(args.days),
        "--top-n", str(args.top_n),
        "--input-dir", args.input_dir,
        "--output-dir", args.output_dir,
    ]

    if args.mode == "spark":
        cmd.extend(["--hdfs-input", args.hdfs_input, "--hdfs-output", args.hdfs_output])

    print(f"\n{'='*60}")
    print(f"STAGE: {stage_name} ({script_name})")
    print(f"  {' '.join(cmd)}")
    print(f"{'='*60}")

    result = subprocess.run(cmd, capture_output=False)
    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(description="Run full recommendation pipeline")
    parser.add_argument("--stages", default="popular,preferences,similar",
                        help="Comma-separated stages to run (default: all)")
    parser.add_argument("--mode", choices=["local", "spark"], default="local")
    parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"))
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--top-n", type=int, default=20)
    parser.add_argument("--input-dir", default="/tmp/recommendation")
    parser.add_argument("--output-dir", default="/tmp/recommendation")
    parser.add_argument("--hdfs-input", default="hdfs://master:9000/data/raw")
    parser.add_argument("--hdfs-output", default="hdfs://master:9000/data")
    args = parser.parse_args()

    stages_to_run = [s.strip() for s in args.stages.split(",")]
    print(f"Pipeline: {stages_to_run}  mode={args.mode}  date={args.date}")

    results = {}
    for stage_name in stages_to_run:
        if stage_name not in STAGES:
            print(f"[SKIP] Unknown stage: {stage_name}")
            results[stage_name] = "unknown"
            continue
        ok = run_stage(stage_name, STAGES[stage_name], args)
        results[stage_name] = "OK" if ok else "FAILED"

    # Summary
    print(f"\n{'='*60}")
    print("PIPELINE SUMMARY")
    print(f"{'='*60}")
    for stage, status in results.items():
        icon = "[OK]" if status == "OK" else "[FAIL]"
        print(f"  {icon} {stage}: {status}")

    print(f"\nOutput tree ({args.output_dir}):")
    tree_cmd = ["find", args.output_dir, "-type", "f", "-name", "*.jsonl"]
    try:
        subprocess.run(tree_cmd)
    except Exception:
        pass

    failed = sum(1 for v in results.values() if v != "OK")
    sys.exit(1 if failed > 0 else 0)


if __name__ == "__main__":
    main()
