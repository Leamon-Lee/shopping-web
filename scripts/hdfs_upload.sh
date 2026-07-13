#!/usr/bin/env bash
# ==============================================================
# hdfs_upload.sh — Export events and upload to HDFS
#
# Prerequisites:
#   1. Docker containers running:
#        docker compose -f docker-compose.hadoop.yml up -d
#   2. Python 3 with psycopg2 or asyncpg installed
#      (or run inside the backend container)
#   3. HDFS NameNode accessible at hdfs://master:9000
#      (from within the hadoop network)
#
# Usage:
#   bash scripts/hdfs_upload.sh 2026-07-13
#   bash scripts/hdfs_upload.sh                    # yesterday
#   bash scripts/hdfs_upload.sh 2026-07-13 --dry-run
#
# HDFS layout:
#   /data/raw/events/dt=YYYY-MM-DD/events.jsonl
#   /data/raw/events/dt=YYYY-MM-DD/_SUCCESS
#   /data/raw/events/dt=YYYY-MM-DD/_METADATA.json
# ==============================================================
set -euo pipefail

DATE="${1:-$(date -u -d 'yesterday' +%Y-%m-%d 2>/dev/null || python3 -c 'from datetime import datetime,timedelta; print((datetime.utcnow()-timedelta(days=1)).strftime("%Y-%m-%d"))' 2>/dev/null || echo '2026-07-12')}"
DRY_RUN="${2:-}"
LOCAL_DIR="/tmp/recommendation"
HDFS_BASE="${HDFS_BASE:-/data/raw}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY_SCRIPT="${SCRIPT_DIR}/export_recommendation_events.py"
HADOOP_CONTAINER="${HADOOP_CONTAINER:-master}"

echo "=== Phase 2: Export events to HDFS ==="
echo "  Date:       ${DATE}"
echo "  Local dir:  ${LOCAL_DIR}"
echo "  HDFS base:  ${HDFS_BASE}"
echo "  Container:  ${HADOOP_CONTAINER}"

# ── Step 1: Check Hadoop cluster is running ────────────────────
echo ""
echo "--- Step 1: Check Hadoop ---"
if docker exec "${HADOOP_CONTAINER}" hdfs dfsadmin -report >/dev/null 2>&1; then
    echo "  [OK] Hadoop NameNode is reachable"
else
    echo "  [WARN] Hadoop cluster not reachable. Start with:"
    echo "    docker compose -f docker-compose.hadoop.yml up -d"
    echo "  Continuing with local export only..."
fi

# ── Step 2: Run the Python export script ───────────────────────
echo ""
echo "--- Step 2: Export events from PostgreSQL ---"

if [[ "${DRY_RUN}" == "--dry-run" ]]; then
    echo "  [DRY-RUN] Would run: python ${PY_SCRIPT} --date ${DATE} --output-dir ${LOCAL_DIR}"
    echo "  [DRY-RUN] Would upload: ${LOCAL_DIR}/events/dt=${DATE}/ → ${HDFS_BASE}/events/dt=${DATE}/"
    exit 0
fi

# Try running inside the backend container first (has DB access)
if docker exec shopping-backend python --version >/dev/null 2>&1; then
    echo "  Running inside shopping-backend container..."
    docker exec -e DATABASE_URL="postgresql+asyncpg://shopping_user:shopping_password@postgres:5432/shopping" \
        shopping-backend python /app/../scripts/export_recommendation_events.py \
        --date "${DATE}" --output-dir "${LOCAL_DIR}" || {
        echo "  [FALLBACK] Trying local Python..."
        python "${PY_SCRIPT}" --date "${DATE}" --output-dir "${LOCAL_DIR}"
    }
else
    echo "  Running locally..."
    python "${PY_SCRIPT}" --date "${DATE}" --output-dir "${LOCAL_DIR}"
fi

# ── Step 3: Check local output ─────────────────────────────────
PARTITION_DIR="${LOCAL_DIR}/events/dt=${DATE}"
echo ""
echo "--- Step 3: Verify local output ---"
if [[ -f "${PARTITION_DIR}/events.jsonl" ]]; then
    FILE_COUNT=$(wc -l < "${PARTITION_DIR}/events.jsonl")
    FILE_SIZE=$(du -h "${PARTITION_DIR}/events.jsonl" | cut -f1)
    echo "  [OK] ${PARTITION_DIR}/events.jsonl — ${FILE_COUNT} lines, ${FILE_SIZE}"
    echo "  First 2 lines:"
    head -2 "${PARTITION_DIR}/events.jsonl" | python -m json.tool 2>/dev/null || head -2 "${PARTITION_DIR}/events.jsonl"
else
    echo "  [FAIL] No events file found. Check PostgreSQL connectivity."
    exit 1
fi

# ── Step 4: Upload to HDFS ─────────────────────────────────────
echo ""
echo "--- Step 4: Upload to HDFS ---"

HDFS_PARTITION="${HDFS_BASE}/events/dt=${DATE}"

if docker exec "${HADOOP_CONTAINER}" hdfs dfsadmin -report >/dev/null 2>&1; then
    # Create HDFS directory
    docker exec "${HADOOP_CONTAINER}" hdfs dfs -mkdir -p "${HDFS_PARTITION}"

    # Copy files into the Hadoop container first, then put to HDFS
    # (docker exec doesn't support piping files directly to hdfs dfs -put -)
    echo "  Copying to HDFS via container ${HADOOP_CONTAINER}..."
    docker cp "${PARTITION_DIR}/events.jsonl" "${HADOOP_CONTAINER}:/tmp/events_${DATE}.jsonl"
    docker cp "${PARTITION_DIR}/_SUCCESS" "${HADOOP_CONTAINER}:/tmp/_SUCCESS_${DATE}"
    docker cp "${PARTITION_DIR}/_METADATA.json" "${HADOOP_CONTAINER}:/tmp/_METADATA_${DATE}.json"

    docker exec "${HADOOP_CONTAINER}" hdfs dfs -put -f "/tmp/events_${DATE}.jsonl" "${HDFS_PARTITION}/events.jsonl"
    docker exec "${HADOOP_CONTAINER}" hdfs dfs -put -f "/tmp/_SUCCESS_${DATE}" "${HDFS_PARTITION}/_SUCCESS"
    docker exec "${HADOOP_CONTAINER}" hdfs dfs -put -f "/tmp/_METADATA_${DATE}.json" "${HDFS_PARTITION}/_METADATA.json"

    # Cleanup temp files in container
    docker exec "${HADOOP_CONTAINER}" rm -f "/tmp/events_${DATE}.jsonl" "/tmp/_SUCCESS_${DATE}" "/tmp/_METADATA_${DATE}.json"

    echo "  [OK] Uploaded to ${HDFS_PARTITION}/"
else
    echo "  [SKIP] Hadoop cluster not reachable. Files are at ${PARTITION_DIR}/"
    echo "  Upload manually when cluster is ready:"
    echo "    docker cp ${PARTITION_DIR}/ ${HADOOP_CONTAINER}:/tmp/events_${DATE}/"
    echo "    docker exec ${HADOOP_CONTAINER} hdfs dfs -put /tmp/events_${DATE}/ ${HDFS_PARTITION}/"
fi

# ── Step 5: Verify in HDFS ─────────────────────────────────────
echo ""
echo "--- Step 5: Verify in HDFS ---"
if docker exec "${HADOOP_CONTAINER}" hdfs dfs -ls "${HDFS_PARTITION}/" 2>/dev/null; then
    echo "  [OK] HDFS files listed above"
else
    echo "  [INFO] Run manually to verify:"
    echo "    docker exec ${HADOOP_CONTAINER} hdfs dfs -ls ${HDFS_PARTITION}/"
fi

echo ""
echo "=== Export complete ==="
echo "  Local:  ${PARTITION_DIR}/"
echo "  HDFS:   ${HDFS_PARTITION}/"
