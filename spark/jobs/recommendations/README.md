# Spark Recommendation Jobs

Production-grade recommendation pipeline for the shopping-web multi-vendor platform.

## Architecture

```
HDFS: /data/raw/events/dt=YYYY-MM-DD/events.jsonl
    │
    ├── build_popular_products.py  ──→  /data/recommendations/popular_products/dt=YYYY-MM-DD/
    ├── build_user_preferences.py  ──→  /data/features/user_preferences/dt=YYYY-MM-DD/
    └── build_item_similarity.py   ──→  /data/recommendations/item_similar/dt=YYYY-MM-DD/
            │
            └──  import → PostgreSQL recommendation_cache  →  FastAPI GET /recommendations
```

## Job Reference

| Job | Description | Output |
|---|---|---|
| `build_popular_products.py` | Weighted event aggregation per product | `/data/recommendations/popular_products/` |
| `build_user_preferences.py` | Per-user category/shop/product affinity | `/data/features/user_preferences/` |
| `build_item_similarity.py` | User co-occurrence item-item similarity | `/data/recommendations/item_similar/` |
| `run_all.py` | Orchestrator — runs all stages sequentially | — |

## Event Weights

| Event Type | Weight |
|---|---|
| `product_view` | 1 |
| `search` | 2 |
| `recommendation_click` | 3 |
| `recommendation_add_to_cart` | 4 |
| `add_to_cart` | 5 |
| `favorite_product` | 6 |
| `order_created` | 8 |
| `order_paid` | 10 |

Time decay: `score = weight * exp(-days_since_event / 30)`

## Quick Start

### Local Mode (development — no Spark required)

```bash
# 1. Export events from PostgreSQL to local JSONL
python scripts/export_recommendation_events.py --date 2026-07-13

# 2. Run a single job
cd spark/jobs/recommendations
python build_popular_products.py --mode local --days 7 --top-n 20 --date 2026-07-13

# 3. Run full pipeline
python run_all.py --mode local --days 7 --top-n 20 --date 2026-07-13

# 4. Check output
cat /tmp/recommendation/recommendations/popular_products/dt=2026-07-13/part-00000.jsonl | python -m json.tool | head -30
```

### Spark Mode (production — requires Spark cluster)

```bash
# Prerequisites
# 1. Hadoop cluster running
docker compose -f docker-compose.hadoop.yml up -d

# 2. Spark cluster running (see docker-compose.spark.yml below)
docker compose -f docker-compose.spark.yml up -d

# 3. Events exported to HDFS
bash scripts/hdfs_upload.sh 2026-07-13

# Run single job via spark-submit
docker exec spark-master spark-submit \
    --master spark://spark-master:7077 \
    --deploy-mode client \
    --conf spark.hadoop.fs.defaultFS=hdfs://master:9000 \
    /app/spark/jobs/recommendations/build_popular_products.py \
    --mode spark --days 7 --top-n 20 --date 2026-07-13

# Run full pipeline
docker exec spark-master spark-submit \
    --master spark://spark-master:7077 \
    /app/spark/jobs/recommendations/run_all.py \
    --mode spark --days 7 --top-n 20 --date 2026-07-13

# Verify output
docker exec master hdfs dfs -cat \
    /data/recommendations/popular_products/dt=2026-07-13/part-00000.json | head -20
```

## Spark Cluster Setup

### Option A: Standalone Spark (docker-compose.spark.yml)

Create `docker-compose.spark.yml` in the project root:

```yaml
services:
  spark-master:
    image: bitnami/spark:3.5
    container_name: spark-master
    hostname: spark-master
    environment:
      - SPARK_MODE=master
      - SPARK_RPC_AUTHENTICATION_ENABLED=no
      - SPARK_RPC_ENCRYPTION_ENABLED=no
      - SPARK_LOCAL_STORAGE_ENCRYPTION_ENABLED=no
      - SPARK_SSL_ENABLED=no
    ports:
      - "8080:8080"
      - "7077:7077"
    volumes:
      - .:/app
    networks:
      - hadoop

  spark-worker:
    image: bitnami/spark:3.5
    container_name: spark-worker
    hostname: spark-worker
    environment:
      - SPARK_MODE=worker
      - SPARK_MASTER_URL=spark://spark-master:7077
      - SPARK_WORKER_MEMORY=2G
      - SPARK_WORKER_CORES=2
      - SPARK_RPC_AUTHENTICATION_ENABLED=no
      - SPARK_RPC_ENCRYPTION_ENABLED=no
      - SPARK_LOCAL_STORAGE_ENCRYPTION_ENABLED=no
      - SPARK_SSL_ENABLED=no
    depends_on:
      - spark-master
    ports:
      - "8081:8081"
    volumes:
      - .:/app
    networks:
      - hadoop

networks:
  hadoop:
    name: hadoop
    external: true
```

```bash
# Start Spark cluster
docker compose -f docker-compose.spark.yml up -d

# Verify
curl http://localhost:8080    # Spark Master UI
```

### Option B: Submit via spark-submit on the host

Install Spark 3.5 locally and configure `core-site.xml` to point to `hdfs://localhost:9000`.

```bash
spark-submit \
    --master local[*] \
    --conf spark.hadoop.fs.defaultFS=hdfs://localhost:9000 \
    build_popular_products.py --mode spark --days 7
```

## Output Schema

### popular_products
```json
{
    "product_id": "uuid",
    "product_name": "Nike Air Max",
    "product_slug": "nike-air-max",
    "category_id": "uuid",
    "category_name": "Shoes",
    "shop_id": "uuid",
    "shop_name": "Nike",
    "score": 42.5,
    "rank": 1,
    "dt": "2026-07-13"
}
```

### item_similar
```json
{
    "product_id": "uuid",
    "product_name": "Nike Air Max",
    "product_slug": "nike-air-max",
    "similar_product_id": "uuid",
    "similar_product_name": "Nike React",
    "score": 0.85,
    "reason": "Customers who viewed this also viewed",
    "dt": "2026-07-13"
}
```

### user_preferences
```json
{
    "user_key": "account-uuid or anonymous-id",
    "dt": "2026-07-13",
    "total_score": 128.5,
    "event_count": 45,
    "top_categories": [{"name": "Shoes", "score": 35.2}],
    "top_shops": [{"name": "Nike", "score": 28.1}],
    "top_products": [{"id": "uuid", "score": 12.0}],
    "price_range": {"min": 89.0, "max": 450.0}
}
```

## Verification

```bash
# 1. Insert test events
python -c "
import psycopg2
conn = psycopg2.connect('postgresql://shopping_user:shopping_password@localhost:5432/shopping')
conn.autocommit = True
cur = conn.cursor()
for i in range(10):
    cur.execute('INSERT INTO user_behavior_events (event_type, product_name, source_page) VALUES (%s,%s,%s)',
               ('product_view', f'Product-{i}', '/test'))
print('10 test events inserted')
conn.close()
"

# 2. Export
python scripts/export_recommendation_events.py --date $(date +%Y-%m-%d)

# 3. Run pipeline locally
cd spark/jobs/recommendations
python run_all.py --mode local --days 1 --date $(date +%Y-%m-%d)

# 4. Check output
cat /tmp/recommendation/recommendations/popular_products/dt=$(date +%Y-%m-%d)/part-00000.jsonl
```

## Migration path from Local → Spark

1. **Local mode**: Uses JSONL files from `scripts/export_recommendation_events.py`
2. **Spark mode with local files**: Set `--hdfs-input file:///tmp/recommendation`
3. **Full production**: Export to HDFS via `scripts/hdfs_upload.sh`, then Spark reads from HDFS

## Dependencies

| Mode | Requirements |
|---|---|
| local | Python 3.10+, no external packages (uses stdlib only) |
| spark | PySpark 3.5+, Hadoop client config, HDFS NameNode accessible |
| spark + HDFS | Bitnami Spark image + Hadoop docker compose |
