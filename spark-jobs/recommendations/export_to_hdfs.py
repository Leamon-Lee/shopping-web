"""Compatibility wrapper for exporting recommendation events.

The current pipeline exports JSONL partitions locally, then `scripts/hdfs_upload.sh`
can upload them to HDFS. This wrapper keeps the legacy command path runnable.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / "scripts" / "export_recommendation_events.py"


def main() -> None:
    parser = argparse.ArgumentParser(description="Export events for recommendation jobs")
    parser.add_argument("--date", default=(datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"))
    parser.add_argument("--output-dir", default="/tmp/recommendation")
    parser.add_argument("--limit", type=int, default=1_000_000)
    parser.add_argument("--jdbc-url", default=None, help="Deprecated; use DATABASE_URL instead")
    parser.add_argument("--jdbc-user", default=None, help="Deprecated; use DATABASE_URL instead")
    parser.add_argument("--jdbc-password", default=None, help="Deprecated; use DATABASE_URL instead")
    parser.add_argument("--hdfs-base", default=None, help="Deprecated; use scripts/hdfs_upload.sh")
    args = parser.parse_args()

    cmd = [
        sys.executable,
        str(TARGET),
        "--date",
        args.date,
        "--output-dir",
        args.output_dir,
        "--limit",
        str(args.limit),
    ]
    raise SystemExit(subprocess.call(cmd))


if __name__ == "__main__":
    main()
