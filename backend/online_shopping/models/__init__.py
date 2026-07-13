from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# 确保所有模型在 SQLAlchemy mapper 配置前被导入
from online_shopping.models.account import Account  # noqa: E402, F401
from online_shopping.models.address import Address  # noqa: E402, F401
from online_shopping.models.category import ProductCategory  # noqa: E402, F401
from online_shopping.models.cart import CartItem, ShoppingCart  # noqa: E402, F401
from online_shopping.models.order import Order, OrderItem  # noqa: E402, F401
from online_shopping.models.payment import Payment  # noqa: E402, F401
from online_shopping.models.payment_method import PaymentMethod  # noqa: E402, F401
from online_shopping.models.product import Product  # noqa: E402, F401
from online_shopping.models.product_image import ProductImage  # noqa: E402, F401
from online_shopping.models.product_variant import ProductVariant  # noqa: E402, F401
from online_shopping.models.review import Review  # noqa: E402, F401
from online_shopping.models.shipment import Shipment  # noqa: E402, F401
from online_shopping.models.shop import Shop, ShopProduct  # noqa: E402, F401
from online_shopping.models.wishlist import WishlistItem  # noqa: E402, F401
from online_shopping.models.user_behavior_event import UserBehaviorEvent  # noqa: E402, F401
from online_shopping.models.recommendation_cache import RecommendationCache  # noqa: E402, F401
from online_shopping.models.recommendation_result import RecommendationResult, ItemSimilarity, PopularProduct  # noqa: E402, F401
