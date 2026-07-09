# 数据库与对象存储配置方案

## 一、现状分析

| 项目 | 当前状态 |
|------|----------|
| 关系型数据库 | PostgreSQL 16 (`docker-compose.postgres.yml`)，已有基础 schema |
| 后端存储 | **内存存储**（`backend/online_shopping/api/store.py`，数据存于 list/dict） |
| ORM / 驱动 | 无，直接操作 Pydantic schema 和 Python 内置数据结构 |
| 图片存储 | ProductImage 仅有 URL 字段，无实际存储后端 |
| 认证 | 无，Account 实体定义了 username/password/status 但未对接数据库 |

当前 `docker-compose.postgres.yml` 已有 PostgreSQL 服务，`docker/postgres/init/001_schema.sql` 定义了 users、addresses、product_categories、products、orders、order_items、payments 七张表。**PostgreSQL 直接沿用，无需替换。**

---

## 二、目标架构

```
┌─────────────────────────────────────────────────┐
│                   FastAPI 后端                    │
│  ┌──────────────┐  ┌──────────────────────────┐ │
│  │  SQLAlchemy   │  │  MinIO Python SDK        │ │
│  │  (asyncpg)    │  │  (minio-py)              │ │
│  └──────┬───────┘  └───────────┬──────────────┘ │
└─────────┼──────────────────────┼────────────────┘
          │                      │
    ┌─────▼─────┐          ┌─────▼─────┐
    │ PostgreSQL │          │   MinIO    │
    │   (16)     │          │  (S3 API)  │
    └───────────┘          └───────────┘
    用户账号/密码/状态      商品图片
    地址/订单/支付          商品数据文件(JSON等)
    商品元数据
    分类数据
```

### 职责划分

| 存储 | 数据内容 | 原因 |
|------|----------|------|
| **PostgreSQL** | 用户账号、密码哈希、账号状态、地址、商品元数据、分类、订单、支付 | 结构化关系数据，需要事务、查询、关联 |
| **MinIO** | 商品图片（多尺寸）、商品附件/数据文件 | 非结构化二进制对象，S3 兼容，支持预签名 URL |

---

## 三、PostgreSQL 配置

### 3.1 Docker Compose 服务（沿用现有）

项目已有 `docker-compose.postgres.yml`，直接沿用：

```yaml
services:
  postgres:
    image: postgres:16-alpine
    container_name: shopping-postgres
    restart: unless-stopped
    environment:
      POSTGRES_DB: shopping
      POSTGRES_USER: shopping_user
      POSTGRES_PASSWORD: shopping_password
      TZ: Asia/Shanghai
      PGTZ: Asia/Shanghai
    ports:
      - "5432:5432"
    volumes:
      - shopping_postgres_data:/var/lib/postgresql/data
      - ./docker/postgres/init:/docker-entrypoint-initdb.d:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U shopping_user -d shopping"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 10s
    networks:
      - shopping-net

networks:
  shopping-net:
    name: shopping-net
    driver: bridge

volumes:
  shopping_postgres_data:
```

### 3.2 PostgreSQL Schema（更新现有）

更新 `docker/postgres/init/001_schema.sql`，替换为以下内容：

```sql
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- 用户账号表（核心表）
CREATE TABLE IF NOT EXISTS accounts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_name       VARCHAR(20)  NOT NULL UNIQUE,
    password_hash   TEXT         NOT NULL,                -- bcrypt/pbkdf2 hash
    status          VARCHAR(32)  NOT NULL DEFAULT 'active', -- active|blocked|banned|compromised|archived|unknown
    first_name      VARCHAR(100) NOT NULL,
    last_name       VARCHAR(100) NOT NULL,
    email           VARCHAR(255) NOT NULL UNIQUE,
    phone_country_code VARCHAR(16),
    phone_number       VARCHAR(64),
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_accounts_status ON accounts(status);
CREATE INDEX IF NOT EXISTS idx_accounts_email  ON accounts(email);

-- 收货地址表
CREATE TABLE IF NOT EXISTS addresses (
    id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id           UUID         NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    street               VARCHAR(255) NOT NULL,
    city                 VARCHAR(120) NOT NULL,
    state                VARCHAR(120) NOT NULL,
    postal_code          VARCHAR(32)  NOT NULL,
    country              VARCHAR(120) NOT NULL,
    is_default_shipping  BOOLEAN      NOT NULL DEFAULT false,
    created_at           TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at           TIMESTAMPTZ  NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_addresses_account ON addresses(account_id);

-- 商品分类表
CREATE TABLE IF NOT EXISTS product_categories (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        VARCHAR(120) NOT NULL UNIQUE,
    description TEXT         NOT NULL DEFAULT '',
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ  NOT NULL DEFAULT now()
);

-- 商品表（核心：product_hash 是商品与 MinIO 图片的唯一绑定标识）
CREATE TABLE IF NOT EXISTS products (
    id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_hash         CHAR(64)      NOT NULL UNIQUE,   -- SHA-256，商品与图片的一一对应标识
    category_id          UUID          REFERENCES product_categories(id) ON DELETE SET NULL,
    name                 VARCHAR(160)  NOT NULL UNIQUE,
    slug                 VARCHAR(200)  NOT NULL UNIQUE,
    description          TEXT          NOT NULL DEFAULT '',
    price                NUMERIC(12,2) NOT NULL CHECK (price > 0),
    available_item_count INTEGER       NOT NULL DEFAULT 0 CHECK (available_item_count >= 0),
    metadata_json        JSONB         DEFAULT '{}'::jsonb,
    created_at           TIMESTAMPTZ   NOT NULL DEFAULT now(),
    updated_at           TIMESTAMPTZ   NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category_id);
CREATE INDEX IF NOT EXISTS idx_products_slug     ON products(slug);
CREATE INDEX IF NOT EXISTS idx_products_hash     ON products(product_hash);

-- 商品图片引用表（实际图片存储在 MinIO，通过 product_hash 定位）
CREATE TABLE IF NOT EXISTS product_images (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID         NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    image_url  VARCHAR(512) NOT NULL,              -- MinIO 对象路径，基于 product_hash
    rank       INTEGER      NOT NULL DEFAULT 0,   -- 展示排序
    created_at TIMESTAMPTZ  NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_images_product ON product_images(product_id);

-- 商品变体表 (SKU)
CREATE TABLE IF NOT EXISTS product_variants (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id      UUID         NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    variant_id_str  VARCHAR(100) NOT NULL UNIQUE,
    name            VARCHAR(160) NOT NULL,
    sku             VARCHAR(64)  NOT NULL UNIQUE,
    price           NUMERIC(12,2) NOT NULL CHECK (price > 0),
    inventory_count INTEGER      NOT NULL DEFAULT 0 CHECK (inventory_count >= 0),
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_variants_product ON product_variants(product_id);

-- 订单表
CREATE TABLE IF NOT EXISTS orders (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id   UUID         REFERENCES accounts(id) ON DELETE SET NULL,
    order_number VARCHAR(64)  NOT NULL UNIQUE,
    status       VARCHAR(32)  NOT NULL DEFAULT 'pending',
    order_date   TIMESTAMPTZ  NOT NULL DEFAULT now(),
    created_at   TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at   TIMESTAMPTZ  NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_orders_account ON orders(account_id);
CREATE INDEX IF NOT EXISTS idx_orders_number  ON orders(order_number);

-- 订单明细表
CREATE TABLE IF NOT EXISTS order_items (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id     UUID         NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id   UUID         REFERENCES products(id) ON DELETE SET NULL,
    product_name VARCHAR(160) NOT NULL,
    quantity     INTEGER      NOT NULL CHECK (quantity > 0),
    price        NUMERIC(12,2) NOT NULL CHECK (price > 0),
    created_at   TIMESTAMPTZ  NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_order_items_order ON order_items(order_id);

-- 支付表
CREATE TABLE IF NOT EXISTS payments (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id   UUID         REFERENCES orders(id) ON DELETE SET NULL,
    status     VARCHAR(32)  NOT NULL DEFAULT 'pending',
    amount     NUMERIC(12,2) NOT NULL CHECK (amount > 0),
    currency   CHAR(3)      NOT NULL DEFAULT 'CNY',
    created_at TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ  NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_payments_order ON payments(order_id);
```

### 3.3 与原有 Schema 的差异

| 项 | 原 Schema | 新 Schema |
|----|-----------|-----------|
| users 表 | `users` | `accounts`（与领域实体 Account 对齐） |
| addresses 字段 | `user_id` | `account_id` |
| 新增字段 | - | `products.product_hash`, `products.slug`, `products.metadata_json (JSONB)` |
| 新增表 | - | `product_images`, `product_variants` |

### 3.4 商品哈希生成规则

`product_hash` 是商品与 MinIO 图片之间的唯一绑定标识，**在商品创建时计算一次，不可变更**。

#### 代码位置

哈希生成逻辑收敛在 **`backend/online_shopping/services/hash_service.py`**，作为领域服务供 API 路由和业务服务统一调用：

```
backend/online_shopping/domain/services/
├── hash_service.py          # [新] 哈希生成服务
├── catalog_service.py       # (现有)
├── order_service.py         # (现有)
├── payment_service.py       # (现有)
└── shipment_service.py      # (现有)
```

#### `hash_service.py` 完整实现

```python
from __future__ import annotations

import hashlib


def generate_product_hash(name: str, category_name: str) -> str:
    """
    基于商品名 + 分类名生成 SHA-256 哈希，作为商品与 MinIO 图片的一一对应标识。

    相同的名称和分类始终产生相同的哈希值，天然去重。
    """
    payload = f"{name.strip().lower()}::{category_name.strip().lower()}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
```

#### 调用方

| 调用位置 | 场景 |
|----------|------|
| `api/routers/products.py` | 创建商品 API 入口 |
| `services/catalog_service.py` | 批量导入商品、后台创建 |
| `services/catalog_service.py` | 商品更新时判断是否需要重算哈希并迁移 MinIO 文件 |

统一入口确保所有创建路径使用同一算法，不会出现不同调用方各自实现导致不一致。

#### 设计要点

| 特性 | 说明 |
|------|------|
| 确定性 | 相同商品名 + 分类 -> 相同哈希，避免重复商品产生不同路径 |
| 唯一性 | CHAR(64) + UNIQUE 约束，数据库层面保证一商品一哈希 |
| 不可变 | 哈希在创建时固化，即使商品改名也不影响已有图片路径 |
| MinIO 路径 | MinIO 对象路径直接使用哈希值作为目录名，实现商品 -> 哈希 -> 图片的链式定位 |

---

## 四、MinIO 配置

### 4.1 Docker Compose 服务

新建 `docker-compose.minio.yml`：

```yaml
services:
  minio:
    image: minio/minio:latest
    container_name: shopping-minio
    restart: unless-stopped
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin123
      TZ: Asia/Shanghai
    ports:
      - "9000:9000"   # S3 API
      - "9001:9001"   # Web Console
    volumes:
      - shopping_minio_data:/data
    healthcheck:
      test: ["CMD", "mc", "ready", "local"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 10s
    networks:
      - shopping-net

  # MinIO 初始化：自动创建 bucket
  minio-init:
    image: minio/mc:latest
    container_name: shopping-minio-init
    depends_on:
      minio:
        condition: service_healthy
    entrypoint: >
      /bin/sh -c "
      mc alias set local http://minio:9000 minioadmin minioadmin123;
      mc mb --ignore-existing local/shopping-products;
      mc mb --ignore-existing local/shopping-data;
      mc anonymous set download local/shopping-products;
      mc anonymous set private local/shopping-data;
      echo 'MinIO buckets ready';
      exit 0;
      "
    networks:
      - shopping-net

networks:
  shopping-net:
    name: shopping-net
    driver: bridge

volumes:
  shopping_minio_data:
```

### 4.2 Bucket 规划

| Bucket | 用途 | 访问策略 | 内容示例 |
|--------|------|----------|----------|
| `shopping-products` | 商品图片 | public (download) | `products/{product_hash}/main.jpg` |
| `shopping-data` | 业务数据文件 | private | 商品导入导出文件、报表等 |

### 4.3 对象路径规范（基于哈希）

```
shopping-products/
  └── products/
      ├── {product_hash}/          # 64 位 SHA-256 哈希，与 PostgreSQL products.product_hash 一致
      │   ├── main.jpg             # 主图 (原图)
      │   ├── main_thumb.jpg       # 缩略图 (200x200)
      │   ├── gallery_01.jpg       # 详情图1
      │   └── gallery_02.jpg       # 详情图2
      └── ...

shopping-data/
  └── exports/
      └── products_20260709.json
```

#### 哈希 -> 图片的对应关系

```
PostgreSQL products 表               MinIO 对象存储
┌──────────────────────┐            ┌─────────────────────────────────┐
│ product_hash         │            │ shopping-products/products/      │
│ a1b2c3... (SHA-256)  │ ────────> │   a1b2c3.../main.jpg            │
│ name: "Everyday Tote"│            │   a1b2c3.../main_thumb.jpg      │
│ category: "Bags"     │            │   a1b2c3.../gallery_01.jpg      │
└──────────────────────┘            └─────────────────────────────────┘

一张 product 对应一个哈希目录，一个哈希目录包含该商品的全部图片。
```

前端/API 通过 MinIO 预签名 URL 或反向代理访问图片，路径中的哈希段保证 URL 稳定且与商品一一对应。

---

## 五、Backend Python 依赖变更

### 5.1 新增依赖

`backend/requirements.txt` 需要新增以下依赖：

```txt
# PostgreSQL 异步驱动 + ORM
sqlalchemy[asyncio]>=2.0,<3.0
asyncpg>=0.29

# MinIO 客户端
minio>=7.2

# 密码哈希
passlib[bcrypt]>=1.7

# 环境变量管理
python-dotenv>=1.0
```

---

## 六、Backend 代码结构调整建议

### 6.1 新增目录结构

```
backend/online_shopping/
├── api/
│   ├── app.py              # FastAPI 应用 + lifespan 初始化
│   ├── deps.py             # [新] 依赖注入 (get_db, get_minio)
│   ├── routers/            # (现有)
│   └── schemas.py          # (现有)
├── config.py               # [新] 统一配置读取 (DATABASE_URL, MINIO_*, etc.)
├── database.py             # [新] SQLAlchemy async engine + session_factory
├── models/                 # [新] SQLAlchemy ORM 模型
│   ├── __init__.py
│   ├── account.py
│   ├── address.py
│   ├── product.py
│   ├── product_image.py
│   ├── product_variant.py
│   ├── category.py
│   ├── order.py
│   └── payment.py
├── storage.py              # [新] MinIO 客户端封装
├── domain/                 # (现有，保持不变)
└── services/               # (现有)
    ├── hash_service.py     # [新] 商品哈希生成服务
    ├── catalog_service.py  # (现有，后续改为读写数据库)
    ├── order_service.py
    ├── payment_service.py
    └── shipment_service.py
```

### 6.2 核心配置 `config.py`

```python
import os
from dataclasses import dataclass

@dataclass
class Settings:
    # PostgreSQL
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://shopping_user:shopping_password@localhost:5432/shopping",
    )

    # MinIO
    minio_endpoint: str = os.getenv("MINIO_ENDPOINT", "localhost:9000")
    minio_access_key: str = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    minio_secret_key: str = os.getenv("MINIO_SECRET_KEY", "minioadmin123")
    minio_secure: bool = os.getenv("MINIO_SECURE", "false").lower() == "true"
    minio_bucket_products: str = os.getenv("MINIO_BUCKET_PRODUCTS", "shopping-products")
    minio_bucket_data: str = os.getenv("MINIO_BUCKET_DATA", "shopping-data")

settings = Settings()
```

### 6.3 数据库连接 `database.py`

```python
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from online_shopping.config import settings

engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_size=10,
    max_overflow=20,
)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db():
    async with async_session() as session:
        yield session
```

### 6.4 MinIO 客户端 `storage.py`

```python
from minio import Minio
from online_shopping.config import settings

_minio_client: Minio | None = None

def get_minio_client() -> Minio:
    global _minio_client
    if _minio_client is None:
        _minio_client = Minio(
            endpoint=settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
        )
    return _minio_client


def build_image_path(product_hash: str, file_name: str) -> str:
    """基于商品哈希构造 MinIO 对象路径"""
    return f"products/{product_hash}/{file_name}"


def upload_product_image(product_hash: str, file_name: str, data: bytes, content_type: str = "image/jpeg") -> str:
    """
    上传商品图片到 MinIO。
    :param product_hash: 商品 SHA-256 哈希（与 PostgreSQL products.product_hash 一致）
    :param file_name:   文件名，如 'main.jpg'
    :param data:        图片二进制数据
    :return:            存储的相对路径
    """
    client = get_minio_client()
    object_path = build_image_path(product_hash, file_name)
    client.put_object(
        bucket_name=settings.minio_bucket_products,
        object_name=object_path,
        data=data,
        length=len(data),
        content_type=content_type,
    )
    return object_path


def get_image_url(product_hash: str, file_name: str) -> str:
    """生成图片访问 URL（可直接存入 product_images.image_url）"""
    return f"/minio/{settings.minio_bucket_products}/{build_image_path(product_hash, file_name)}"
```

### 6.5 FastAPI 生命周期变更 `app.py`

在现有 `create_app()` 基础上**增加两处修改**（不是替换整个文件）：

**修改 1 — 新增 import**（文件顶部）：

```python
# 新增
from contextlib import asynccontextmanager
from online_shopping.database import engine
```

**修改 2 — `create_app()` 增加 lifespan 参数**：

```python
# 新增 lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 开发环境可打开自动建表；生产用 Alembic migration
    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Online Shopping Backend",
        version="0.1.0",
        description="FastAPI API for the online shopping domain model.",
        lifespan=lifespan,                           # <-- 新增这一行
    )
    # ... CORS、routers 等其余代码完全不变
```

现有 `app.py` 中的 CORS 中间件、路由注册等代码全部保留不动。

### 6.6 依赖注入 `deps.py`（新建）

路由不直接创建数据库连接或 MinIO 客户端，而是通过 FastAPI `Depends` 注入。`deps.py` 集中管理这些依赖：

```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from minio import Minio
from online_shopping.database import async_session
from online_shopping.storage import get_minio_client

async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session

def get_minio() -> Minio:
    return get_minio_client()
```

### 6.7 路由层变更示例

以 `api/routers/products.py` 为例，**在现有路由文件中增加创建商品端点**。路由通过 `Depends` 注入依赖，调用 `hash_service` 和 `storage` 完成 PostgreSQL + MinIO 联动：

```python
from fastapi import APIRouter, Depends, UploadFile, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from online_shopping.api.deps import get_db, get_minio
from online_shopping.services.hash_service import generate_product_hash
from online_shopping.storage import upload_product_image, get_image_url

router = APIRouter()

# ... 现有路由 (GET /products, GET /products/{name} 等) 全部保留 ...

@router.post("/products")
async def create_product(
    name: str,
    category_name: str,
    description: str,
    price: float,
    files: list[UploadFile],
    db: AsyncSession = Depends(get_db),
):
    # 1. 计算商品哈希
    product_hash = generate_product_hash(name, category_name)

    # 2. 检查哈希是否已存在
    # existing = await db.execute(
    #     select(ProductModel).where(ProductModel.product_hash == product_hash)
    # )
    # if existing.scalar_one_or_none():
    #     raise HTTPException(status_code=409, detail="商品已存在")

    # 3. 写入 PostgreSQL
    # product = ProductModel(product_hash=product_hash, name=name, ...)
    # db.add(product)
    # await db.flush()

    # 4. 图片上传到 MinIO
    for idx, file in enumerate(files):
        object_path = upload_product_image(product_hash, file.filename, await file.read())
        image_url = get_image_url(product_hash, file.filename)
        # image_model = ProductImage(product_id=product.id, image_url=image_url, rank=idx)
        # db.add(image_model)

    # await db.commit()
    return {"product_hash": product_hash, "image_count": len(files)}
```

### 6.8 各新增文件职责总览

| 文件 | 职责 | 被谁调用 |
|------|------|----------|
| `api/deps.py` | 提供 `get_db`、`get_minio` 依赖注入 | 所有路由文件（通过 `Depends`） |
| `services/hash_service.py` | `generate_product_hash()` 算法唯一入口 | 路由、catalog_service |
| `storage.py` | MinIO 客户端、上传、URL 生成 | 路由、catalog_service |
| `database.py` | SQLAlchemy engine + session factory | `deps.py` |
| `config.py` | 统一配置读取 | 所有模块 |
| `models/*.py` | ORM 模型映射 PostgreSQL 表 | 路由、services |

---

## 七、环境变量总览

### 7.1 docker-compose.backend.yml 变更

当前环境变量：

```yaml
DATABASE_URL: postgresql://shopping_user:shopping_password@postgres:5432/shopping
```

变更为（加上 MinIO 配置）：

```yaml
environment:
  PYTHONUNBUFFERED: "1"
  PYTHONPATH: /app
  TZ: Asia/Shanghai
  DATABASE_URL: postgresql+asyncpg://shopping_user:shopping_password@postgres:5432/shopping
  MINIO_ENDPOINT: minio:9000
  MINIO_ACCESS_KEY: minioadmin
  MINIO_SECRET_KEY: minioadmin123
  MINIO_BUCKET_PRODUCTS: shopping-products
  MINIO_BUCKET_DATA: shopping-data
```

### 7.2 启动顺序

```cmd
# 1. 启动 PostgreSQL（已有）
docker compose -f docker-compose.postgres.yml up -d

# 2. 启动 MinIO（新建）
docker compose -f docker-compose.minio.yml up -d

# 3. 启动后端
docker compose -f docker-compose.backend.yml up -d

# 4. 启动前端
docker compose -f docker-compose.frontend.yml up -d
```

---

## 八、迁移策略

### 8.1 Schema 迁移

当前 `docker/postgres/init/001_schema.sql` 需更新为新版（见 3.2 节）。如果 PostgreSQL volume 已存在，需手动执行变更或重建 volume：

```cmd
# 重建 PostgreSQL（会清空数据，仅开发环境）
docker compose -f docker-compose.postgres.yml down -v
docker compose -f docker-compose.postgres.yml up -d
```

后续 schema 版本管理建议引入 **Alembic**：

```cmd
cd backend
pip install alembic
alembic init migrations
```

配置 `alembic.ini` 使用 `postgresql+asyncpg://` 连接串。

### 8.2 后端代码迁移

从内存存储切换到 PostgreSQL + MinIO 的路径：

1. **Phase 1**：建好 PostgreSQL 表 + MinIO bucket，`config.py`、`database.py`、`storage.py` 就位
2. **Phase 2**：逐模块替换——先从 products 模块开始，再迁移 orders、cart、accounts
3. **Phase 3**：删除 `store.py` 中的内存存储代码

---

## 九、安全注意事项

| 项目 | 建议 |
|------|------|
| 密码存储 | 使用 `passlib` + `bcrypt` 哈希，**绝不存明文** |
| 数据库连接 | 生产环境使用 secrets 管理密码，不写死在 docker-compose |
| MinIO 凭证 | 同样使用 secrets / 环境变量注入 |
| MinIO bucket | `shopping-products` 设 public download，但禁止 list；`shopping-data` 严格 private |
| SQL 注入 | SQLAlchemy ORM 使用参数化查询，禁止拼接 SQL |
| 图片上传 | 校验文件类型（魔数检测）、限制文件大小、防病毒扫描 |

---

## 十、文件清单

### 需要新建

| 文件 | 说明 |
|------|------|
| `docker-compose.minio.yml` | MinIO 容器定义 + 初始化 |
| `backend/online_shopping/config.py` | 统一配置 |
| `backend/online_shopping/database.py` | SQLAlchemy engine + session |
| `backend/online_shopping/services/hash_service.py` | 商品哈希生成服务 |
| `backend/online_shopping/storage.py` | MinIO 客户端封装 |
| `backend/online_shopping/models/` | SQLAlchemy ORM 模型目录 |

### 需要修改

| 文件 | 变更内容 |
|------|----------|
| `docker/postgres/init/001_schema.sql` | 更新为新的 accounts/products/images/variants 表结构 |
| `backend/requirements.txt` | 新增 sqlalchemy, asyncpg, minio, passlib, python-dotenv |
| `backend/online_shopping/api/app.py` | 添加 lifespan, 依赖注入 |
| `backend/online_shopping/api/routers/*.py` | 从内存 store 切换到数据库 session |
| `backend/online_shopping/api/store.py` | 逐步废弃，由数据库操作层替代 |
| `docker-compose.backend.yml` | DATABASE_URL 改为 asyncpg 驱动, 新增 MinIO 环境变量 |

### 无需变更（沿用现有）

| 文件 | 说明 |
|------|------|
| `docker-compose.postgres.yml` | 沿用现有 PostgreSQL 容器定义 |
| `docker-compose.frontend.yml` | 前端配置不变 |

---

**总结**：PostgreSQL 负责所有结构化关系数据（用户、订单、商品元数据），MinIO 负责非结构化对象存储（图片、文件）。**商品与图片通过 SHA-256 哈希值一一对应**——`products.product_hash` 既作为数据库唯一标识，也作为 MinIO 存储路径的目录名，实现从商品到图片的直接定位。PostgreSQL 沿用现有基础设施，MinIO 通过新增 Docker Compose 一键部署，后端通过 SQLAlchemy + asyncpg 访问数据库，通过 minio-py SDK 访问对象存储。
