# Online Shopping System

Ecommerce workspace with a FastAPI backend and a Next.js storefront frontend.

## Project layout

- `backend/online_shopping/domain/entities`: business entities
- `backend/online_shopping/domain/value_objects`: validated value objects
- `backend/online_shopping/domain/enums`: status enums
- `backend/online_shopping/domain/interfaces`: domain contracts
- `backend/online_shopping/services`: application services
- `backend/online_shopping/api`: FastAPI app, schemas, routers, and in-memory API store
- `frontend`: Next.js storefront
- `docs/design`: PlantUML design documents

## Run locally

Use two terminals: one for FastAPI and one for Next.js.

### Backend

```powershell
cd backend
python -m pip install -r requirements.txt
$env:PYTHONPATH = "."
python main.py
```

The FastAPI app is exposed as `online_shopping.api.app:app` and runs on port `8001`.

API docs: `http://localhost:8001/docs`

### Frontend

Create a local env file from the example:

```powershell
Copy-Item frontend\.env.local.example frontend\.env.local
```

Required local values:

```text
NEXT_PUBLIC_BACKEND_URL=http://localhost:8001
NEXT_PUBLIC_BASE_URL=http://localhost:8000
NEXT_PUBLIC_DEFAULT_REGION=cn
```

Start the storefront:

```powershell
cd frontend
corepack enable
corepack yarn install
corepack yarn dev
```

Storefront: `http://localhost:8000/`

## Verified Run Flow

Start Docker Desktop first, then run the stack from the repository root.

Start infrastructure services:

```cmd
docker compose up -d postgres minio minio-init
```

Import CSV catalog data into PostgreSQL and MinIO:

```cmd
docker compose --profile seed run --rm seed
```

Expected seed summary:

```text
CSV loaded: 41 categories, 302 products, 135 images, 850 variants
Inserted 301 products
Import complete!
```

Start the backend and frontend:

```cmd
docker compose up -d
```

Open:

- Storefront home: `http://localhost:8000/`
- Shop: `http://localhost:8000/shop`
- Cart: `http://localhost:8000/cart`
- Admin panel: `http://localhost:8000/admin`
- Manager panel: `http://localhost:8000/manager`
- Customer panel: `http://localhost:8000/customer`
- Backend docs: `http://localhost:8001/docs`
- Backend health: `http://localhost:8001/health`
- MinIO console: `http://localhost:9001`

Verify the backend is using imported database data:

```powershell
(Invoke-RestMethod http://localhost:8001/products).Count
```

The verified run returned `301`. The same import also creates active seed shops
from the CSV brand sources and links products through `shop_products`.

```powershell
$hall = Invoke-RestMethod http://localhost:8001/hall
$hall.shops.name -join ", "
$hall.products.Count
```

The verified hall run returned `Dell, Haier, Muji, Nike, Skechers, Under Armour,
Uniqlo, Xiaomi` and `301` products.

If container-side `pip install` fails because of package download timeouts or hash mismatches, keep PostgreSQL and MinIO in Docker and run the seed script with local Python:

```powershell
$env:PYTHONPATH = "$PWD\backend"
$env:DATABASE_URL = "postgresql+asyncpg://shopping_user:shopping_password@localhost:5432/shopping"
$env:MINIO_ENDPOINT = "localhost:9000"
$env:MINIO_ACCESS_KEY = "minioadmin"
$env:MINIO_SECRET_KEY = "minioadmin123"
$env:MINIO_BUCKET_PRODUCTS = "shopping-products"
$env:MINIO_BUCKET_DATA = "shopping-data"
$env:PUBLIC_MINIO_BASE_URL = "http://localhost:9000"
python import_csv_data.py
```

Then run the backend locally against the Docker database:

```powershell
$env:PYTHONPATH = "$PWD\backend"
$env:DATABASE_URL = "postgresql+asyncpg://shopping_user:shopping_password@localhost:5432/shopping"
$env:MINIO_ENDPOINT = "localhost:9000"
$env:MINIO_ACCESS_KEY = "minioadmin"
$env:MINIO_SECRET_KEY = "minioadmin123"
$env:MINIO_BUCKET_PRODUCTS = "shopping-products"
$env:MINIO_BUCKET_DATA = "shopping-data"
$env:PUBLIC_MINIO_BASE_URL = "http://localhost:9000"
python -m uvicorn online_shopping.api.app:app --host 0.0.0.0 --port 8001
```

In another terminal, run the frontend locally:

```powershell
cd frontend
$env:NEXT_PUBLIC_BACKEND_URL = "http://localhost:8001"
$env:NEXT_PUBLIC_BASE_URL = "http://localhost:8000"
$env:NEXT_PUBLIC_DEFAULT_REGION = "cn"
corepack enable
yarn dev --hostname 0.0.0.0
```

This fallback was verified with Docker PostgreSQL/MinIO plus local backend/frontend:

```text
GET http://localhost:8001/products -> 301 products
GET http://localhost:8001/hall -> 8 shops, 301 products
GET http://localhost:8001/shop?shop=nike -> 50 Nike products
GET http://localhost:8000/ -> 200 OK
GET http://localhost:8000/hall -> 200 OK
GET http://localhost:8000/shop?shop=nike -> 200 OK
```

Stop the stack:

```cmd
docker compose down
```

## Run with Split Docker Compose Files

Start PostgreSQL first if you want the database container available:

```cmd
docker compose -f docker-compose.postgres.yml up -d
```

Start the FastAPI backend:

```cmd
docker compose -f docker-compose.backend.yml up -d
```

Start the Next.js frontend:

```cmd
docker compose -f docker-compose.frontend.yml up -d
```

```cmd
docker compose -f docker-compose.minio.yml up -d
```

Docker URLs:

- Frontend: `http://localhost:8000/`
- Backend docs: `http://localhost:8001/docs`
- PostgreSQL: `localhost:5432`

Stop containers:

```cmd
docker compose -f docker-compose.frontend.yml down
docker compose -f docker-compose.backend.yml down
docker compose -f docker-compose.postgres.yml down
```

## Backend-Native API

The backend keeps the existing OOP/domain model under `backend/online_shopping/domain`.
The frontend uses backend-native field names and calls FastAPI routes directly.

## Frontend Route Map

The frontend route structure follows the role-based navigation below:

```text
/
├── /hall
├── /sign-in
│   ├── /customer
│   ├── /manager
│   └── /admin
├── /customer/:username
│   ├── /hall
│   ├── /profile
│   ├── /cart
│   ├── /orders
│   ├── /orders/:orderId
│   ├── /payment
│   ├── /wishlist
│   ├── /reviews
│   └── /settings
├── /manager/:username
│   ├── /dashboard
│   ├── /shop/apply
│   ├── /shop
│   ├── /shop/:shopId
│   ├── /products
│   ├── /products/create
│   ├── /products/:productId/edit
│   ├── /orders
│   ├── /orders/:orderId
│   ├── /analytics
│   ├── /income
│   └── /settings
└── /admin/:username
    ├── /dashboard
    ├── /shops
    ├── /shops/pending
    ├── /shops/:shopId
    ├── /products
    ├── /products/pending
    ├── /users
    ├── /users/:userId
    ├── /categories
    ├── /reports
    └── /settings
```

Core routes include:

- `GET /regions`
- `GET /shop`
- `GET /shop/{product_name_or_slug}`
- `GET /shop/categories`
- `GET /cart`
- `POST /cart/items`
- `PATCH /cart/items/{product_name}`
- `DELETE /cart/items/{product_name}`
- `GET /admin`
- `GET /manager`
- `GET /customer`
- `GET /orders`
- `POST /orders`
- `GET /orders/{order_number}`
- `POST /payments/process`
