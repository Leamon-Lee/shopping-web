"""Compatibility wrapper for the current item-similarity recommendation job."""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / "spark" / "jobs" / "recommendations" / "build_item_similarity.py"


def main() -> None:
    parser = argparse.ArgumentParser(description="ItemCF recommendation job")
    parser.add_argument("--days", type=int, default=30)
    parser.add_argument("--top-n", type=int, default=20)
    parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"))
    parser.add_argument("--mode", choices=["local", "spark"], default="local")
    parser.add_argument("--input-dir", default="/tmp/recommendation")
    parser.add_argument("--output-dir", default="/tmp/recommendation")
    parser.add_argument("--hdfs-input", default="hdfs://master:9000/data/raw")
    parser.add_argument("--hdfs-output", default="hdfs://master:9000/data")
    parser.add_argument("--hdfs-base", default=None, help="Deprecated; kept for old commands")
    parser.add_argument("--jdbc-url", default=None, help="Deprecated; kept for old commands")
    parser.add_argument("--jdbc-user", default=None, help="Deprecated; kept for old commands")
    parser.add_argument("--jdbc-password", default=None, help="Deprecated; kept for old commands")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.dry_run:
        print(f"Dry run: would execute {TARGET} for date={args.date}, days={args.days}, top_n={args.top_n}")
        return

    cmd = [
        sys.executable,
        str(TARGET),
        "--mode",
        args.mode,
        "--date",
        args.date,
        "--days",
        str(args.days),
        "--top-n",
        str(args.top_n),
        "--input-dir",
        args.input_dir,
        "--output-dir",
        args.output_dir,
        "--hdfs-input",
        args.hdfs_input,
        "--hdfs-output",
        args.hdfs_output,
    ]
    raise SystemExit(subprocess.call(cmd))


if __name__ == "__main__":
    main()
