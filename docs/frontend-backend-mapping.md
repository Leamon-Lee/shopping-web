# Frontend-Backend Mapping

## Scope

This document maps the current Python backend domain contract to the current Next.js frontend.

Important constraints:

* The backend remains the source of truth.
* The frontend should adapt through TypeScript types, API services, and adapter functions.
* The current backend has no HTTP API endpoints, no FastAPI routers, no Pydantic DTOs, and no database field contract.
* The current frontend is still mostly Medusa-starter shaped and uses `@medusajs/types` / Medusa SDK data functions.

Because no backend DTOs exist yet, mappings below distinguish:

* Backend domain field names from `docs/backend-contract.md`
* Current frontend/Medusa field names when present
* Recommended frontend domain types and adapter names for a future integration

## 1. Entity Mapping

| Backend entity | Current matching frontend type/interface | Recommended frontend type/interface | Notes |
| --- | --- | --- | --- |
| `Account` | `HttpTypes.StoreCustomer` partially | `BackendAccount`, `FrontendUser` | Current frontend customer lacks `user_name`, `status`, nested `Name`, and backend payment methods. |
| `Customer` | `HttpTypes.StoreCustomer` partially | `BackendCustomer`, `FrontendCustomer` | Backend customer owns cart/orders/search; current frontend customer is Medusa customer profile. |
| `Member` | None direct | `BackendMember`, `FrontendUser` | Represents registered customer with account. |
| `Guest` | None direct | `BackendGuest` | Could map to anonymous visitor/cart state. |
| `Admin` | None direct | `BackendAdmin`, `FrontendAdmin` | Current frontend has no admin UI. |
| `Product` | `HttpTypes.StoreProduct` partially | `BackendProduct`, `FrontendProduct` | Backend uses `name`, `description`, `price`, `available_item_count`, `category`; frontend uses `title`, `handle`, `thumbnail`, variants. |
| `ProductCategory` | `HttpTypes.StoreProductCategory` partially | `BackendProductCategory`, `FrontendCategory` | Backend category lacks handle/id in current domain. |
| `ProductReview` | None direct | `BackendProductReview`, `FrontendProductReview` | No current review UI/type. |
| `Catalog` | Collections/categories/product listing partially | `BackendCatalog`, `FrontendCatalogIndex` | Backend search methods not implemented; frontend currently relies on Medusa list endpoints. |
| `ShoppingCart` | `HttpTypes.StoreCart` partially | `BackendShoppingCart`, `FrontendCart` | Backend cart has `items`; frontend cart has Medusa IDs, region, totals, promotions, shipping methods. |
| `Item` | `HttpTypes.StoreCartLineItem` partially | `BackendCartItem`, `FrontendCartItem` | Backend item uses product/price/quantity; frontend line item uses line ID, variant/product, totals. |
| `Order` | `HttpTypes.StoreOrder` partially | `BackendOrder`, `FrontendOrder` | Backend order has order_number/status/items/logs/shipments/payment; frontend expects Medusa order IDs/items/payment collections. |
| `OrderLog` | None direct | `BackendOrderLog`, `FrontendOrderStatusEvent` | No current frontend timeline type. |
| `Payment` | Payment collection/provider types partially | `BackendPayment`, `FrontendPayment` | Current frontend maps to Medusa payment providers/sessions. |
| `CreditCard` | Stripe card UI only | `BackendCreditCardPaymentMethod`, `FrontendCardPaymentForm` | Sensitive fields should not be returned raw. |
| `CreditCardTransaction` | None direct | `BackendCreditCardTransaction`, `FrontendPaymentTransaction` | Current frontend does not expose this backend transaction model. |
| `ElectronicBankTransfer` | None direct | `BackendBankTransferPaymentMethod`, `FrontendBankTransferForm` | No current bank transfer UI. |
| `ElectronicBankTransaction` | None direct | `BackendBankTransferTransaction`, `FrontendPaymentTransaction` | No current bank transaction UI. |
| `Shipment` | `StoreCartShippingOption` / order shipping display partially | `BackendShipment`, `FrontendShipment` | Backend shipment tracks actual shipment; frontend currently lists shipping options. |
| `ShipmentLog` | None direct | `BackendShipmentLog`, `FrontendShipmentEvent` | No current shipment tracking timeline. |
| `Notification` | None direct | `BackendNotification`, `FrontendNotification` | No current notification UI. |
| `EmailNotification` | None direct | `BackendEmailNotification`, `FrontendNotification` | Notification channel type needed. |
| `SMSNotification` | None direct | `BackendSmsNotification`, `FrontendNotification` | Notification channel type needed. |

## 2. Field Mapping Table

### Account/User Fields

| Backend field name | Backend type | Frontend field name | Frontend type | Conversion needed | Used in frontend |
| --- | --- | --- | --- | --- | --- |
| `user_name` | `Username` | `userName` | `string` | yes: unwrap `Username.value`, snake_case to camelCase | Not currently used; needed for login/profile if backend auth is used. |
| `password` | `Password` | `password` | `string` | yes: frontend sends plain password; backend wraps/validates | Login/register forms currently send `password` to Medusa auth. |
| `status` | `AccountStatus` | `status` | `AccountStatus` union | enum string passthrough | Not currently displayed. |
| `name.first_name` | `Name.first_name` | `firstName` or `first_name` | `string` | yes: naming strategy needed | Account forms currently use Medusa `first_name`. |
| `name.last_name` | `Name.last_name` | `lastName` or `last_name` | `string` | yes: naming strategy needed | Account forms currently use Medusa `last_name`. |
| `shipping_address` | `Address` | `shippingAddress` | `FrontendAddress` | yes: snake_case to camelCase if frontend domain type is camelCase | Checkout/account address UI exists but uses Medusa address fields. |
| `email` | `Email` | `email` | `string` | yes: unwrap `Email.value` | Login/register/profile. |
| `phone.country_code` | `Phone.country_code` | `countryCode` | `string` | yes: snake_case to camelCase | Current forms mostly use flat `phone`. |
| `phone.number` | `Phone.number` | `phoneNumber` or `phone` | `string` | yes: backend splits phone; current frontend uses one phone string | Register/profile/address forms. |
| `credit_card` | `CreditCard \| None` | `creditCard` | masked payment method | yes: never return raw card number/code | Current frontend uses Stripe card element, not backend card object. |
| `electronic_bank_transfer` | `ElectronicBankTransfer \| None` | `electronicBankTransfer` | masked bank method | yes: never return raw account/routing number | Not currently used. |

### Address Fields

| Backend field name | Backend type | Frontend field name | Frontend type | Conversion needed | Used in frontend |
| --- | --- | --- | --- | --- | --- |
| `street` | `str` | `address1` or `address_1` | `string` | yes: backend `street` differs from Medusa `address_1` | Checkout/account address forms. |
| `city` | `str` | `city` | `string` | no if plain value | Checkout/account address forms. |
| `state` | `str` | `province` or `state` | `string` | yes: current frontend uses Medusa `province`; backend uses `state` | Checkout/account address forms. |
| `postal_code` | `str` | `postalCode` or `postal_code` | `string` | yes if camelCase | Checkout/account address forms. |
| `country` | `str` | `countryCode` or `country_code` | `string` | yes: backend says country, frontend expects country code in Medusa forms | Checkout/account address forms. |

### Product and Category Fields

| Backend field name | Backend type | Frontend field name | Frontend type | Conversion needed | Used in frontend |
| --- | --- | --- | --- | --- | --- |
| `name` | `ProductName` | `title` or `name` | `string` | yes: current frontend product cards use `title`; backend uses `name` | Home/store/product cards. |
| `description` | `ProductDescription` | `description` | `string` | yes: unwrap `value` | Product detail. |
| `price` | `Price` | `price.amount` or `price` | `number` | yes: backend simple float; frontend currently computes from Medusa variant prices | Product cards/detail/cart item. |
| `available_item_count` | `ProductCount` | `availableItemCount` or `inventoryQuantity` | `number` | yes: snake_case to camelCase, unwrap `value` | Product detail/add-to-cart availability. |
| `category` | `ProductCategory` | `category` | `FrontendCategory` | yes: nested object mapping | Store filters/category pages. |
| `ProductCategory.name` | `CategoryName` | `name` or `title` | `string` | yes: unwrap `value`; current category displays `name` | Category nav/pages. |
| `ProductCategory.description` | `CategoryDescription` | `description` | `string` | yes: unwrap `value` | Category detail/SEO; not currently prominent. |
| `rating` | `Rating` | `rating` | `number` | yes: unwrap `value` | Review UI not currently present. |
| `review` | `ReviewContent` | `review` or `content` | `string` | yes: name decision needed | Review UI not currently present. |

### Cart and Item Fields

| Backend field name | Backend type | Frontend field name | Frontend type | Conversion needed | Used in frontend |
| --- | --- | --- | --- | --- | --- |
| `items` | `list[Item]` | `items` | `FrontendCartItem[]` | yes: map item/product/price fields | Cart page/dropdown/checkout summary. |
| `Item.quantity` | `Quantity` | `quantity` | `number` | yes: unwrap `value` | Cart item selector. |
| `Item.price` | `Price` | `unitPrice` or `price` | `number` | yes: unwrap `value` | Cart line item, summary. |
| `Item.product` | `Product` | `product` | `FrontendProduct` | yes: product adapter | Cart item/product link. |

Current frontend also sends Medusa-only cart fields that the Python backend does not define:

* `variant_id`
* `region_id`
* `locale`
* `shipping_methods`
* `promotions`
* `metadata`

These must be removed or translated when integrating with the Python backend.

### Order Fields

| Backend field name | Backend type | Frontend field name | Frontend type | Conversion needed | Used in frontend |
| --- | --- | --- | --- | --- | --- |
| `order_number` | `OrderNumber` | `orderNumber` | `string` | yes: unwrap `value`; clarify `OrderId` mismatch | Order confirmation/details. |
| `status` | `OrderStatus` | `status` | `OrderStatus` union | enum string passthrough | Order cards/details. |
| `order_date` | `OrderDate \| None` | `orderDate` | `string \| null` | yes: backend `object` must become serializable date | Order cards/details. |
| `items` | `list[Item]` | `items` | `FrontendCartItem[]` | yes: item adapter | Order details. |
| `order_logs` | `list[OrderLog]` | `orderLogs` | `FrontendOrderStatusEvent[]` | yes: snake_case to camelCase | Not currently used. |
| `shipments` | `list[Shipment]` | `shipments` | `FrontendShipment[]` | yes: shipment adapter | Shipping details/tracking. |
| `payment` | `Payment \| None` | `payment` | `FrontendPayment \| null` | yes: payment adapter | Order payment details. |

### Payment Fields

| Backend field name | Backend type | Frontend field name | Frontend type | Conversion needed | Used in frontend |
| --- | --- | --- | --- | --- | --- |
| `status` | `PaymentStatus` | `status` | `PaymentStatus` union | enum string passthrough | Checkout/order payment status. |
| `amount` | `Amount \| float \| None` | `amount` | `number \| null` | yes: unwrap `Amount.value` when object | Cart/order totals. |
| `currency` | `str \| None` | `currencyCode` or `currency` | `string \| null` | yes if frontend uses `currencyCode` | Price display. |
| `name_on_card` | `Name` | `nameOnCard` | `FrontendName` or `string` | yes | Payment form only; do not display raw card details. |
| `card_number` | `CardNumber` | `cardNumber` | `string` | yes: input only, do not return | Stripe UI currently handles this outside backend. |
| `code` | `SecurityCode` | `code` or `securityCode` | `string` | yes: input only, do not return | Payment form only. |
| `billing_address` | `Address` | `billingAddress` | `FrontendAddress` | yes | Checkout billing form. |
| `bank_name` | `BankName` | `bankName` | `string` | yes | Bank-transfer UI missing. |
| `routing_number` | `RoutingNumber` | `routingNumber` | `string` | yes | Bank-transfer UI missing. |
| `account_number` | `AccountNumber` | `accountNumber` | `string` | yes | Bank-transfer UI missing. |

### Shipment and Notification Fields

| Backend field name | Backend type | Frontend field name | Frontend type | Conversion needed | Used in frontend |
| --- | --- | --- | --- | --- | --- |
| `shipment_date` | `ShipmentDate` | `shipmentDate` | `string` | yes: serialize backend object | Shipment details missing. |
| `estimated_arrival` | `EstimatedArrival` | `estimatedArrival` | `string` | yes: serialize backend object | Shipment details missing. |
| `shipment_method` | `ShipmentMethod` | `shipmentMethod` | `string` | yes: unwrap `value` | Shipping display. |
| `shipment_logs` | `list[ShipmentLog]` | `shipmentLogs` | `FrontendShipmentEvent[]` | yes | Tracking timeline missing. |
| `ShipmentLog.status` | `ShipmentStatus` | `status` | `ShipmentStatus` union | enum string passthrough | Tracking timeline missing. |
| `creation_date` | `CreationDate` | `creationDate` | `string` | yes: serialize backend object | Order/shipment timelines. |
| `notification_id` | `NotificationId` | `notificationId` | `number` | yes: unwrap `value` | Notification UI missing. |
| `created_on` | `CreationDate` | `createdOn` | `string` | yes: serialize backend object | Notification UI missing. |
| `content` | `NotificationContent` | `content` | `string` | yes: unwrap `value` | Notification UI missing. |
| `email` | `Email` | `email` | `string` | yes: unwrap `value` | Notification recipient display if needed. |
| `phone` | `Phone` | `phone` | `string` or structured phone | yes | Notification recipient display if needed. |

## 3. API Payload Mapping

There are no implemented backend API endpoints yet. The mappings below are recommended future mappings for frontend adapters. They are not active endpoint contracts.

### Product Listing/Search

| Layer | Shape |
| --- | --- |
| Frontend request object | `{ query?: string; categoryName?: string; page?: number; limit?: number }` |
| Backend request payload | No endpoint yet. Domain service currently has `CatalogService.search(query: str)` and `Catalog.search_products_by_name(ProductName)` / `search_products_by_category(CategoryName)` stubs. |
| Backend response payload | No DTO yet. Should eventually return products with `name`, `description`, `price`, `available_item_count`, `category`. |
| Frontend display object | `FrontendProduct[]` with `name/title`, `description`, `price`, `availableItemCount`, `category`, and any image/slug fields once backend provides them. |

### Product Detail

| Layer | Shape |
| --- | --- |
| Frontend request object | `{ productId: string \| number }` or `{ handle: string }` if backend adds slugs |
| Backend request payload | No endpoint yet. Backend `Product` currently has no explicit exposed ID field in constructor. |
| Backend response payload | `Product` DTO needed. |
| Frontend display object | `FrontendProduct` with product details and category. |

### Create/Update Product

| Layer | Shape |
| --- | --- |
| Frontend request object | `{ name: string; description: string; price: number; availableItemCount: number; categoryId?: number; categoryName?: string }` |
| Backend request payload | `{ name: { value } \| string; description: { value } \| string; price: { value } \| number; available_item_count: { value } \| number; category: ProductCategory reference }` depending on DTO decision. |
| Backend response payload | Created/updated `Product` DTO. |
| Frontend display object | `FrontendProduct`. |

### Category List/Create/Update

| Layer | Shape |
| --- | --- |
| Frontend request object | List: `{}`. Create/update: `{ name: string; description: string }` |
| Backend request payload | `{ name: CategoryName/string; description: CategoryDescription/string }` |
| Backend response payload | `ProductCategory` DTO. |
| Frontend display object | `FrontendCategory`. |

### Cart

| Layer | Shape |
| --- | --- |
| Frontend request object | Get cart: `{}` or `{ cartId }`. Add item: `{ productId; quantity }`. Update item: `{ itemId; quantity }`. |
| Backend request payload | No endpoint yet. Domain `ShoppingCart.add_item()` and `Item.update_quantity()` do not currently accept arguments. |
| Backend response payload | `ShoppingCart` DTO with `items`. |
| Frontend display object | `FrontendCart` with mapped `FrontendCartItem[]`, totals computed by frontend or backend. |

### Place Order

| Layer | Shape |
| --- | --- |
| Frontend request object | `{ items; shippingAddress; paymentMethod; customer/contact }` |
| Backend request payload | No endpoint yet. Service accepts an already-created `Order` object through `OrderService.place_order(order)`. |
| Backend response payload | `Order` DTO with `order_number`, `status`, `items`, `payment`, `shipments`. |
| Frontend display object | `FrontendOrder`. |

### Payment

| Layer | Shape |
| --- | --- |
| Frontend request object | Card: `{ amount; currency; card; billingAddress }`. Bank: `{ amount; bankName; routingNumber; accountNumber }`. |
| Backend request payload | No endpoint yet. Service accepts `Payment` object through `PaymentService.process_payment(payment)`. |
| Backend response payload | `Payment` DTO with safe fields only: `status`, `amount`, `currency`, masked method summary if needed. |
| Frontend display object | `FrontendPayment` / checkout payment result. |

### Account/Auth

| Layer | Shape |
| --- | --- |
| Frontend request object | Login: `{ userName; password }`. Register: `{ userName; password; firstName; lastName; email; phone; shippingAddress }`. |
| Backend request payload | No endpoint yet. Would map to `Account`, `Member`, and `Customer` constructors. |
| Backend response payload | Safe account/customer DTO. Never include `password`, raw card number, security code, raw bank account number. |
| Frontend display object | `FrontendUser` / session object. |

### Shipment Tracking

| Layer | Shape |
| --- | --- |
| Frontend request object | `{ orderNumber }` or `{ shipmentId }` once IDs exist |
| Backend request payload | No endpoint yet. Domain has `Shipment` and `ShipmentLog`. |
| Backend response payload | `Shipment` DTO with `shipment_date`, `estimated_arrival`, `shipment_method`, `shipment_logs`. |
| Frontend display object | `FrontendShipment` with tracking events. |

### Notifications

| Layer | Shape |
| --- | --- |
| Frontend request object | `{ accountId?; channel? }` once IDs/auth exist |
| Backend request payload | No endpoint yet. Domain has `Notification`, `EmailNotification`, `SMSNotification`. |
| Backend response payload | Notification DTO with `notification_id`, `created_on`, `content`, channel metadata. |
| Frontend display object | `FrontendNotification[]`. |

## 4. Naming Mismatch Analysis

### snake_case vs camelCase

Fields likely to need snake_case-to-camelCase conversion:

* `user_name` -> `userName`
* `first_name` -> `firstName`
* `last_name` -> `lastName`
* `shipping_address` -> `shippingAddress`
* `billing_address` -> `billingAddress`
* `credit_card` -> `creditCard`
* `electronic_bank_transfer` -> `electronicBankTransfer`
* `available_item_count` -> `availableItemCount`
* `product_names` -> `productNames`
* `product_categories` -> `productCategories`
* `last_updated` -> `lastUpdated`
* `order_number` -> `orderNumber`
* `order_date` -> `orderDate`
* `order_logs` -> `orderLogs`
* `shipment_date` -> `shipmentDate`
* `estimated_arrival` -> `estimatedArrival`
* `shipment_method` -> `shipmentMethod`
* `shipment_logs` -> `shipmentLogs`
* `creation_date` -> `creationDate`
* `created_on` -> `createdOn`
* `notification_id` -> `notificationId`
* `name_on_card` -> `nameOnCard`
* `card_number` -> `cardNumber`
* `routing_number` -> `routingNumber`
* `account_number` -> `accountNumber`
* `country_code` -> `countryCode`
* `postal_code` -> `postalCode`

### Different Names

Backend and current frontend use meaningfully different names:

| Backend | Current frontend/Medusa | Issue |
| --- | --- | --- |
| `Product.name` | `StoreProduct.title` | Product adapter must rename. |
| `Product.price` | variant calculated prices | Backend has simple price; frontend expects variant pricing. |
| `Product.available_item_count` | `inventory_quantity` on variants | Inventory model differs. |
| `ProductCategory.name` | `StoreProductCategory.name` | Mostly compatible, but frontend also expects `handle`, parent/children. |
| `Address.street` | `address_1` | Address adapter must map. |
| `Address.state` | `province` | Address adapter must map. |
| `Address.country` | `country_code` | Backend may store country name; frontend often expects ISO code. |
| `Order.order_number` | `order.id` / display ID | Need backend ID/order-number decision. |
| `Item.product` | line item product + variant | Backend has no variants. |
| `Payment.currency` | `currency_code` | Naming differs. |

### Frontend Missing Required Backend Fields

Current frontend forms/data objects do not reliably include:

* `user_name` for backend account login/register; current login uses email.
* Structured `Name` object for account/cardholder; current forms often use flat `first_name` / `last_name`.
* Structured `Phone` with `country_code` and `number`; current frontend often uses flat `phone`.
* Backend `Address.street`; current forms use `address_1`.
* `Product.available_item_count`.
* Required product `category` in current static homepage product cards.
* `ProductCategory.description` in category-oriented UI.
* `Order.order_number` as a required backend constructor field.
* `Shipment.shipment_date`, `estimated_arrival`, and `shipment_method`.

### Frontend Sends Fields Backend Does Not Accept

Current Medusa frontend data functions send or expect fields not present in the Python backend domain:

* Product/query fields: `region_id`, `fields`, `variants`, `calculated_price`, `thumbnail`, `handle`, `metadata`, `tags`.
* Cart fields: `variant_id`, `region_id`, `locale`, `shipping_methods`, `promotions`.
* Customer fields: `company`, `address_1`, `address_2`, `province`, `country_code`, `is_default_billing`, `is_default_shipping`.
* Order transfer fields: `token`, transfer request objects.
* Shipping option fields: `shipping_option`, `cart_id`, arbitrary `data`.
* Payment provider fields: `payment_provider`, `provider_id`, Stripe/Medusa payment provider IDs.

These should not be sent to the Python backend unless corresponding DTO fields are explicitly added.

### Value Object Shape Mismatch

The backend uses value objects such as `ProductName(value)`, `Price(value)`, and `Name(first_name, last_name)`.

The frontend should not expose this implementation detail directly unless the backend API serializes value objects as wrappers. Preferred adapter approach:

* Backend DTOs can remain snake_case and value-object-aware.
* Frontend display objects should use simple render-ready primitives.
* Adapter functions should unwrap/wrap values at the API boundary.

## 5. Recommended Frontend Adapters

Create frontend adapters in a dedicated location such as `frontend/src/lib/adapters/backend/*` once API integration starts.

### Product Adapters

Recommended functions:

```ts
mapBackendProductToFrontendProduct(backend: BackendProduct): FrontendProduct
mapFrontendProductFormToCreateProductPayload(form: ProductFormValues): CreateProductPayload
mapFrontendProductFormToUpdateProductPayload(form: ProductFormValues): UpdateProductPayload
mapBackendCategoryToFrontendCategory(backend: BackendProductCategory): FrontendCategory
mapFrontendCategoryFormToPayload(form: CategoryFormValues): ProductCategoryPayload
```

Responsibilities:

* Map `name` to `title` or standardize frontend on `name`.
* Unwrap `ProductName.value`, `ProductDescription.value`, `Price.value`, and `ProductCount.value` if API uses value-object wrappers.
* Map `available_item_count` to `availableItemCount`.
* Provide placeholder/optional image fields because backend currently has no image model.
* Avoid assuming product `handle` exists until backend adds one.

### User/Account Adapters

Recommended functions:

```ts
mapBackendAccountToFrontendUser(account: BackendAccount): FrontendUser
mapFrontendLoginFormToLoginPayload(form: LoginFormValues): LoginPayload
mapFrontendRegisterFormToCreateAccountPayload(form: RegisterFormValues): CreateAccountPayload
mapFrontendProfileFormToUpdateAccountPayload(form: ProfileFormValues): UpdateAccountPayload
```

Responsibilities:

* Map `user_name` to `userName`.
* Map `Name(first_name, last_name)` to frontend name fields.
* Map backend structured `Phone` to frontend phone display/input shape.
* Never map backend `password` into frontend display state.
* Never expose raw card/bank details.

### Address Adapters

Recommended functions:

```ts
mapBackendAddressToFrontendAddress(address: BackendAddress): FrontendAddress
mapFrontendAddressFormToBackendAddressPayload(form: AddressFormValues): BackendAddressPayload
```

Responsibilities:

* Map `street` to current frontend `address1`/`address_1` equivalent.
* Map `state` to `province` only if maintaining Medusa-form compatibility.
* Decide whether `country` should be country name or ISO code before API integration.
* Preserve backend required fields: street, city, state, postal_code, country.

### Cart Adapters

Recommended functions:

```ts
mapBackendCartToFrontendCart(cart: BackendShoppingCart): FrontendCart
mapBackendItemToFrontendCartItem(item: BackendItem): FrontendCartItem
mapFrontendAddToCartToBackendPayload(input: AddToCartInput): AddCartItemPayload
mapFrontendQuantityUpdateToBackendPayload(input: UpdateCartQuantityInput): UpdateCartItemPayload
```

Responsibilities:

* Map `Item.quantity.value` to `quantity`.
* Map `Item.price.value` to unit price or line subtotal depending on backend DTO.
* Remove Medusa-only `variant_id` unless backend adds variants.
* Compute cart totals on frontend only if backend does not return totals.

### Order Adapters

Recommended functions:

```ts
mapBackendOrderToFrontendOrder(order: BackendOrder): FrontendOrder
mapFrontendOrderFormToCreateOrderPayload(form: OrderFormValues): CreateOrderPayload
mapBackendOrderLogToFrontendStatusEvent(log: BackendOrderLog): FrontendOrderStatusEvent
```

Responsibilities:

* Map `order_number` to `orderNumber`.
* Map `order_date` to an ISO string/date display object.
* Map `order_logs` to timeline events.
* Map nested `items`, `payment`, and `shipments`.
* Handle enum values directly as strings.
* Track the unresolved `OrderNumber` vs `OrderId` contract gap.

### Payment Adapters

Recommended functions:

```ts
mapBackendPaymentToFrontendPayment(payment: BackendPayment): FrontendPayment
mapFrontendCardPaymentFormToBackendPayload(form: CardPaymentFormValues): CreditCardPaymentPayload
mapFrontendBankTransferFormToBackendPayload(form: BankTransferFormValues): BankTransferPaymentPayload
```

Responsibilities:

* Map `PaymentStatus` enum strings directly.
* Map `Amount.value` or raw float to `amount`.
* Map `currency` to `currencyCode` if frontend standardizes on that.
* Treat `card_number`, `code`, `routing_number`, and `account_number` as write-only fields.
* Prefer tokenized payment methods if backend later supports a payment gateway.

### Shipment Adapters

Recommended functions:

```ts
mapBackendShipmentToFrontendShipment(shipment: BackendShipment): FrontendShipment
mapBackendShipmentLogToFrontendShipmentEvent(log: BackendShipmentLog): FrontendShipmentEvent
mapFrontendShipmentFormToBackendPayload(form: ShipmentFormValues): ShipmentPayload
```

Responsibilities:

* Map `shipment_date`, `estimated_arrival`, and `creation_date` to serializable strings.
* Map `shipment_method.value` to display text.
* Map `ShipmentStatus` enum strings directly.

### Notification Adapters

Recommended functions:

```ts
mapBackendNotificationToFrontendNotification(notification: BackendNotification): FrontendNotification
mapBackendEmailNotificationToFrontendNotification(notification: BackendEmailNotification): FrontendNotification
mapBackendSmsNotificationToFrontendNotification(notification: BackendSmsNotification): FrontendNotification
```

Responsibilities:

* Map `notification_id` to `notificationId`.
* Map `created_on` to `createdOn`.
* Unwrap `content.value`.
* Represent channel-specific recipient fields safely.

## Recommended Type Layers

Use separate types for each layer:

1. `Backend*Payload` / `Backend*Response`: mirrors backend DTOs exactly, likely snake_case.
2. `Frontend*`: render-ready camelCase objects used by components.
3. `*FormValues`: form state objects matching frontend controls.
4. Adapter functions: the only place where naming, value-object wrappers, date serialization, and sensitive-field filtering happen.

This separation allows the backend to remain unchanged while the frontend adapts cleanly.

## Integration Warnings

* Do not reuse Medusa `HttpTypes` as the long-term contract for this Python backend.
* Do not make frontend components depend on backend private attribute names such as `__name` or `__price`.
* Do not assume current Medusa routes map to the Python backend.
* Do not send Medusa-only fields to the Python backend without backend DTO support.
* Do not return sensitive payment fields to the frontend.
* Do not implement adapters until backend API DTOs or endpoint paths are defined.
