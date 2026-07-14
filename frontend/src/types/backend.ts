// ── Strict types matching FastAPI Pydantic schemas ──────────────────
// All types match backend online_shopping/api/schemas.py

export type AccountStatus =
  | "active"
  | "blocked"
  | "banned"
  | "compromised"
  | "archived"
  | "unknown"

export type OrderStatus =
  | "created"
  | "confirmed"
  | "processing"
  | "shipped"
  | "completed"
  | "canceled"

export type PaymentStatus =
  | "pending"
  | "completed"
  | "failed"
  | "declined"
  | "canceled"
  | "abandoned"
  | "settling"
  | "settled"
  | "refunded"

export type ShipmentStatus =
  | "pending"
  | "shipped"
  | "delivered"
  | "on_hold"

// ── Account ──────────────────────────────────────────────────────────

export interface Name {
  first_name: string
  last_name: string
}

export interface Phone {
  country_code: string
  number: string
}

export interface Address {
  id?: string
  street: string
  city: string
  state: string
  postal_code: string
  country: string
  is_default_shipping?: boolean
  is_default_billing?: boolean
  // Legacy compatibility
  address_1?: string
  address_2?: string
  company?: string
  country_code?: string
  province?: string
  phone?: string
  first_name?: string
  last_name?: string
  // ISO country code
  iso_2?: string
}

export interface Account {
  user_name: string
  status: AccountStatus
  name: Name
  shipping_address: Address
  email: string
  phone: Phone
  addresses: Address[]
  // Top-level aliases for checkout component compatibility
  first_name?: string
  last_name?: string
}

// ── Auth ─────────────────────────────────────────────────────────────

export interface LoginPayload {
  email: string
  password: string
}

export interface RegisterPayload {
  email: string
  password: string
  first_name?: string
  last_name?: string
  phone_country_code?: string
  phone_number?: string
  street?: string
  city?: string
  state?: string
  postal_code?: string
  country?: string
}

export interface TokenResponse {
  access_token: string
  token_type: "bearer"
  user: Account
}

export interface AccountUpdate {
  first_name?: string | null
  last_name?: string | null
  phone_number?: string | null
  phone_country_code?: string | null
}

// ── Product / Category / Image ───────────────────────────────────────

export interface Category {
  name: string
  description: string
}

export interface ProductImage {
  image_url: string
  url: string | null
  rank: number
}

export interface ProductVariant {
  id: string
  title: string
  name: string
  sku: string
  price: number
  inventory_quantity: number
  inventory_count: number
  manage_inventory: boolean
  allow_backorder: boolean
  product: Record<string, unknown> | null
  options: Record<string, unknown>[]
  // Legacy Medusa compatibility
  calculated_price?: { calculated_amount?: number } | null
  calculated_amount?: number
}

/** Product with optional computed minimum price (legacy sort utility). */
export interface MinPricedProduct extends Product {
  _minPrice?: number
  created_at?: string
}

export interface Product {
  id: string | null
  name: string
  slug: string | null
  handle: string | null
  title: string | null
  description: string
  price: number
  available_item_count: number
  category: Category
  thumbnail: string | null
  images: ProductImage[]
  variants: ProductVariant[]
  options: BackendProductOption[]
  shop?: {
    shop_id?: string
    shop_name?: string
  }
  // Legacy Medusa compatibility
  created_at?: string
  updated_at?: string
  tags?: Record<string, unknown>[]
  collection?: { title?: string; id?: string } | null
  collection_id?: string
  type?: { value?: string } | null
  width?: number
  height?: number
  weight?: number
  length?: number
  material?: string
  origin_country?: string
  subtitle?: string
}

export interface ProductCreate {
  name: string
  description: string
  price: number
  available_item_count: number
  category: Category
}

// ── Cart ─────────────────────────────────────────────────────────────

export interface CartItemCreate {
  product_name: string
  quantity: number
}

export interface CartItem {
  id: string
  quantity: number
  price: number
  unit_price: number | null
  total: number | null
  product: Product
  product_title: string
  product_handle: string
  thumbnail: string | null
  variant: ProductVariant | null | undefined
  created_at: string | null
  // Legacy Medusa compat
  title?: string
  description?: string
  subtitle?: string
}

export interface ShoppingCart {
  id: string | null
  email: string | null
  items: CartItem[]
  total_quantity: number
  subtotal: number
  total: number | null
  currency_code: string
  region: any
  shipping_address: any
  billing_address: any
  shipping_methods: any[]
  payment_collection: any
  promotions: Record<string, unknown>[]
  // Legacy Medusa compat
  item_total?: number
  gift_cards?: unknown[]
}

// ── Order ────────────────────────────────────────────────────────────

export interface Payment {
  status: PaymentStatus
  amount: number | null
  currency: string | null
}

export interface Shipment {
  status: ShipmentStatus
  shipment_date: string | null
  estimated_arrival: string | null
  shipment_method: string | null
}

export interface OrderCreate {
  order_number?: string | null
  items?: CartItemCreate[]
  payment?: {
    amount: number
    currency: string
  } | null
}

export interface Order {
  id: string | null
  order_number: string
  status: OrderStatus
  order_date: string | null
  email: string | null
  items: CartItem[]
  payment: Payment | null
  shipments: Shipment[]
  shipping_address: Record<string, unknown> | null
  billing_address: Record<string, unknown> | null
  shipping_method: Record<string, unknown> | null
  subtotal: number | null
  total: number | null
  currency_code: string
  // Legacy compat
  display_id?: string
  created_at?: string
}

// ── Shop / Hall ──────────────────────────────────────────────────────

export interface ShopSummary {
  id: string
  name: string
  slug: string
  product_count: number
  categories: string[]
}

export interface HallSection {
  title: string
  slug: string
  shop: ShopSummary
  products: Product[]
}

export interface HallPayload {
  route: "/hall"
  shops: ShopSummary[]
  categories: Array<{ name: string; slug: string }>
  sections: HallSection[]
  product_count: number
  shop_count: number
  category_count: number
}

export interface PaginatedHallProducts {
  products: Product[]
  count: number
  limit: number
  offset: number
  has_more: boolean
}

// ── Region ───────────────────────────────────────────────────────────

export interface RegionCountry {
  country_code: string
  display_name: string
  iso_2?: string
  iso_3?: string
}

export interface Region {
  region_id: string
  id?: string
  name: string
  currency_code: string
  countries: RegionCountry[]
}

// ── Address management ───────────────────────────────────────────────

export interface AddressCreate {
  street: string
  city: string
  state?: string
  postal_code?: string
  country?: string
  is_default_shipping?: boolean
}

// ── Utility types ────────────────────────────────────────────────────

/** Unwraps a value object `{ value: T }` back to `T`, or returns the value as-is. */
export type Unwrapped<T> = T extends { value: infer V } ? V : T

export function unwrapValue<T>(value: T): Unwrapped<T> {
  if (value !== null && typeof value === "object" && "value" in (value as any)) {
    return (value as any).value as Unwrapped<T>
  }
  return value as Unwrapped<T>
}

// ── Backward-compatible aliases (for gradual migration) ─────────────
// Old code imports these; new code should use the primary names above.

export type BackendRecord = Record<string, any>
export type BackendAccountStatus = AccountStatus
export type BackendOrderStatus = OrderStatus
export type BackendPaymentStatus = PaymentStatus
export type BackendShipmentStatus = ShipmentStatus
export type BackendName = Name
export type BackendPhone = Phone
export type BackendAddress = Address & Record<string, unknown>
export type BackendProductCategory = Category
export type BackendProductVariant = ProductVariant
export type BackendProductImage = ProductImage
export type BackendProductOption = Record<string, any> & {
  id?: string
  title?: string
  name?: string
  values?: Array<{ value?: string; label?: string; title?: string; name?: string }>
}
export type BackendProductListParams = Record<string, any>
export type BackendProduct = Product & { options?: any[] }
export type BackendShopSummary = ShopSummary
export type BackendHallSection = HallSection
export type BackendHallPayload = HallPayload
export type BackendItem = CartItem
export type BackendCartLineItem = CartItem
export type BackendOrderLineItem = CartItem
export type BackendPromotion = Record<string, unknown>
export type BackendPaymentSession = Record<string, any>
export type BackendPrice = Record<string, any> & { price_rules?: Record<string, any>[]; value?: any }
export type BackendFreeShippingPrice = BackendPrice & {
  target_reached: boolean
  target_remaining: number
  remaining_percentage: number
}
export type BackendShippingOption = Record<string, any> & {
  id?: string
  name?: string
  amount?: number
  price_type?: string
  prices?: Array<{ amount?: number; currency_code?: string }>
  rules?: Record<string, any>[]
  service_zone?: { fulfillment_set?: { type?: string; location?: { address?: Record<string, any> } } }
  insufficient_inventory?: boolean
}
export type BackendCollection = Record<string, any> & { products?: Product[] }
export type BackendShoppingCart = ShoppingCart & {
  discount_total?: number
  gift_card_total?: number
  gift_card_tax_total?: number
  item_tax_total?: number
  shipping_tax_total?: number
  shipping_total?: number
  tax_total?: number
  original_total?: number
  original_item_subtotal?: number
  original_item_total?: number
  original_tax_total?: number
  original_shipping_total?: number
  item_total?: number
}
export type BackendCart = BackendShoppingCart
export type BackendPayment = Payment
export type BackendShipmentLog = { status: ShipmentStatus; creation_date: { value: string } }
export type BackendShipment = {
  shipment_date: { value: string }
  estimated_arrival: { value: string }
  shipment_method: { value: string }
  shipment_logs?: BackendShipmentLog[]
}
export type BackendOrderLog = { creation_date: string; status: OrderStatus }
export type BackendOrder = Order & {
  order_logs?: BackendOrderLog[]
  shipments?: BackendShipment[]
  currency_code?: string
  shipping_methods?: Record<string, unknown>[]
}
export type BackendAccount = Account
export type BackendCustomer = Account
export type BackendNotification = {
  notification_id: { value: number }
  created_on: { value: string }
  content: { value: string }
}
export type BackendProductFormPayload = ProductCreate
export type BackendAddressPayload = Address
export type BackendLoginPayload = LoginPayload
export type BackendRegisterAccountPayload = LoginPayload & {
  name: Name
  shipping_address: Address
  email: string
  phone: Phone
}
export type BackendOrderPayload = {
  order_number?: string
  items?: Array<{ product_name: string; quantity: number }>
  payment?: Payment
}
export type BackendRegion = Region
export type BackendProductReview = { rating: number; review: string; product: Product }

// Value object helpers (legacy)
export type BackendValue<T> = T | { value: T }
export type ValueObject<T> = { value: T }
