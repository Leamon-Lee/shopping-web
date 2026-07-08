# Backend Contract

## Current Backend Shape

The backend is now organized as a standalone FastAPI project under `backend/`.

The source of truth remains the domain layer under `backend/src/online_shopping/domain` and the simple service layer under `backend/src/online_shopping/services`. The FastAPI boundary is under `backend/src/online_shopping/api` and exposes Pydantic DTOs with backend-style snake_case fields.

Current API scope is intentionally small and in-memory: products, categories, cart, orders, payment processing, and health checks. There is still no database, ORM mapping, persistence, or authentication middleware.

## Backend Entity/Class Summary

### Account

Source: `backend/src/online_shopping/domain/entities/account.py`

Fields from constructor:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `user_name` | `Username` | yes | Username value object. |
| `password` | `Password` | yes | Password value object. Do not expose back to frontend. |
| `status` | `AccountStatus` | yes | Account state enum. |
| `name` | `Name` | yes | Customer name value object. |
| `shipping_address` | `Address` | yes | Primary shipping address. |
| `email` | `Email` | yes | Email value object. |
| `phone` | `Phone` | yes | Phone value object. |
| `credit_card` | `CreditCard \| None` | no | Optional payment method. Sensitive fields. |
| `electronic_bank_transfer` | `ElectronicBankTransfer \| None` | no | Optional payment method. Sensitive fields. |
| `members` | `list[Member] \| None` | no | Defaults to empty list. |
| `admins` | `list[Admin] \| None` | no | Defaults to empty list. |

Relationships:

* Account may have one credit card.
* Account may have one electronic bank transfer method.
* Account may relate to members and admins.
* Account owns a shipping address and contact information.

Public behavior:

* `get_shipping_address() -> Address`
* `add_product_review() -> bool` is not implemented.
* `add_product() -> bool` is not implemented.

### Customer, Member, Guest, Admin

Sources:

* `backend/src/online_shopping/domain/entities/customer.py`
* `backend/src/online_shopping/domain/entities/member.py`
* `backend/src/online_shopping/domain/entities/guest.py`
* `backend/src/online_shopping/domain/entities/admin.py`

Customer fields:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `shopping_cart` | `ShoppingCart` | yes | Current customer cart. |
| `orders` | `list[Order] \| None` | no | Defaults to empty list. |
| `search` | `Search \| None` | no | Optional search capability. |

Member fields:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `account` | `Account` | yes | Member is a registered customer with account. |
| `*args`, `**kwargs` | Customer constructor args | yes | Passed to `Customer`. |

Guest behavior:

* `register_account() -> bool` is not implemented.

Admin fields:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `account` | `Account` | yes | Admin account. |
| `products` | `list[Product] \| None` | no | Defaults to empty list. |
| `product_categories` | `list[ProductCategory] \| None` | no | Defaults to empty list. |

Admin behavior:

* `block_user() -> bool` is not implemented.
* `add_new_product_category() -> bool` is not implemented.
* `modify_product_category() -> bool` is not implemented.

### Product, ProductCategory, ProductReview, Catalog

Sources:

* `backend/src/online_shopping/domain/entities/product.py`
* `backend/src/online_shopping/domain/entities/product_category.py`
* `backend/src/online_shopping/domain/entities/product_review.py`
* `backend/src/online_shopping/domain/entities/catalog.py`

Product fields:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `name` | `ProductName` | yes | Non-empty product name. |
| `description` | `ProductDescription` | yes | String, max 500 characters. |
| `price` | `Price` | yes | Must be greater than zero. |
| `available_item_count` | `ProductCount` | yes | Inventory count value object. |
| `category` | `ProductCategory` | yes | Product category relationship. |

Product behavior:

* `get_available_count() -> ProductCount`

ProductCategory fields:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `name` | `CategoryName` | yes | Category label. |
| `description` | `CategoryDescription` | yes | Category description. |

ProductReview fields:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `rating` | `Rating` | yes | Rating value object. |
| `review` | `ReviewContent` | yes | Review text. |
| `product` | `Product` | yes | Reviewed product. |

ProductReview behavior:

* `get_rating() -> Rating`

Catalog fields:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `last_updated` | `CreationDate` | yes | Last catalog update timestamp. |
| `product_names` | `ProductNameMap` | yes | Product-name search index. |
| `product_categories` | `ProductCategoryMap` | yes | Category search index. |
| `name` | `Name` | yes | Catalog name uses the shared `Name` value object. |
| `products` | `list[Product] \| None` | no | Defaults to empty list. |

Catalog behavior:

* `search_products_by_name(name: ProductName) -> list[Product]` is not implemented.
* `search_products_by_category(category: CategoryName) -> list[Product]` is not implemented.

### ShoppingCart and Item

Sources:

* `backend/src/online_shopping/domain/entities/shopping_cart.py`
* `backend/src/online_shopping/domain/entities/item.py`

ShoppingCart fields:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `items` | `list[Item] \| None` | no | Defaults to empty list. Exposed as read-only tuple through property. |

ShoppingCart behavior:

* `items -> tuple[Item, ...]`
* `get_items() -> list[Item]`
* `add_item() -> bool` is not implemented.
* `remove_item() -> bool` is not implemented.

Item fields:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `quantity` | `Quantity` | yes | Quantity value object. No validation currently enforced. |
| `price` | `Price` | yes | Must be greater than zero. |
| `product` | `Product` | yes | Product relationship. |

Item behavior:

* `update_quantity() -> bool` is not implemented.

### Order and OrderLog

Sources:

* `backend/src/online_shopping/domain/entities/order.py`
* `backend/src/online_shopping/domain/entities/order_log.py`

Order fields:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `order_number` | `OrderNumber` | yes | Constructor annotation says `OrderNumber`. Current tests pass `OrderId`, so this needs clarification before API exposure. |
| `status` | `OrderStatus` | no | Defaults to `OrderStatus.PENDING`. |
| `order_date` | `OrderDate \| None` | no | Optional date wrapper. |
| `items` | `list[Item] \| None` | no | Defaults to empty list. |
| `order_logs` | `list[OrderLog] \| None` | no | Defaults to empty list. |
| `shipments` | `list[Shipment] \| None` | no | Defaults to empty list. |
| `payment` | `Payment \| None` | no | Optional payment relationship. |

Order behavior:

* `order_number -> OrderNumber`
* `status -> OrderStatus`
* `send_for_shipment() -> bool` is not implemented.

OrderLog fields:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `creation_date` | `CreationDate` | yes | Timestamp wrapper. |
| `status` | `OrderStatus` | yes | Order status at log time. |
| `notifications` | `list[Notification] \| None` | no | Defaults to empty list. |

### Payment and Payment Methods

Sources:

* `backend/src/online_shopping/domain/entities/payment.py`
* `backend/src/online_shopping/domain/entities/credit_card.py`
* `backend/src/online_shopping/domain/entities/credit_card_transaction.py`
* `backend/src/online_shopping/domain/entities/electronic_bank_transfer.py`
* `backend/src/online_shopping/domain/entities/electronic_bank_transaction.py`

Payment fields:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `status` | `PaymentStatus \| int` | no | Defaults to `PaymentStatus.PENDING`. Invalid non-`PaymentStatus` values are coerced to `PENDING`. |
| `amount` | `Amount \| float \| None` | no | Payment amount. |
| `currency` | `str \| None` | no | Optional currency string. No validation currently enforced. |

Payment behavior:

* `amount -> Amount | float | None`
* `status -> PaymentStatus`
* `process_payment() -> PaymentStatus` is not implemented.

CreditCard fields:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `name_on_card` | `Name` | yes | Cardholder name. |
| `card_number` | `CardNumber` | yes | 13 to 19 digits after spaces are removed. Sensitive. |
| `code` | `Code` / `SecurityCode` | yes | 3 or 4 digits. Sensitive. |
| `billing_address` | `BillingAddress` | yes | Alias of `Address`. |

CreditCardTransaction fields:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `credit_card` | `CreditCard` | yes | Payment method relationship. |
| `status` | `PaymentStatus` | no | Defaults to `PENDING`. |
| `amount` | `Amount \| float \| None` | no | Optional amount. |

ElectronicBankTransfer fields:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `bank_name` | `BankName` | yes | Bank name. |
| `routing_number` | `RoutingNumber` | yes | Routing number. Sensitive. |
| `account_number` | `AccountNumber` | yes | Bank account number. Sensitive. |

ElectronicBankTransaction fields:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `electronic_bank_transfer` | `ElectronicBankTransfer` | yes | Payment method relationship. |
| `status` | `PaymentStatus` | no | Defaults to `PENDING`. |
| `amount` | `Amount \| float \| None` | no | Optional amount. |

### Shipment and ShipmentLog

Sources:

* `backend/src/online_shopping/domain/entities/shipment.py`
* `backend/src/online_shopping/domain/entities/shipment_log.py`

Shipment fields:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `shipment_date` | `ShipmentDate` | yes | Date wrapper. |
| `estimated_arrival` | `EstimatedArrival` | yes | Date wrapper. |
| `shipment_method` | `ShipmentMethod` | yes | Shipping method string wrapper. |
| `shipment_logs` | `list[ShipmentLog] \| None` | no | Defaults to empty list. |

Shipment behavior:

* `add_shipment_log() -> bool` is not implemented.

ShipmentLog fields:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `status` | `ShipmentStatus` | yes | Shipment state. |
| `creation_date` | `CreationDate` | yes | Log timestamp wrapper. |
| `notifications` | `list[Notification] \| None` | no | Defaults to empty list. |

### Notification

Sources:

* `backend/src/online_shopping/domain/entities/notification.py`
* `backend/src/online_shopping/domain/entities/email_notification.py`
* `backend/src/online_shopping/domain/entities/sms_notification.py`

Notification fields:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `notification_id` | `NotificationId` | yes | Notification identifier. |
| `created_on` | `CreationDate` | yes | Creation timestamp. |
| `content` | `NotificationContent` | yes | Notification body. |

Notification behavior:

* `send_notification() -> bool` is not implemented.

EmailNotification extra field:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `email` | `Email` | yes | Recipient email. |

SMSNotification extra field:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `phone` | `Phone` | yes | Recipient phone. |

## Value Objects and Validation Rules

| Value object | Backend fields | Type | Validation |
| --- | --- | --- | --- |
| `Username` | `value` | `str` | Trimmed. Required. 3 to 20 characters. |
| `Password` | `value` | `str` | At least 8 characters. |
| `CustomerId` | `value` | `int` | Positive integer. |
| `Name` | `first_name`, `last_name` | `str` | Both non-empty, trimmed. |
| `Email` | `value` | `str` | Must match basic email regex, trimmed. |
| `Phone` | `country_code`, `number` | `str` | Both non-empty, trimmed. |
| `Address` | `street`, `city`, `state`, `postal_code`, `country` | `str` | All non-empty, trimmed. |
| `ProductId` | `value` | `int` | Positive integer. |
| `ProductName` | `value` | `str` | Required, trimmed. |
| `Price` | `value` | `float` | Number greater than zero, coerced to float. |
| `ProductDescription` | `value` | `str` | String, max 500 characters, trimmed. |
| `ProductCount` | `value` | `int` | No current validation. |
| `CategoryName` | `value` | `str` | No current validation. |
| `CategoryDescription` | `value` | `str` | No current validation. |
| `Quantity` | `value` | `int` | No current validation. |
| `Rating` | `value` | `int` | No current validation. |
| `ReviewContent` | `value` | `str` | No current validation. |
| `OrderId` | `value` | `int` | Positive integer. |
| `OrderNumber` | `value` | `str` | No current validation. |
| `OrderDate` | `value` | `object` | No current validation. |
| `CreationDate` | `value` | `object` | No current validation. |
| `CardNumber` | `value` | `str` | 13 to 19 digits after spaces removed. |
| `SecurityCode` / `Code` | `value` | `str` | 3 or 4 digits. |
| `BankName` | `value` | `str` | No current validation. |
| `RoutingNumber` | `value` | `str` | No current validation. |
| `AccountNumber` | `value` | `str` | No current validation. |
| `Amount` | `value` | `float` | No current validation. |
| `TrackingNumber` | `value` | `str` | Required, trimmed. |
| `ShipmentDate` | `value` | `object` | No current validation. |
| `EstimatedArrival` | `value` | `object` | No current validation. |
| `ShipmentMethod` | `value` | `str` | No current validation. |
| `Message` | `value` | `str` | Required, trimmed. |
| `NotificationId` | `value` | `int` | No current validation. |
| `NotificationContent` | `value` | `str` | No current validation. |

## Enum/Status Values

### AccountStatus

Values:

* `active`
* `blocked`
* `banned`
* `compromised`
* `archived`
* `unknown`

### OrderStatus

Values:

* `unshipped`
* `pending`
* `shipped`
* `complete`
* `canceled`
* `refund_applied`

Default for `Order`: `pending`.

### PaymentStatus

Values:

* `unpaid`
* `pending`
* `completed`
* `failed`
* `declined`
* `canceled`
* `abandoned`
* `settling`
* `settled`
* `refunded`

Default for `Payment`: `pending`.

### ShipmentStatus

Values:

* `pending`
* `shipped`
* `delivered`
* `on_hold`

## Service Layer Summary

Sources: `backend/src/online_shopping/services`

| Service | Method | Input | Output | Current behavior |
| --- | --- | --- | --- | --- |
| `CatalogService` | `search(query: str)` | Search text | `list[object]` | Returns `[]`, including for non-empty queries. |
| `OrderService` | `place_order(order: Order)` | `Order` | `Order` | Returns the same order object. |
| `PaymentService` | `process_payment(payment: Payment)` | `Payment` | `Payment` | Returns the same payment object. |
| `ShipmentService` | `ship(shipment: Shipment)` | `Shipment` | `Shipment` | Returns the same shipment object. |

## API Endpoint Summary

FastAPI entry point: `backend/src/online_shopping/api/app.py`

Run target:

| Command target | Purpose | Notes |
| --- | --- | --- |
| `backend/main.py` | Starts uvicorn for `online_shopping.api.app:app` | Defaults to `0.0.0.0:8001`. |

Current endpoints:

| Method | Path | Purpose | Request body | Response body | Query parameters | Path parameters | Auth |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `GET` | `/health` | Backend health check | none | `{ "status": "ok" }` | none | none | none |
| `GET` | `/products` | List products | none | `list[ProductOut]` | none | none | none |
| `POST` | `/products` | Create product | `ProductCreate` | `ProductOut` | none | none | none |
| `GET` | `/products/categories` | List product categories | none | `list[CategoryOut]` | none | none | none |
| `GET` | `/products/{product_name}` | Get product by name | none | `ProductOut` | none | `product_name` | none |
| `GET` | `/cart` | Get current in-memory cart | none | `ShoppingCartOut` | none | none | none |
| `POST` | `/cart/items` | Add product to cart | `CartItemCreate` | `ShoppingCartOut` | none | none | none |
| `PATCH` | `/cart/items/{product_name}` | Update cart quantity | `CartItemUpdate` | `ShoppingCartOut` | none | `product_name` | none |
| `DELETE` | `/cart/items/{product_name}` | Remove cart item | none | `ShoppingCartOut` | none | `product_name` | none |
| `GET` | `/orders` | List in-memory orders | none | `list[OrderOut]` | none | none | none |
| `POST` | `/orders` | Create order from request items or current cart | `OrderCreate` | `OrderOut` | none | none | none |
| `GET` | `/orders/{order_number}` | Get order by order number | none | `OrderOut` | none | `order_number` | none |
| `POST` | `/payments/process` | Process payment payload | `PaymentCreate` | `PaymentOut` | none | none | none |

## Authentication Requirements

No authentication system is implemented yet.

Domain hints:

* `Account` stores `user_name`, `password`, `status`, identity, contact, and payment method relationships.
* `Member` wraps `Customer` with an `Account`.
* `Guest` has a future `register_account()` behavior.
* `Admin` has future account-management and category/product-management behavior.

Frontend must treat authentication as not yet available until the backend exposes concrete login/register/session endpoints and response models.

## Field Naming Summary

The backend uses Python-style snake_case constructor arguments and value objects. The current frontend is TypeScript/Next.js and may prefer camelCase interfaces, but it must adapt to backend field names once an API layer exists.

Recommended API payload strategy:

| Backend field name | Expected frontend field name if different | Notes |
| --- | --- | --- |
| `user_name` | `userName` | Backend currently uses `user_name`. Keep mapping explicit. |
| `first_name` | `firstName` | Nested under `name`. |
| `last_name` | `lastName` | Nested under `name`. |
| `shipping_address` | `shippingAddress` | Nested `Address`. |
| `billing_address` | `billingAddress` | Alias of `Address`. |
| `credit_card` | `creditCard` | Sensitive. Avoid returning raw card number/code. |
| `electronic_bank_transfer` | `electronicBankTransfer` | Sensitive. Avoid returning raw account/routing numbers. |
| `available_item_count` | `availableItemCount` | Product inventory. |
| `product_categories` | `productCategories` | Catalog category index. |
| `product_names` | `productNames` | Catalog name index. |
| `last_updated` | `lastUpdated` | Catalog timestamp. |
| `order_number` | `orderNumber` | Clarify whether this is separate from `OrderId`. |
| `order_date` | `orderDate` | Date wrapper currently uses `object`. |
| `order_logs` | `orderLogs` | List of order status logs. |
| `shipment_date` | `shipmentDate` | Date wrapper currently uses `object`. |
| `estimated_arrival` | `estimatedArrival` | Date wrapper currently uses `object`. |
| `shipment_method` | `shipmentMethod` | Shipping method string wrapper. |
| `shipment_logs` | `shipmentLogs` | List of shipment status logs. |
| `creation_date` | `creationDate` | Used by logs. |
| `created_on` | `createdOn` | Used by notifications. |
| `notification_id` | `notificationId` | Notification identifier. |
| `name_on_card` | `nameOnCard` | Sensitive payment method field. |
| `card_number` | `cardNumber` | Sensitive. Should not be returned raw. |
| `routing_number` | `routingNumber` | Sensitive. |
| `account_number` | `accountNumber` | Sensitive. |
| `country_code` | `countryCode` | Phone country/area code. |
| `postal_code` | `postalCode` | Address postal code. |

Value object payloads need a decision:

* Backend-internal shape: `{ "name": { "value": "Desk Shelf" } }`
* Frontend-friendly API shape: `{ "name": "Desk Shelf" }`

No DTOs exist yet, so this is unresolved. The frontend should not hard-code either shape until the backend exposes DTOs.

## Frontend Impact Summary

### Frontend Pages Needed

Based on current backend entities, the frontend needs pages for:

* Product listing/search
* Product detail
* Product categories
* Shopping cart
* Checkout
* Order confirmation
* Order history/details
* Login
* Register account
* Account profile
* Shipping address management
* Payment method management
* Product reviews
* Admin product management
* Admin category management
* Admin account/user management
* Shipment tracking/details
* Notification history or preferences, if exposed

### Frontend Forms Needed

Forms implied by backend entities:

* Login form: `user_name`, `password`
* Register form: username, password, name, email, phone, shipping address
* Profile/contact form: `Name`, `Email`, `Phone`
* Address form: `street`, `city`, `state`, `postal_code`, `country`
* Product form: `name`, `description`, `price`, `available_item_count`, `category`
* Category form: `name`, `description`
* Cart item quantity form/control: `quantity`
* Product review form: `rating`, `review`
* Credit card form: `name_on_card`, `card_number`, `code`, `billing_address`
* Electronic bank transfer form: `bank_name`, `routing_number`, `account_number`
* Shipment form/admin control: `shipment_date`, `estimated_arrival`, `shipment_method`

### Frontend API Functions Needed

No API endpoints exist yet, but frontend integration will eventually need functions for:

* `listProducts`
* `getProduct`
* `searchProductsByName`
* `searchProductsByCategory`
* `listCategories`
* `createCategory` / `updateCategory`
* `getCart`
* `addCartItem`
* `removeCartItem`
* `updateCartItemQuantity`
* `placeOrder`
* `getOrder`
* `listOrders`
* `processPayment`
* `createShipment`
* `getShipment`
* `registerAccount`
* `login`
* `logout`
* `getCurrentAccount`
* `updateAccount`
* `addProductReview`
* `listNotifications`

These function names are frontend suggestions only. The backend must define actual endpoint paths, request bodies, and response models first.

### Frontend Types/Interfaces Needed

Frontend TypeScript types should eventually mirror API DTOs for:

* `Account`
* `AccountStatus`
* `Customer`
* `Member`
* `Admin`
* `Name`
* `Email`
* `Phone`
* `Address`
* `Product`
* `ProductCategory`
* `ProductReview`
* `Catalog`
* `ShoppingCart`
* `CartItem`
* `Order`
* `OrderStatus`
* `OrderLog`
* `Payment`
* `PaymentStatus`
* `CreditCardPaymentMethod`
* `ElectronicBankTransferPaymentMethod`
* `Shipment`
* `ShipmentStatus`
* `ShipmentLog`
* `Notification`

Do not generate frontend types directly from current Python private attributes. Wait for DTOs or explicitly map value objects into API payload shapes.

## Missing Frontend Features

The current frontend is a standalone Medusa-derived storefront and does not yet reflect this Python backend contract.

Backend features that do not yet have confirmed frontend pages:

* Native product catalog backed by `Product` and `ProductCategory`
* Product search by name/category from `Catalog`
* Shopping cart backed by `ShoppingCart` and `Item`
* Order placement backed by `OrderService`
* Order history/details backed by `Order`
* Payment flow backed by `PaymentService`
* Credit-card and bank-transfer payment method management
* Shipment tracking/details backed by `Shipment`
* Account registration/login backed by `Account`, `Member`, and `Guest`
* Admin product/category/account management
* Product review creation/display
* Notification display/delivery preferences

Backend fields not currently displayed in the frontend with this backend contract:

* Account status
* Username
* Full account profile fields
* Shipping/billing address from backend `Address`
* Product inventory count
* Product category description
* Product review rating/content
* Order logs
* Shipment logs
* Payment status
* Shipment status
* Notification content

Backend fields not currently included in frontend forms with this backend contract:

* `available_item_count`
* `category.description`
* `rating`
* `review`
* `shipment_date`
* `estimated_arrival`
* `shipment_method`
* `bank_name`
* `routing_number`
* `account_number`
* `status` fields for account/order/payment/shipment admin workflows

## Contract Gaps To Resolve Before Frontend Integration

1. Add an HTTP API layer or document that no HTTP API is intended.
2. Define Pydantic request/response schemas or another DTO layer.
3. Decide whether JSON uses snake_case or camelCase.
4. Decide whether value objects serialize as `{ value }` wrappers or plain values.
5. Clarify `Order.order_number` versus `OrderId`; tests currently pass `OrderId` to the `Order` constructor.
6. Add explicit IDs to entities that need routing and frontend linking, such as product, category, cart item, account, shipment, and notification.
7. Add validation for currently unvalidated value objects such as `Quantity`, `Rating`, `Amount`, and `ProductCount`.
8. Define authentication/session requirements.
9. Define which sensitive payment fields may be sent to or returned from the frontend.
10. Define database field names if persistence is added.
