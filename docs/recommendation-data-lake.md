# Recommendation Data Lake — Directory Convention v1.0

## Overview

This document defines the HDFS directory layout for the shopping-web recommendation
system data pipeline. The pipeline ingests raw operational data from PostgreSQL,
cleans and transforms it, extracts features, and produces recommendation results.

All paths are relative to the HDFS root (`hdfs://master:9000`).

## Architecture

```
PostgreSQL (OLTP)
    │
    ├── export_recommendation_events.py (daily)
    │       │
    │       ▼
    │   /data/raw/events/dt=YYYY-MM-DD/
    │
    ├── (future) /data/raw/products/dt=YYYY-MM-DD/
    ├── (future) /data/raw/orders/dt=YYYY-MM-DD/
    │
    ▼
Spark ETL Jobs (itemcf.py, popular.py)
    │
    ├── /data/clean/events/dt=YYYY-MM-DD/        (deduped, validated)
    ├── /data/features/user_features/            (user embeddings)
    ├── /data/features/product_features/         (product embeddings)
    ├── /data/features/user_product_scores/      (ALS scores)
    │
    ▼
Recommendation Generation
    │
    ├── /data/recommendations/user_recs/         (per-user top-N)
    └── /data/recommendations/item_similar/      (item-item similarity)
            │
            ▼
        PostgreSQL (recommendation_cache table)
            │
            ▼
        FastAPI GET /recommendations
```

## Directory Reference

### Raw Layer (`/data/raw/`)

Source-of-truth snapshots from operational databases.
**Never modify raw data in place.** Always create new partitions.

| Path | Source Table | Partition | Format | Retention |
|---|---|---|---|---|
| `/data/raw/events/dt=YYYY-MM-DD/` | `user_behavior_events` | daily | JSONL | 90 days |
| `/data/raw/products/dt=YYYY-MM-DD/` | `products` (TODO) | daily | JSONL | 30 days |
| `/data/raw/orders/dt=YYYY-MM-DD/` | `orders`, `order_items` (TODO) | daily | JSONL | 365 days |

**Files per partition:**
```
/data/raw/events/dt=2026-07-13/
├── events.jsonl       # One JSON object per line
├── _SUCCESS           # Empty marker (Spark convention)
└── _METADATA.json     # Export metadata (count, timestamp, schema)
```

**Event fields (events.jsonl):**

| Field | Type | Description |
|---|---|---|
| `id` | UUID | Primary key |
| `event_type` | string | One of 11 types (see below) |
| `account_id` | UUID? | Authenticated user (nullable) |
| `user_email` | string? | User email at event time |
| `anonymous_id` | string? | Cross-session anonymous ID (localStorage) |
| `session_id` | string? | Session ID (sessionStorage) |
| `product_id` | UUID? | Product UUID |
| `product_name` | string? | Product name snapshot |
| `product_slug` | string? | Product slug snapshot |
| `shop_id` | UUID? | Shop UUID |
| `shop_name` | string? | Shop name snapshot |
| `category_id` | UUID? | Category UUID |
| `category_name` | string? | Category name snapshot |
| `query` | string? | Search query text |
| `quantity` | int? | Cart/order quantity |
| `price` | float? | Unit price at event time |
| `source_page` | string? | URL path (e.g., `/nike/nike-air-max`) |
| `metadata_json` | JSON | Extensible payload |
| `created_at` | timestamp | Event timestamp |

**Event types:**

| Value | Description | Typical source_page |
|---|---|---|
| `product_view` | Product detail page opened | `/shop-slug/product-slug` |
| `search` | User typed a search query | `/hall?q=...` |
| `add_to_cart` | Product added to cart | (any) |
| `remove_from_cart` | Product removed from cart | `/cart` |
| `checkout_start` | User entered checkout flow | `/checkout` |
| `order_created` | Order placed (before payment) | `/checkout` |
| `order_paid` | Payment completed | (after payment) |
| `favorite_product` | Product favorited (future) | (future) |
| `recommendation_impression` | Recommendation card seen | (any) |
| `recommendation_click` | Recommendation card clicked | (any) |
| `recommendation_add_to_cart` | Recommended product added to cart | (any) |

### Clean Layer (`/data/clean/`)

Deduplicated, validated, schema-enforced data.
Produced by Spark jobs after raw ingestion.

| Path | Description | Retention |
|---|---|---|
| `/data/clean/events/dt=YYYY-MM-DD/` | Validated events with consistent types | 90 days |

**Transformations:**
- Deduplicate by `id`
- Validate `event_type` against allowed set
- Coerce UUID fields to string
- Fill missing `anonymous_id` from session correlation
- Drop events older than retention window

### Feature Layer (`/data/features/`)

Derived features for ML model training.

| Path | Description | Format | Refresh |
|---|---|---|---|
| `/data/features/user_features/dt=YYYY-MM-DD/` | User embedding vectors, category affinities, recency scores | Parquet | Weekly |
| `/data/features/product_features/dt=YYYY-MM-DD/` | Product embedding vectors, popularity scores | Parquet | Weekly |
| `/data/features/user_product_scores/dt=YYYY-MM-DD/` | ALS user-item scores matrix | Parquet | Weekly |

### Recommendation Output (`/data/recommendations/`)

Final recommendation results, ready for import into PostgreSQL `recommendation_cache`.

| Path | Description | Format |
|---|---|---|
| `/data/recommendations/user_recs/dt=YYYY-MM-DD/` | Per-user top-N product recommendations | JSONL |
| `/data/recommendations/item_similar/dt=YYYY-MM-DD/` | Item-item similarity matrix (top 20 per product) | JSONL |

**user_recs format:**
```json
{"user_id": "...", "recs": [{"product_id": "...", "score": 0.95}, ...]}
```

**item_similar format:**
```json
{"product_id": "...", "similar": [{"product_id": "...", "score": 0.87}, ...]}
```

## Data Retention Policy

| Layer | Retention | Rationale |
|---|---|---|
| Raw events | 90 days | Same as real-time recommendation window |
| Raw orders | 365 days | Required for annual reporting |
| Clean layer | 90 days | Reconstructible from raw |
| Features | 90 days | Reconstructible from clean |
| Recommendations | 30 days | Refreshed daily; old recs are stale |

**Cleanup command:**
```bash
# Remove raw events older than 90 days
docker exec master hdfs dfs -rm -r -skipTrash /data/raw/events/dt=2026-04-*
```

## Privacy Notes

1. **No PII in raw events**: `user_email` is collected but should be hashed before
   sharing with analytics teams. Consider replacing with `user_id_hash` in clean layer.

2. **No session reconstruction**: `session_id` is a random UUID generated client-side
   and cannot be linked to server sessions or auth tokens.

3. **Anonymous ID rotation**: Users can clear `localStorage` to reset their
   `anonymous_id`. Analytics must handle ID churn.

4. **Data access control** (future):
   - Raw layer: data engineers + ML engineers
   - Clean layer: analysts + ML engineers
   - Features: ML engineers only
   - Recommendations: application layer (read-only from PostgreSQL)

5. **GDPR/CCPA compliance** (future):
   - Provide `DELETE /admin/data/user/{user_id}` endpoint
   - Spark job to scrub user data from all layers
   - Data retention audit log in `_METADATA.json`

## Export Commands

### Local export only
```bash
python scripts/export_recommendation_events.py --date 2026-07-13
```

### Export + HDFS upload
```bash
bash scripts/hdfs_upload.sh 2026-07-13
bash scripts/hdfs_upload.sh                    # yesterday (default)
bash scripts/hdfs_upload.sh 2026-07-13 --dry-run
```

### Manual HDFS verification
```bash
docker exec master hdfs dfs -ls /data/raw/events/dt=2026-07-13/
docker exec master hdfs dfs -cat /data/raw/events/dt=2026-07-13/events.jsonl | head -3
docker exec master hdfs dfs -du -h /data/raw/events/
```

### Spark ingestion (future)
```bash
# Read with Spark
events = spark.read.json("hdfs://master:9000/data/raw/events/dt=2026-07-13/events.jsonl")

# Or read a date range
events = spark.read.json("hdfs://master:9000/data/raw/events/dt=2026-07-1[0-9]/events.jsonl")
```

## Operational Schedule

| Job | Frequency | Trigger | Dependencies |
|---|---|---|---|
| `export_recommendation_events.py` | Daily 02:00 UTC | Cron / Airflow | PostgreSQL available |
| `hdfs_upload.sh` | Daily 02:30 UTC | Cron / Airflow | export script success |
| `itemcf.py` | Weekly Mon 04:00 | Cron / Airflow | 30 days of raw events in HDFS |
| `popular.py` | Daily 03:00 | Cron / Airflow | 7 days of raw events in HDFS |
