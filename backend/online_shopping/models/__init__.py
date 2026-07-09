from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# 确保所有模型在 SQLAlchemy mapper 配置前被导入
from online_shopping.models.account import Account  # noqa: E402, F401
from online_shopping.models.address import Address  # noqa: E402, F401
from online_shopping.models.category import ProductCategory  # noqa: E402, F401
from online_shopping.models.order import Order, OrderItem  # noqa: E402, F401
from online_shopping.models.payment import Payment  # noqa: E402, F401
from online_shopping.models.product import Product  # noqa: E402, F401
from online_shopping.models.product_image import ProductImage  # noqa: E402, F401
from online_shopping.models.product_variant import ProductVariant  # noqa: E402, F401
