from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from online_shopping.api.routers import cart, health, orders, payments, products


def create_app() -> FastAPI:
    app = FastAPI(
        title="Online Shopping Backend",
        version="0.1.0",
        description="FastAPI API for the online shopping domain model.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health.router)
    app.include_router(products.router, prefix="/products", tags=["products"])
    app.include_router(cart.router, prefix="/cart", tags=["cart"])
    app.include_router(orders.router, prefix="/orders", tags=["orders"])
    app.include_router(payments.router, prefix="/payments", tags=["payments"])
    return app


app = create_app()
