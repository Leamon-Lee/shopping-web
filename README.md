# Online Shopping System

Ecommerce workspace with a FastAPI backend and a Next.js storefront frontend.

## Project layout

- `backend/src/online_shopping/domain/entities`: business entities
- `backend/src/online_shopping/domain/value_objects`: validated value objects
- `backend/src/online_shopping/domain/enums`: status enums
- `backend/src/online_shopping/domain/interfaces`: domain contracts
- `backend/src/online_shopping/services`: application services
- `backend/src/online_shopping/api`: FastAPI app, schemas, routers, and in-memory API store
- `frontend`: Next.js storefront
- `docs/design`: PlantUML design documents

## Run backend

```powershell
cd backend
$env:PYTHONPATH = "src"
python main.py
```

The FastAPI app is exposed as `online_shopping.api.app:app` and defaults to port `8001`.
