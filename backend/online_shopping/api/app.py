from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from online_shopping.api.routers import accounts, cart, events, health, marketplace, orders, panels, payments, products, recommendations, regions

from contextlib import asynccontextmanager
from online_shopping.database import engine

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
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:8000",
            "http://127.0.0.1:8000",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health.router)
    app.include_router(marketplace.router, tags=["marketplace"])
    app.include_router(accounts.router, prefix="/accounts", tags=["accounts"])
    app.include_router(products.router, prefix="/shop", tags=["shop"])
    app.include_router(products.router, prefix="/products", tags=["products"])
    app.include_router(regions.router, prefix="/regions", tags=["regions"])
    app.include_router(cart.router, prefix="/cart", tags=["cart"])
    app.include_router(orders.router, prefix="/orders", tags=["orders"])
    app.include_router(payments.router, prefix="/payments", tags=["payments"])
    app.include_router(panels.router, tags=["panels"])
    app.include_router(events.router, prefix="/events", tags=["events"])
    app.include_router(recommendations.router, prefix="/recommendations", tags=["recommendations"])
    return app


app = create_app()
