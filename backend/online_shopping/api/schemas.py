from pydantic import BaseModel, Field

from online_shopping.domain.enums.account_status import AccountStatus
from online_shopping.domain.enums.order_status import OrderStatus
from online_shopping.domain.enums.payment_status import PaymentStatus
from online_shopping.domain.enums.shipment_status import ShipmentStatus


class CategoryBase(BaseModel):
    name: str = Field(min_length=1)
    description: str = ""


class CategoryCreate(CategoryBase):
    pass


class CategoryOut(CategoryBase):
    pass


class ProductBase(BaseModel):
    name: str = Field(min_length=1)
    description: str = ""
    price: float = Field(gt=0)
    available_item_count: int = Field(ge=0)
    category: CategoryOut


class ProductCreate(ProductBase):
    pass


class ImageOut(BaseModel):
    image_url: str
    url: str | None = None
    rank: int = 0


class ProductVariantOut(BaseModel):
    id: str
    title: str
    name: str
    sku: str
    price: float
    inventory_quantity: int
    inventory_count: int
    manage_inventory: bool = True
    allow_backorder: bool = False
    product: dict | None = None
    options: list[dict] = Field(default_factory=list)


class ProductOut(ProductBase):
    id: str | None = None
    slug: str | None = None
    handle: str | None = None
    title: str | None = None
    thumbnail: str | None = None
    images: list[ImageOut] = Field(default_factory=list)
    variants: list[ProductVariantOut] = Field(default_factory=list)
    options: list[dict] = Field(default_factory=list)


class CartItemCreate(BaseModel):
    product_name: str = Field(min_length=1)
    quantity: int = Field(ge=1)


class CartItemUpdate(BaseModel):
    quantity: int = Field(ge=1)


class CartItemOut(BaseModel):
    id: str = ""
    quantity: int = Field(ge=1)
    price: float = Field(gt=0)
    product: ProductOut
    product_title: str
    product_handle: str
    thumbnail: str | None = None
    variant: ProductVariantOut | None = None
    unit_price: float | None = None
    total: float | None = None
    created_at: str | None = None


class ShoppingCartOut(BaseModel):
    id: str | None = None
    items: list[CartItemOut]
    total_quantity: int
    subtotal: float
    total: float | None = None
    currency_code: str = "cny"
    region: dict = Field(default_factory=lambda: {"id": "reg_cny", "currency_code": "cny"})
    promotions: list[dict] = Field(default_factory=list)
    shipping_methods: list[dict] = Field(default_factory=list)


class PaymentCreate(BaseModel):
    amount: float = Field(gt=0)
    currency: str = Field(default="CNY", min_length=3, max_length=3)


class PaymentOut(BaseModel):
    status: PaymentStatus = PaymentStatus.PENDING
    amount: float | None = None
    currency: str | None = None


class ShipmentOut(BaseModel):
    status: ShipmentStatus = ShipmentStatus.PENDING
    shipment_date: str | None = None
    estimated_arrival: str | None = None
    shipment_method: str | None = None


class OrderCreate(BaseModel):
    order_number: str | None = None
    items: list[CartItemCreate] = Field(default_factory=list)
    payment: PaymentCreate | None = None


class OrderOut(BaseModel):
    order_number: str
    status: OrderStatus = OrderStatus.CREATED
    order_date: str | None = None
    items: list[CartItemOut]
    payment: PaymentOut | None = None
    shipments: list[ShipmentOut] = Field(default_factory=list)


class NameOut(BaseModel):
    first_name: str
    last_name: str


class PhoneOut(BaseModel):
    country_code: str
    number: str


class AddressOut(BaseModel):
    street: str
    city: str
    state: str
    postal_code: str
    country: str


class AccountOut(BaseModel):
    user_name: str
    status: AccountStatus
    name: NameOut
    shipping_address: AddressOut
    email: str
    phone: PhoneOut
    addresses: list[AddressOut] = []


class LoginPayload(BaseModel):
    email: str = Field(min_length=1)
    password: str = Field(min_length=1)


class RegisterPayload(BaseModel):
    email: str = Field(min_length=1)
    password: str = Field(min_length=8)
    first_name: str = ""
    last_name: str = ""
    phone_country_code: str = ""
    phone_number: str = ""
    street: str = ""
    city: str = ""
    state: str = ""
    postal_code: str = ""
    country: str = ""


class AddressCreate(BaseModel):
    street: str = Field(min_length=1)
    city: str = Field(min_length=1)
    state: str = ""
    postal_code: str = ""
    country: str = ""
    is_default_shipping: bool = False


class AddressUpdate(BaseModel):
    street: str | None = None
    city: str | None = None
    state: str | None = None
    postal_code: str | None = None
    country: str | None = None
    is_default_shipping: bool | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: AccountOut


class AccountUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    phone_number: str | None = None
    phone_country_code: str | None = None


class AccountRole(BaseModel):
    """Role claim embedded in JWT for frontend authorization."""
    role: str = "customer"  # "customer", "manager", or "admin"
