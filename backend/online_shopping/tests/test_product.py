import pytest

from online_shopping.domain.entities.product import Product
from online_shopping.domain.entities.product_category import ProductCategory
from online_shopping.domain.entities.product_variant import ProductVariant
from online_shopping.domain.value_objects.product_values import (
    CategoryDescription,
    CategoryName,
    Price,
    ProductCount,
    ProductDescription,
    ProductName,
    ProductSlug,
    ProductVariantId,
    ProductVariantName,
    Quantity,
    Rating,
    Sku,
)


def test_price_accepts_positive_number() -> None:
    assert Price(10).value == 10.0


def test_price_exposes_minor_units() -> None:
    assert Price(10.25).minor_units == 1025


def test_inventory_and_quantity_constraints() -> None:
    assert ProductCount(0).value == 0
    assert Quantity(1).value == 1
    with pytest.raises(ValueError):
        ProductCount(-1)
    with pytest.raises(ValueError):
        Quantity(0)


def test_product_gets_backend_slug_and_default_variant() -> None:
    category = ProductCategory(
        name=CategoryName("Bags"),
        description=CategoryDescription("Reusable bags"),
    )
    product = Product(
        name=ProductName("Everyday Tote"),
        description=ProductDescription("Durable cotton tote"),
        price=Price(29),
        category=category,
        variants=[
            ProductVariant(
                variant_id=ProductVariantId("variant_everyday-tote"),
                name=ProductVariantName("Default Variant"),
                sku=Sku("SKU-EVERYDAY-TOTE"),
                price=Price(29),
                inventory_count=ProductCount(25),
            )
        ],
    )

    assert product.slug == ProductSlug("everyday-tote")
    assert product.get_default_variant().variant_id.value == "variant_everyday-tote"
    assert product.is_available(2)


def test_rating_is_limited_to_storefront_range() -> None:
    assert Rating(5).value == 5
    with pytest.raises(ValueError):
        Rating(6)
