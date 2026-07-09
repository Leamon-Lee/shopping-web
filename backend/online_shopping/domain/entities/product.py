from online_shopping.domain.entities.category import Category
from online_shopping.domain.entities.product_image import ProductImage
from online_shopping.domain.entities.product_variant import ProductVariant
from online_shopping.domain.value_objects.product_values import (
    Price,
    ProductCount,
    ProductDescription,
    ProductId,
    ProductName,
    ProductSlug,
    ProductVariantId,
    ProductVariantName,
    Sku,
)


class Product:
    def __init__(
        self,
        name: ProductName,
        description: ProductDescription,
        price: Price,
        category: Category,
        product_id: ProductId | None = None,
        slug: ProductSlug | None = None,
        variants: list[ProductVariant] | None = None,
        images: list[ProductImage] | None = None,
        metadata: dict[str, object] | None = None,
    ) -> None:
        self.__product_id = product_id
        self.__name = name
        self.__description = description
        self.__price = price
        self.__category = category
        self.__slug = slug or ProductSlug.from_name(name)
        self.__images = images or []
        self.__metadata = metadata or {}
        self.__variants = variants or [
            ProductVariant(
                variant_id=ProductVariantId(f"variant_{self.__slug.value}"),
                name=ProductVariantName("Default Variant"),
                sku=Sku(f"SKU-{self.__slug.value.upper()}"),
                price=price,
                inventory_count=ProductCount(0),
            )
        ]

    @property
    def product_id(self) -> ProductId | None:
        return self.__product_id

    @property
    def name(self) -> ProductName:
        return self.__name

    @property
    def description(self) -> ProductDescription:
        return self.__description

    @property
    def price(self) -> Price:
        return self.__price

    @property
    def category(self) -> Category:
        return self.__category

    @property
    def slug(self) -> ProductSlug:
        return self.__slug

    @property
    def variants(self) -> tuple[ProductVariant, ...]:
        return tuple(self.__variants)

    @property
    def images(self) -> tuple[ProductImage, ...]:
        return tuple(self.__images)

    @property
    def metadata(self) -> dict[str, object]:
        return dict(self.__metadata)

    def get_available_count(self) -> ProductCount:
        total = sum(
            variant.inventory_count.value
            for variant in self.__variants
            if variant.manages_inventory
        )
        return ProductCount(total)

    def get_default_variant(self) -> ProductVariant:
        return self.__variants[0]

    def find_variant(self, variant_id: ProductVariantId) -> ProductVariant | None:
        return next(
            (
                variant
                for variant in self.__variants
                if variant.variant_id.value == variant_id.value
            ),
            None,
        )

    def is_available(self, requested_quantity: int = 1) -> bool:
        return self.get_default_variant().is_available(requested_quantity)
