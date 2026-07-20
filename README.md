# Shopping Web

Docker-first ecommerce demo with a separated FastAPI backend, Next.js frontend, PostgreSQL, MinIO object storage, and a Hadoop/Spark recommendation pipeline.

The current recommendation flow is:

```text
PostgreSQL events/reviews/products
  -> JSONL export
  -> HDFS raw partitions
  -> Spark recommendation jobs
  -> HDFS recommendation output
  -> PostgreSQL recommendation_results
  -> frontend hall recommendations
```

## Requirements

- Docker Desktop
- Git
- PowerShell on Windows, or Bash on macOS/Linux/WSL
- At least 8 GB RAM available to Docker is recommended when running Hadoop and Spark together

No local Python or Node setup is required for the normal path. Backend and frontend both run in Docker containers.

## Clone

```powershell
git clone git@github.com:Leamon-Lee/shopping-web.git
cd shopping-web
```

If SSH is not configured:

```powershell
git clone https://github.com/Leamon-Lee/shopping-web.git
cd shopping-web
```

## Quick Start: Storefront + Backend

Start PostgreSQL, MinIO, backend, and frontend:

```powershell
docker compose up -d
```

Import the seed catalog into PostgreSQL and upload product images/data into MinIO:

```powershell
docker compose --profile seed run --rm seed
```

Open:

- Frontend: http://localhost:8000
- Backend API docs: http://localhost:8001/docs
- Backend health: http://localhost:8001/health
- MinIO console: http://localhost:9001

Default local services:

| Service | URL / Port |
| --- | --- |
| Frontend | http://localhost:8000 |
| Backend | http://localhost:8001 |
| PostgreSQL | localhost:5432 |
| MinIO S3 | http://localhost:9000 |
| MinIO console | http://localhost:9001 |

Useful checks:

```powershell
Invoke-RestMethod http://localhost:8001/health
(Invoke-RestMethod http://localhost:8001/products).Count
Invoke-RestMethod http://localhost:8001/hall
```

## Frontend And Backend Are Split

The root compose file includes separate compose files:

```text
docker-compose.postgres.yml
docker-compose.minio.yml
docker-compose.backend.yml
docker-compose.frontend.yml
```

Run them separately if needed:

```powershell
docker compose -f docker-compose.postgres.yml up -d
docker compose -f docker-compose.minio.yml up -d
docker compose -f docker-compose.backend.yml up -d
docker compose -f docker-compose.frontend.yml up -d
```

The frontend talks to the backend through `NEXT_PUBLIC_BACKEND_URL=http://localhost:8001`.

## Start Hadoop And Spark

Create the shared Hadoop network once:

```powershell
docker network create hadoop
```

If it already exists, Docker will report that; it is safe to continue.

Start Hadoop HDFS/YARN:

```powershell
docker compose -f docker-compose.hadoop.yml up -d --build
```

Start Spark standalone:

```powershell
docker compose -f docker-compose.spark.yml up -d
```

Open:

- HDFS NameNode: http://localhost:9870
- YARN ResourceManager: http://localhost:8088
- Spark Master: http://localhost:8080
- Spark Worker: http://localhost:8081

Verify distributed storage has two DataNodes:

```powershell
docker exec master hdfs dfsadmin -report
```

You should see:

```text
Live datanodes (2)
Hostname: slaver1
Hostname: slaver2
```

Allow Spark to write recommendation output into `/data`:

```powershell
docker exec master hdfs dfs -mkdir -p /data
docker exec master hdfs dfs -chmod -R 777 /data
```

## Run Hadoop Recommendation Pipeline

Set a date. Use today's date when testing new clicks/reviews:

```powershell
$DATE = "2026-07-14"
```

Export recommendation inputs from PostgreSQL and upload them to HDFS:

```powershell
.\scripts\hdfs_upload.ps1 -Date $DATE
```

This creates:

```text
/data/raw/events/dt=YYYY-MM-DD/events.jsonl
/data/raw/reviews/dt=YYYY-MM-DD/reviews.jsonl
/data/raw/products/dt=YYYY-MM-DD/products.jsonl
```

Run the Spark recommendation stage:

```powershell
docker exec spark-master sh -lc "/opt/spark/bin/spark-submit --master spark://spark-master:7077 /app/spark/jobs/recommendations/build_user_recommendations.py --mode spark --date $DATE --days 1 --top-n 20 --hdfs-input hdfs://master:9000/data/raw --hdfs-output hdfs://master:9000/data"
```

Verify HDFS output:

```powershell
docker exec master hdfs dfs -ls /data/recommendations/user_recommendations/dt=$DATE
docker exec master sh -lc "hdfs dfs -cat /data/recommendations/user_recommendations/dt=$DATE/part-*.json | head -1"
```

Copy Spark output back to a local import folder:

```powershell
New-Item -ItemType Directory -Force "tmp/recommendation/recommendations/user_recommendations/dt=$DATE" | Out-Null
docker exec master sh -lc "hdfs dfs -cat /data/recommendations/user_recommendations/dt=$DATE/part-*.json" | Set-Content -Encoding UTF8 "tmp/recommendation/recommendations/user_recommendations/dt=$DATE/part-00000.jsonl"
```

Import recommendations into PostgreSQL:

```powershell
docker run --rm --network shopping-net -v "${PWD}:/workspace" -w /workspace python:3.12-slim sh -lc "pip install --no-cache-dir psycopg2-binary && DATABASE_URL=postgresql://shopping_user:shopping_password@shopping-postgres:5432/shopping python scripts/import_recommendations.py --date $DATE --input-dir /workspace/tmp/recommendation --types user_recs"
```

For a live demo loop that repeats upload -> Spark -> import every 5 seconds:

```powershell
.\scripts\recommendation_loop.ps1 -Date $DATE -IntervalSeconds 5
```

Run a single full pipeline cycle with the same script:

```powershell
.\scripts\recommendation_loop.ps1 -Date $DATE -Once
```

Verify the backend is serving Hadoop recommendations:

```powershell
$r = Invoke-RestMethod "http://localhost:8001/recommendations/users/leamonlee%40mail.com"
$r.items | Select-Object -First 8 @{n="name";e={$_.product.name}}, algorithm, reason, score | Format-Table -AutoSize
```

Expected algorithm:

```text
hadoop_commerce_v1
```

Open the customer hall:

```text
http://localhost:8000/customer/leamonlee%40mail.com/hall
```

After a user clicks product cards, export the same date again, rerun Spark, import again, and refresh the hall. The recommendation rail should shift toward similar categories/products.

## Bash Version Of The Pipeline

On macOS/Linux/WSL:

```bash
DATE=2026-07-14
docker compose up -d
docker compose --profile seed run --rm seed
docker network create hadoop || true
docker compose -f docker-compose.hadoop.yml up -d --build
docker compose -f docker-compose.spark.yml up -d
docker exec master hdfs dfs -mkdir -p /data
docker exec master hdfs dfs -chmod -R 777 /data
bash scripts/hdfs_upload.sh "$DATE"
docker exec spark-master sh -lc "/opt/spark/bin/spark-submit --master spark://spark-master:7077 /app/spark/jobs/recommendations/build_user_recommendations.py --mode spark --date $DATE --days 1 --top-n 20 --hdfs-input hdfs://master:9000/data/raw --hdfs-output hdfs://master:9000/data"
mkdir -p "tmp/recommendation/recommendations/user_recommendations/dt=$DATE"
docker exec master sh -lc "hdfs dfs -cat /data/recommendations/user_recommendations/dt=$DATE/part-*.json" > "tmp/recommendation/recommendations/user_recommendations/dt=$DATE/part-00000.jsonl"
docker run --rm --network shopping-net -v "$PWD:/workspace" -w /workspace python:3.12-slim sh -lc "pip install --no-cache-dir psycopg2-binary && DATABASE_URL=postgresql://shopping_user:shopping_password@shopping-postgres:5432/shopping python scripts/import_recommendations.py --date $DATE --input-dir /workspace/tmp/recommendation --types user_recs"
```

## Important URLs

| Page | URL |
| --- | --- |
| Shopping hall | http://localhost:8000/customer/leamonlee%40mail.com/hall |
| Customer panel | http://localhost:8000/customer/leamonlee%40mail.com |
| Cart | http://localhost:8000/cart |
| Login | http://localhost:8000/auth/login |
| Backend docs | http://localhost:8001/docs |
| HDFS UI | http://localhost:9870 |
| Spark UI | http://localhost:8080 |

## Data And Volumes

Persistent Docker volumes:

```text
shopping_postgres_data
shopping_minio_data
hadoop_namenode
hadoop_datanode1
hadoop_datanode2
hadoop_history
frontend_node_modules
frontend_next_cache
```

Reset everything:

```powershell
docker compose down -v
docker compose -f docker-compose.hadoop.yml down -v
docker compose -f docker-compose.spark.yml down -v
```

Then rerun the quick start.

## Troubleshooting

If the frontend is up but product images are missing, rerun:

```powershell
docker compose --profile seed run --rm seed
```

If Hadoop starts but Spark cannot write to HDFS:

```powershell
docker exec master hdfs dfs -chmod -R 777 /data
```

If the hall does not show personalized recommendations:

```powershell
docker exec shopping-postgres psql -U shopping_user -d shopping -c "select algorithm, scene, count(*) from recommendation_results group by algorithm, scene order by algorithm, scene;"
```

You should see `hadoop_commerce_v1` rows for `home`.

If a port is already in use, stop the previous containers:

```powershell
docker ps
docker compose down
```

## Stop

```powershell
docker compose down
docker compose -f docker-compose.spark.yml down
docker compose -f docker-compose.hadoop.yml down
```
