param(
    [string]$Date = "",
    [switch]$DryRun,
    [string]$LocalDir = "/tmp/recommendation",
    [string]$HdfsBase = "/data/raw",
    [string]$HadoopContainer = "master",
    [string]$BackendContainer = "shopping-backend"
)

if (-not $Date) {
    $Date = (Get-Date).ToUniversalTime().AddDays(-1).ToString("yyyy-MM-dd")
}

$eventsPartition = "$LocalDir/events/dt=$Date"
$reviewsPartition = "$LocalDir/reviews/dt=$Date"
$productsPartition = "$LocalDir/products/dt=$Date"
$hdfsEventsPartition = "$HdfsBase/events/dt=$Date"
$hdfsReviewsPartition = "$HdfsBase/reviews/dt=$Date"
$hdfsProductsPartition = "$HdfsBase/products/dt=$Date"

Write-Host "=== Export recommendation inputs to HDFS ==="
Write-Host "  Date:      $Date"
Write-Host "  Local dir: $LocalDir"
Write-Host "  HDFS base: $HdfsBase"

Write-Host ""
Write-Host "--- Step 1: Check Hadoop ---"
docker exec $HadoopContainer hdfs dfsadmin -report *> $null
if ($LASTEXITCODE -eq 0) {
    Write-Host "  [OK] Hadoop NameNode is reachable"
} else {
    Write-Host "  [WARN] Hadoop is not reachable. Export can still run locally."
}

Write-Host ""
Write-Host "--- Step 2: Export PostgreSQL inputs ---"
if ($DryRun) {
    Write-Host "  [DRY-RUN] docker cp .\scripts\export_recommendation_events.py ${BackendContainer}:/tmp/export_recommendation_events.py"
    Write-Host "  [DRY-RUN] docker exec $BackendContainer python /tmp/export_recommendation_events.py --date $Date --output-dir $LocalDir"
    Write-Host "  [DRY-RUN] upload $eventsPartition -> $hdfsEventsPartition"
    Write-Host "  [DRY-RUN] upload $reviewsPartition -> $hdfsReviewsPartition"
    Write-Host "  [DRY-RUN] upload $productsPartition -> $hdfsProductsPartition"
    exit 0
}

docker cp ".\scripts\export_recommendation_events.py" "${BackendContainer}:/tmp/export_recommendation_events.py"
if ($LASTEXITCODE -ne 0) { throw "Failed to copy export script into $BackendContainer" }

docker exec `
    -e DATABASE_URL="postgresql://shopping_user:shopping_password@postgres:5432/shopping" `
    $BackendContainer python /tmp/export_recommendation_events.py `
    --date $Date --output-dir $LocalDir
if ($LASTEXITCODE -ne 0) {
    throw "Export failed inside $BackendContainer"
}
docker exec $BackendContainer rm -f /tmp/export_recommendation_events.py

Write-Host ""
Write-Host "--- Step 3: Verify local output in backend container ---"
docker exec $BackendContainer test -f "$eventsPartition/events.jsonl"
if ($LASTEXITCODE -ne 0) { throw "Missing $eventsPartition/events.jsonl" }
docker exec $BackendContainer test -f "$reviewsPartition/reviews.jsonl"
if ($LASTEXITCODE -ne 0) { throw "Missing $reviewsPartition/reviews.jsonl" }
docker exec $BackendContainer test -f "$productsPartition/products.jsonl"
if ($LASTEXITCODE -ne 0) { throw "Missing $productsPartition/products.jsonl" }

$eventCount = docker exec $BackendContainer sh -lc "wc -l < '$eventsPartition/events.jsonl'"
$reviewCount = docker exec $BackendContainer sh -lc "wc -l < '$reviewsPartition/reviews.jsonl'"
$productCount = docker exec $BackendContainer sh -lc "wc -l < '$productsPartition/products.jsonl'"
Write-Host "  [OK] events.jsonl rows=$eventCount"
Write-Host "  [OK] reviews.jsonl rows=$reviewCount"
Write-Host "  [OK] products.jsonl rows=$productCount"

Write-Host ""
Write-Host "--- Step 4: Upload to HDFS ---"
docker exec $HadoopContainer hdfs dfs -mkdir -p $hdfsEventsPartition $hdfsReviewsPartition $hdfsProductsPartition
if ($LASTEXITCODE -ne 0) { throw "Failed to create HDFS partitions" }

docker cp "${BackendContainer}:$eventsPartition/events.jsonl" ".\tmp_events_$Date.jsonl"
docker cp "${BackendContainer}:$eventsPartition/_SUCCESS" ".\tmp_events_SUCCESS_$Date"
docker cp "${BackendContainer}:$eventsPartition/_METADATA.json" ".\tmp_events_METADATA_$Date.json"
docker cp "${BackendContainer}:$reviewsPartition/reviews.jsonl" ".\tmp_reviews_$Date.jsonl"
docker cp "${BackendContainer}:$reviewsPartition/_SUCCESS" ".\tmp_reviews_SUCCESS_$Date"
docker cp "${BackendContainer}:$reviewsPartition/_METADATA.json" ".\tmp_reviews_METADATA_$Date.json"
docker cp "${BackendContainer}:$productsPartition/products.jsonl" ".\tmp_products_$Date.jsonl"
docker cp "${BackendContainer}:$productsPartition/_SUCCESS" ".\tmp_products_SUCCESS_$Date"
docker cp "${BackendContainer}:$productsPartition/_METADATA.json" ".\tmp_products_METADATA_$Date.json"

docker cp ".\tmp_events_$Date.jsonl" "${HadoopContainer}:/tmp/events_$Date.jsonl"
docker cp ".\tmp_events_SUCCESS_$Date" "${HadoopContainer}:/tmp/events_SUCCESS_$Date"
docker cp ".\tmp_events_METADATA_$Date.json" "${HadoopContainer}:/tmp/events_METADATA_$Date.json"
docker cp ".\tmp_reviews_$Date.jsonl" "${HadoopContainer}:/tmp/reviews_$Date.jsonl"
docker cp ".\tmp_reviews_SUCCESS_$Date" "${HadoopContainer}:/tmp/reviews_SUCCESS_$Date"
docker cp ".\tmp_reviews_METADATA_$Date.json" "${HadoopContainer}:/tmp/reviews_METADATA_$Date.json"
docker cp ".\tmp_products_$Date.jsonl" "${HadoopContainer}:/tmp/products_$Date.jsonl"
docker cp ".\tmp_products_SUCCESS_$Date" "${HadoopContainer}:/tmp/products_SUCCESS_$Date"
docker cp ".\tmp_products_METADATA_$Date.json" "${HadoopContainer}:/tmp/products_METADATA_$Date.json"

Remove-Item -Force ".\tmp_events_$Date.jsonl", ".\tmp_events_SUCCESS_$Date", ".\tmp_events_METADATA_$Date.json", ".\tmp_reviews_$Date.jsonl", ".\tmp_reviews_SUCCESS_$Date", ".\tmp_reviews_METADATA_$Date.json", ".\tmp_products_$Date.jsonl", ".\tmp_products_SUCCESS_$Date", ".\tmp_products_METADATA_$Date.json"

docker exec $HadoopContainer hdfs dfs -put -f "/tmp/events_$Date.jsonl" "$hdfsEventsPartition/events.jsonl"
docker exec $HadoopContainer hdfs dfs -put -f "/tmp/events_SUCCESS_$Date" "$hdfsEventsPartition/_SUCCESS"
docker exec $HadoopContainer hdfs dfs -put -f "/tmp/events_METADATA_$Date.json" "$hdfsEventsPartition/_METADATA.json"
docker exec $HadoopContainer hdfs dfs -put -f "/tmp/reviews_$Date.jsonl" "$hdfsReviewsPartition/reviews.jsonl"
docker exec $HadoopContainer hdfs dfs -put -f "/tmp/reviews_SUCCESS_$Date" "$hdfsReviewsPartition/_SUCCESS"
docker exec $HadoopContainer hdfs dfs -put -f "/tmp/reviews_METADATA_$Date.json" "$hdfsReviewsPartition/_METADATA.json"
docker exec $HadoopContainer hdfs dfs -put -f "/tmp/products_$Date.jsonl" "$hdfsProductsPartition/products.jsonl"
docker exec $HadoopContainer hdfs dfs -put -f "/tmp/products_SUCCESS_$Date" "$hdfsProductsPartition/_SUCCESS"
docker exec $HadoopContainer hdfs dfs -put -f "/tmp/products_METADATA_$Date.json" "$hdfsProductsPartition/_METADATA.json"
docker exec $HadoopContainer rm -f "/tmp/events_$Date.jsonl" "/tmp/events_SUCCESS_$Date" "/tmp/events_METADATA_$Date.json" "/tmp/reviews_$Date.jsonl" "/tmp/reviews_SUCCESS_$Date" "/tmp/reviews_METADATA_$Date.json" "/tmp/products_$Date.jsonl" "/tmp/products_SUCCESS_$Date" "/tmp/products_METADATA_$Date.json"

Write-Host ""
Write-Host "--- Step 5: Verify HDFS ---"
docker exec $HadoopContainer hdfs dfs -ls "$hdfsEventsPartition/"
docker exec $HadoopContainer hdfs dfs -ls "$hdfsReviewsPartition/"
docker exec $HadoopContainer hdfs dfs -ls "$hdfsProductsPartition/"

Write-Host ""
Write-Host "=== Export complete ==="
Write-Host "  Events HDFS:  $hdfsEventsPartition/"
Write-Host "  Reviews HDFS: $hdfsReviewsPartition/"
Write-Host "  Products HDFS: $hdfsProductsPartition/"
