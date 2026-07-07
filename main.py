from online_shopping.services.catalog_service import CatalogService


def main() -> None:
    catalog_service = CatalogService()
    print(f"Online shopping system ready: {catalog_service.__class__.__name__}")


if __name__ == "__main__":
    main()
