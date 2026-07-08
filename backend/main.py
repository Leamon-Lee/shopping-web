import uvicorn

from online_shopping.api.app import app


def main() -> None:
    uvicorn.run(
        "online_shopping.api.app:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
    )


if __name__ == "__main__":
    main()
