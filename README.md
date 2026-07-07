# Online Shopping System

Domain model for an online shopping system, organized as a `src` package.

## Project layout

- `src/online_shopping/domain/entities`: business entities
- `src/online_shopping/domain/value_objects`: validated value objects
- `src/online_shopping/domain/enums`: status enums
- `src/online_shopping/domain/interfaces`: domain contracts
- `src/online_shopping/services`: application services
- `docs/design`: PlantUML design documents

## Run

```powershell
$env:PYTHONPATH = "src"
python main.py
```
