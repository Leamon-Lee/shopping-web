#!/usr/bin/env bash
# Export recommendation inputs and upload them to HDFS.
#
# Usage:
#   bash scripts/hdfs_upload.sh 2026-07-13
#   bash scripts/hdfs_upload.sh 2026-07-13 --dry-run
#
# HDFS layout:
#   /data/raw/events/dt=YYYY-MM-DD/events.jsonl
#   /data/raw/reviews/dt=YYYY-MM-DD/reviews.jsonl
#   /data/raw/products/dt=YYYY-MM-DD/products.jsonl

set -euo pipefail

DATE="${1:-$(python3 -c 'from datetime import datetime,timedelta; print((datetime.utcnow()-timedelta(days=1)).strftime("%Y-%m-%d"))' 2>/dev/null || echo '2026-07-12')}"
DRY_RUN="${2:-}"
LOCAL_DIR="${LOCAL_DIR:-/tmp/recommendation}"
HDFS_BASE="${HDFS_BASE:-/data/raw}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY_SCRIPT="${SCRIPT_DIR}/export_recommendation_events.py"
HADOOP_CONTAINER="${HADOOP_CONTAINER:-master}"
BACKEND_CONTAINER="${BACKEND_CONTAINER:-shopping-backend}"

EVENTS_PARTITION="${LOCAL_DIR}/events/dt=${DATE}"
REVIEWS_PARTITION="${LOCAL_DIR}/reviews/dt=${DATE}"
PRODUCTS_PARTITION="${LOCAL_DIR}/products/dt=${DATE}"
HDFS_EVENTS_PARTITION="${HDFS_BASE}/events/dt=${DATE}"
HDFS_REVIEWS_PARTITION="${HDFS_BASE}/reviews/dt=${DATE}"
HDFS_PRODUCTS_PARTITION="${HDFS_BASE}/products/dt=${DATE}"

echo "=== Export recommendation inputs to HDFS ==="
echo "  Date:      ${DATE}"
echo "  Local dir: ${LOCAL_DIR}"
echo "  HDFS base: ${HDFS_BASE}"
echo "  Hadoop:    ${HADOOP_CONTAINER}"

echo ""
echo "--- Step 1: Check Hadoop ---"
if docker exec "${HADOOP_CONTAINER}" hdfs dfsadmin -report >/dev/null 2>&1; then
    echo "  [OK] Hadoop NameNode is reachable"
else
    echo "  [WARN] Hadoop is not reachable. Files will remain local if upload is attempted."
fi

echo ""
echo "--- Step 2: Export PostgreSQL inputs ---"
if [[ "${DRY_RUN}" == "--dry-run" ]]; then
    echo "  [DRY-RUN] python ${PY_SCRIPT} --date ${DATE} --output-dir ${LOCAL_DIR}"
    echo "  [DRY-RUN] upload ${EVENTS_PARTITION}/ -> ${HDFS_EVENTS_PARTITION}/"
    echo "  [DRY-RUN] upload ${REVIEWS_PARTITION}/ -> ${HDFS_REVIEWS_PARTITION}/"
    echo "  [DRY-RUN] upload ${PRODUCTS_PARTITION}/ -> ${HDFS_PRODUCTS_PARTITION}/"
    exit 0
fi

OUTPUT_IN_BACKEND=0
if docker exec "${BACKEND_CONTAINER}" python --version >/dev/null 2>&1; then
    echo "  Running inside ${BACKEND_CONTAINER} container..."
    docker cp "${PY_SCRIPT}" "${BACKEND_CONTAINER}:/tmp/export_recommendation_events.py"
    docker exec -e DATABASE_URL="postgresql://shopping_user:shopping_password@postgres:5432/shopping" \
        "${BACKEND_CONTAINER}" python /tmp/export_recommendation_events.py \
        --date "${DATE}" --output-dir "${LOCAL_DIR}"
    docker exec "${BACKEND_CONTAINER}" rm -f /tmp/export_recommendation_events.py
    OUTPUT_IN_BACKEND=1
else
    echo "  Running locally..."
    python "${PY_SCRIPT}" --date "${DATE}" --output-dir "${LOCAL_DIR}"
fi

echo ""
echo "--- Step 3: Verify local output ---"
if [[ "${OUTPUT_IN_BACKEND}" == "1" ]]; then
    docker exec "${BACKEND_CONTAINER}" test -f "${EVENTS_PARTITION}/events.jsonl"
    docker exec "${BACKEND_CONTAINER}" test -f "${REVIEWS_PARTITION}/reviews.jsonl"
    docker exec "${BACKEND_CONTAINER}" test -f "${PRODUCTS_PARTITION}/products.jsonl"
    EVENT_COUNT=$(docker exec "${BACKEND_CONTAINER}" sh -lc "wc -l < '${EVENTS_PARTITION}/events.jsonl'")
    REVIEW_COUNT=$(docker exec "${BACKEND_CONTAINER}" sh -lc "wc -l < '${REVIEWS_PARTITION}/reviews.jsonl'")
    PRODUCT_COUNT=$(docker exec "${BACKEND_CONTAINER}" sh -lc "wc -l < '${PRODUCTS_PARTITION}/products.jsonl'")
else
    if [[ ! -f "${EVENTS_PARTITION}/events.jsonl" ]]; then
        echo "  [FAIL] Missing ${EVENTS_PARTITION}/events.jsonl"
        exit 1
    fi
    if [[ ! -f "${REVIEWS_PARTITION}/reviews.jsonl" ]]; then
        echo "  [FAIL] Missing ${REVIEWS_PARTITION}/reviews.jsonl"
        exit 1
    fi
    if [[ ! -f "${PRODUCTS_PARTITION}/products.jsonl" ]]; then
        echo "  [FAIL] Missing ${PRODUCTS_PARTITION}/products.jsonl"
        exit 1
    fi
    EVENT_COUNT=$(wc -l < "${EVENTS_PARTITION}/events.jsonl")
    REVIEW_COUNT=$(wc -l < "${REVIEWS_PARTITION}/reviews.jsonl")
    PRODUCT_COUNT=$(wc -l < "${PRODUCTS_PARTITION}/products.jsonl")
fi
echo "  [OK] events.jsonl rows=${EVENT_COUNT}"
echo "  [OK] reviews.jsonl rows=${REVIEW_COUNT}"
echo "  [OK] products.jsonl rows=${PRODUCT_COUNT}"

echo ""
echo "--- Step 4: Upload to HDFS ---"
if docker exec "${HADOOP_CONTAINER}" hdfs dfsadmin -report >/dev/null 2>&1; then
    docker exec "${HADOOP_CONTAINER}" hdfs dfs -mkdir -p "${HDFS_EVENTS_PARTITION}" "${HDFS_REVIEWS_PARTITION}" "${HDFS_PRODUCTS_PARTITION}"

    TMP_COPY_DIR="$(mktemp -d)"
    trap 'rm -rf "${TMP_COPY_DIR}"' EXIT
    if [[ "${OUTPUT_IN_BACKEND}" == "1" ]]; then
        docker cp "${BACKEND_CONTAINER}:${EVENTS_PARTITION}/events.jsonl" "${TMP_COPY_DIR}/events.jsonl"
        docker cp "${BACKEND_CONTAINER}:${EVENTS_PARTITION}/_SUCCESS" "${TMP_COPY_DIR}/events_SUCCESS"
        docker cp "${BACKEND_CONTAINER}:${EVENTS_PARTITION}/_METADATA.json" "${TMP_COPY_DIR}/events_METADATA.json"
        docker cp "${BACKEND_CONTAINER}:${REVIEWS_PARTITION}/reviews.jsonl" "${TMP_COPY_DIR}/reviews.jsonl"
        docker cp "${BACKEND_CONTAINER}:${REVIEWS_PARTITION}/_SUCCESS" "${TMP_COPY_DIR}/reviews_SUCCESS"
        docker cp "${BACKEND_CONTAINER}:${REVIEWS_PARTITION}/_METADATA.json" "${TMP_COPY_DIR}/reviews_METADATA.json"
        docker cp "${BACKEND_CONTAINER}:${PRODUCTS_PARTITION}/products.jsonl" "${TMP_COPY_DIR}/products.jsonl"
        docker cp "${BACKEND_CONTAINER}:${PRODUCTS_PARTITION}/_SUCCESS" "${TMP_COPY_DIR}/products_SUCCESS"
        docker cp "${BACKEND_CONTAINER}:${PRODUCTS_PARTITION}/_METADATA.json" "${TMP_COPY_DIR}/products_METADATA.json"
    else
        cp "${EVENTS_PARTITION}/events.jsonl" "${TMP_COPY_DIR}/events.jsonl"
        cp "${EVENTS_PARTITION}/_SUCCESS" "${TMP_COPY_DIR}/events_SUCCESS"
        cp "${EVENTS_PARTITION}/_METADATA.json" "${TMP_COPY_DIR}/events_METADATA.json"
        cp "${REVIEWS_PARTITION}/reviews.jsonl" "${TMP_COPY_DIR}/reviews.jsonl"
        cp "${REVIEWS_PARTITION}/_SUCCESS" "${TMP_COPY_DIR}/reviews_SUCCESS"
        cp "${REVIEWS_PARTITION}/_METADATA.json" "${TMP_COPY_DIR}/reviews_METADATA.json"
        cp "${PRODUCTS_PARTITION}/products.jsonl" "${TMP_COPY_DIR}/products.jsonl"
        cp "${PRODUCTS_PARTITION}/_SUCCESS" "${TMP_COPY_DIR}/products_SUCCESS"
        cp "${PRODUCTS_PARTITION}/_METADATA.json" "${TMP_COPY_DIR}/products_METADATA.json"
    fi

    docker cp "${TMP_COPY_DIR}/events.jsonl" "${HADOOP_CONTAINER}:/tmp/events_${DATE}.jsonl"
    docker cp "${TMP_COPY_DIR}/events_SUCCESS" "${HADOOP_CONTAINER}:/tmp/events_SUCCESS_${DATE}"
    docker cp "${TMP_COPY_DIR}/events_METADATA.json" "${HADOOP_CONTAINER}:/tmp/events_METADATA_${DATE}.json"
    docker cp "${TMP_COPY_DIR}/reviews.jsonl" "${HADOOP_CONTAINER}:/tmp/reviews_${DATE}.jsonl"
    docker cp "${TMP_COPY_DIR}/reviews_SUCCESS" "${HADOOP_CONTAINER}:/tmp/reviews_SUCCESS_${DATE}"
    docker cp "${TMP_COPY_DIR}/reviews_METADATA.json" "${HADOOP_CONTAINER}:/tmp/reviews_METADATA_${DATE}.json"
    docker cp "${TMP_COPY_DIR}/products.jsonl" "${HADOOP_CONTAINER}:/tmp/products_${DATE}.jsonl"
    docker cp "${TMP_COPY_DIR}/products_SUCCESS" "${HADOOP_CONTAINER}:/tmp/products_SUCCESS_${DATE}"
    docker cp "${TMP_COPY_DIR}/products_METADATA.json" "${HADOOP_CONTAINER}:/tmp/products_METADATA_${DATE}.json"

    docker exec "${HADOOP_CONTAINER}" hdfs dfs -put -f "/tmp/events_${DATE}.jsonl" "${HDFS_EVENTS_PARTITION}/events.jsonl"
    docker exec "${HADOOP_CONTAINER}" hdfs dfs -put -f "/tmp/events_SUCCESS_${DATE}" "${HDFS_EVENTS_PARTITION}/_SUCCESS"
    docker exec "${HADOOP_CONTAINER}" hdfs dfs -put -f "/tmp/events_METADATA_${DATE}.json" "${HDFS_EVENTS_PARTITION}/_METADATA.json"
    docker exec "${HADOOP_CONTAINER}" hdfs dfs -put -f "/tmp/reviews_${DATE}.jsonl" "${HDFS_REVIEWS_PARTITION}/reviews.jsonl"
    docker exec "${HADOOP_CONTAINER}" hdfs dfs -put -f "/tmp/reviews_SUCCESS_${DATE}" "${HDFS_REVIEWS_PARTITION}/_SUCCESS"
    docker exec "${HADOOP_CONTAINER}" hdfs dfs -put -f "/tmp/reviews_METADATA_${DATE}.json" "${HDFS_REVIEWS_PARTITION}/_METADATA.json"
    docker exec "${HADOOP_CONTAINER}" hdfs dfs -put -f "/tmp/products_${DATE}.jsonl" "${HDFS_PRODUCTS_PARTITION}/products.jsonl"
    docker exec "${HADOOP_CONTAINER}" hdfs dfs -put -f "/tmp/products_SUCCESS_${DATE}" "${HDFS_PRODUCTS_PARTITION}/_SUCCESS"
    docker exec "${HADOOP_CONTAINER}" hdfs dfs -put -f "/tmp/products_METADATA_${DATE}.json" "${HDFS_PRODUCTS_PARTITION}/_METADATA.json"

    docker exec "${HADOOP_CONTAINER}" rm -f \
        "/tmp/events_${DATE}.jsonl" "/tmp/events_SUCCESS_${DATE}" "/tmp/events_METADATA_${DATE}.json" \
        "/tmp/reviews_${DATE}.jsonl" "/tmp/reviews_SUCCESS_${DATE}" "/tmp/reviews_METADATA_${DATE}.json" \
        "/tmp/products_${DATE}.jsonl" "/tmp/products_SUCCESS_${DATE}" "/tmp/products_METADATA_${DATE}.json"

    echo "  [OK] Uploaded events, reviews, and products"
else
    echo "  [SKIP] Hadoop cluster not reachable. Local files are ready."
fi

echo ""
echo "--- Step 5: Verify HDFS ---"
docker exec "${HADOOP_CONTAINER}" hdfs dfs -ls "${HDFS_EVENTS_PARTITION}/" || true
docker exec "${HADOOP_CONTAINER}" hdfs dfs -ls "${HDFS_REVIEWS_PARTITION}/" || true
docker exec "${HADOOP_CONTAINER}" hdfs dfs -ls "${HDFS_PRODUCTS_PARTITION}/" || true

echo ""
echo "=== Export complete ==="
echo "  Events local:  ${EVENTS_PARTITION}/"
echo "  Reviews local: ${REVIEWS_PARTITION}/"
echo "  Products local: ${PRODUCTS_PARTITION}/"
echo "  Events HDFS:   ${HDFS_EVENTS_PARTITION}/"
echo "  Reviews HDFS:  ${HDFS_REVIEWS_PARTITION}/"
echo "  Products HDFS: ${HDFS_PRODUCTS_PARTITION}/"
