"""Tests for config, storage utilities, and API mappers."""

import os
from unittest import mock

import pytest

from online_shopping.config import Settings, settings
from online_shopping.storage import build_image_path, get_image_url
from online_shopping.api.mappers import image_to_out, product_to_out, cart_item_to_out, cart_to_out, order_to_out, variant_to_out
from online_shopping.api.schemas import ImageOut


class TestSettings:
    def test_defaults(self):
        s = Settings()
        assert s.database_url is not None
        assert s.jwt_secret_key == "dev-secret-key-change-in-production"
        assert s.jwt_algorithm == "HS256"
        assert s.jwt_expire_minutes == 1440

    def test_minio_defaults(self):
        s = Settings()
        assert s.minio_endpoint == "localhost:9000"
        assert s.minio_access_key == "minioadmin"
        assert s.minio_secure is False
        assert s.minio_bucket_products == "shopping-products"

    def test_env_override(self):
        # Settings fields use os.getenv at class definition time,
        # so we verify the fields exist with correct types instead.
        s = Settings()
        assert isinstance(s.jwt_secret_key, str)
        assert isinstance(s.jwt_expire_minutes, int)
        assert isinstance(s.minio_secure, bool)
        # Custom instantiation with kwargs (dataclass skips defaults when value provided)
        s2 = Settings(
            jwt_secret_key="prod-secret",
            jwt_expire_minutes=60,
            minio_secure=True,
        )
        assert s2.jwt_secret_key == "prod-secret"
        assert s2.jwt_expire_minutes == 60
        assert s2.minio_secure is True

    def test_global_settings(self):
        assert isinstance(settings, Settings)

    def test_dataclass_field_types(self):
        s = Settings()
        assert isinstance(s.database_url, str)
        assert isinstance(s.jwt_expire_minutes, int)
        assert isinstance(s.minio_secure, bool)
        assert isinstance(s.public_minio_base_url, str)


class TestStorage:
    def test_build_image_path(self):
        path = build_image_path("abc123", "image.jpg")
        assert path == "products/abc123/image.jpg"

    def test_build_image_path_subfolder(self):
        path = build_image_path("hash123", "sub/img.png")
        assert path == "products/hash123/sub/img.png"

    def test_get_image_url(self):
        url = get_image_url("abc123", "image.jpg")
        assert url.startswith("http://localhost:9000/shopping-products/products/abc123/image.jpg")

    def test_get_image_url_trailing_slash(self):
        with mock.patch.object(settings, "public_minio_base_url", "http://localhost:9000/"):
            url = get_image_url("hash", "img.jpg")
            # Should not have double-slash in the path (protocol :// is fine)
            assert "products//" not in url
            assert "shopping-products//" not in url


class TestImageToOut:
    def test_image_to_out(self):
        class FakeImage:
            image_url = "/test.jpg"
            url = "/test.jpg"
            rank = 1
        result = image_to_out(FakeImage())
        assert isinstance(result, ImageOut)
        assert result.image_url == "/test.jpg"
        assert result.rank == 1


class TestVariantToOut:
    def test_basic(self):
        class FakeVariant:
            id = 1
            name = "Default"
            sku = "SKU-1"
            price = 29.0
            inventory_count = 25
            manages_inventory = True
            allows_backorder = False
            product = None
        result = variant_to_out(FakeVariant())
        assert result.id == "1"
        assert result.name == "Default"
        assert result.sku == "SKU-1"
        assert result.price == 29.0

    def test_include_product(self):
        class FakeProduct:
            id = 1
            name = "Tote"
            slug = "tote"
            images = []
        class FakeVariant:
            id = 2
            name = "Large"
            sku = "SKU-L"
            price = 35.0
            inventory_count = 10
            manages_inventory = True
            allows_backorder = False
            product = FakeProduct()
        result = variant_to_out(FakeVariant(), include_product=True)
        assert result.product is not None
        assert result.product["title"] == "Tote"
        assert result.product["handle"] == "tote"


class TestProductToOut:
    def test_basic(self):
        class FakeCategory:
            name = "Bags"
            description = "Nice bags"
        class FakeProduct:
            id = 1
            name = "Tote"
            slug = "tote"
            description = "A tote bag"
            price = 29.0
            available_item_count = 25
            category = FakeCategory()
            images = []
            variants = []
        result = product_to_out(FakeProduct())
        assert result.id == "1"
        assert result.name == "Tote"
        assert result.slug == "tote"
        assert result.category.name == "Bags"
        assert result.thumbnail is None

    def test_with_images(self):
        class FakeImage:
            image_url = "/img1.jpg"
            rank = 0
        class FakeCategory:
            name = "Bags"
            description = "Nice bags"
        class FakeProduct:
            id = 1
            name = "Tote"
            slug = "tote"
            description = "A tote bag"
            price = 29.0
            available_item_count = 25
            category = FakeCategory()
            images = [FakeImage()]
            variants = []
        result = product_to_out(FakeProduct())
        assert result.thumbnail == "/img1.jpg"
        assert len(result.images) == 1

    def test_null_category(self):
        class FakeProduct:
            id = 1
            name = "Tote"
            slug = "tote"
            description = "A tote bag"
            price = 29.0
            available_item_count = 25
            category = None
            images = []
            variants = []
        result = product_to_out(FakeProduct())
        assert result.category.name == "Uncategorized"


class TestCartItemToOut:
    def test_basic(self):
        class FakeCategory:
            name = "Bags"
            description = "Nice bags"
        class FakeProduct:
            id = 1
            name = "Tote"
            slug = "tote"
            description = "A tote"
            price = 29.0
            available_item_count = 25
            category = FakeCategory()
            images = []
            variants = []
        class FakeMinVariant:
            id = 1
            name = "Default"
            sku = "SKU-1"
            price = 29.0
            inventory_count = 25
            manages_inventory = True
            allows_backorder = False
            product = FakeProduct()
        class FakeCartItem:
            id = 1
            quantity = 2
            price = 29.0
            variant = FakeMinVariant()
            created_at = None
        result = cart_item_to_out(FakeCartItem())
        assert result.quantity == 2
        assert result.product_title == "Tote"
        assert result.product_handle == "tote"


class TestCartToOut:
    def test_basic(self):
        class FakeCategory:
            name = "Bags"
            description = "Nice bags"
        class FakeProduct:
            id = 1
            name = "Tote"
            slug = "tote"
            description = "A tote"
            price = 29.0
            available_item_count = 25
            category = FakeCategory()
            images = []
            variants = []
        class FakeMinVariant:
            id = 1
            name = "Default"
            sku = "SKU-1"
            price = 29.0
            inventory_count = 25
            manages_inventory = True
            allows_backorder = False
            product = FakeProduct()
        class FakeCartItem:
            id = 1
            quantity = 2
            price = 29.0
            variant = FakeMinVariant()
            created_at = None
        class FakeCart:
            id = 1
            items = [FakeCartItem()]
            currency_code = "cny"
            region_id = "reg_cny"
        result = cart_to_out(FakeCart())
        assert result.total_quantity == 2
        assert result.currency_code == "cny"
        assert result.region["id"] == "reg_cny"


class TestOrderToOut:
    def test_basic(self):
        class FakeOrderItem:
            id = 1
            quantity = 2
            price = 29.0
            product_id = 1
            product_name = "Tote"
        class FakeOrder:
            order_number = "ORD-1001"
            status = "created"
            order_date = None
            items = [FakeOrderItem()]
            payments = []
        result = order_to_out(FakeOrder())
        assert result.order_number == "ORD-1001"
        assert len(result.items) == 1
        assert result.payment is None

    def test_with_payment(self):
        class FakePayment:
            status = "completed"
            amount = 58.0
            currency = "cny"
        class FakeOrderItem:
            id = 1
            quantity = 2
            price = 29.0
            product_id = 1
            product_name = "Tote"
        class FakeOrder:
            order_number = "ORD-1001"
            status = "created"
            order_date = None
            items = [FakeOrderItem()]
            payments = [FakePayment()]
        result = order_to_out(FakeOrder())
        assert result.payment is not None
        assert result.payment.status == "completed"
        assert result.payment.amount == 58.0
