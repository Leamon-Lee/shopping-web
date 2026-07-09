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


class ProductOut(ProductBase):
    pass


class CartItemCreate(BaseModel):
    product_name: str = Field(min_length=1)
    quantity: int = Field(ge=1)


class CartItemUpdate(BaseModel):
    quantity: int = Field(ge=1)


class CartItemOut(BaseModel):
    quantity: int = Field(ge=1)
    price: float = Field(gt=0)
    product: ProductOut


class ShoppingCartOut(BaseModel):
    items: list[CartItemOut]
    total_quantity: int
    subtotal: float


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
    street_address: str
    city: str
    state: str
    zip_code: str
    country: str


class AccountOut(BaseModel):
    user_name: str
    status: AccountStatus
    name: NameOut
    shipping_address: AddressOut
    email: str
    phone: PhoneOut
