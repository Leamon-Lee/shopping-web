export type ValueObject<T> = {
  value: T
}

export type BackendValue<T> = T | ValueObject<T>

export type BackendAccountStatus =
  | "active"
  | "blocked"
  | "banned"
  | "compromised"
  | "archived"
  | "unknown"

export type BackendOrderStatus =
  | "unshipped"
  | "pending"
  | "shipped"
  | "complete"
  | "canceled"
  | "refund_applied"

export type BackendPaymentStatus =
  | "unpaid"
  | "pending"
  | "completed"
  | "failed"
  | "declined"
  | "canceled"
  | "abandoned"
  | "settling"
  | "settled"
  | "refunded"

export type BackendShipmentStatus =
  | "pending"
  | "shipped"
  | "delivered"
  | "on_hold"

export type BackendName = {
  first_name: string
  last_name: string
}

export type BackendPhone = {
  country_code: string
  number: string
}

export type BackendAddress = {
  street: string
  city: string
  state: string
  postal_code: string
  country: string
}

export type BackendProductCategory = {
  name: BackendValue<string>
  description: BackendValue<string>
}

export type BackendProduct = {
  name: BackendValue<string>
  description: BackendValue<string>
  price: BackendValue<number>
  available_item_count: BackendValue<number>
  category: BackendProductCategory
}

export type BackendProductReview = {
  rating: BackendValue<number>
  review: BackendValue<string>
  product: BackendProduct
}

export type BackendItem = {
  quantity: BackendValue<number>
  price: BackendValue<number>
  product: BackendProduct
}

export type BackendShoppingCart = {
  items: BackendItem[]
}

export type BackendPayment = {
  status: BackendPaymentStatus
  amount?: BackendValue<number> | null
  currency?: string | null
}

export type BackendShipmentLog = {
  status: BackendShipmentStatus
  creation_date: BackendValue<string>
}

export type BackendShipment = {
  shipment_date: BackendValue<string>
  estimated_arrival: BackendValue<string>
  shipment_method: BackendValue<string>
  shipment_logs?: BackendShipmentLog[]
}

export type BackendOrderLog = {
  creation_date: BackendValue<string>
  status: BackendOrderStatus
}

export type BackendOrder = {
  order_number: BackendValue<string>
  status: BackendOrderStatus
  order_date?: BackendValue<string> | null
  items: BackendItem[]
  order_logs?: BackendOrderLog[]
  shipments?: BackendShipment[]
  payment?: BackendPayment | null
}

export type BackendAccount = {
  user_name: BackendValue<string>
  status: BackendAccountStatus
  name: BackendName
  shipping_address: BackendAddress
  email: BackendValue<string>
  phone: BackendPhone
}

export type BackendNotification = {
  notification_id: BackendValue<number>
  created_on: BackendValue<string>
  content: BackendValue<string>
}

export type BackendProductFormPayload = {
  name: string
  description: string
  price: number
  available_item_count: number
  category: {
    name: string
    description: string
  }
}

export type BackendAddressPayload = BackendAddress

export type BackendLoginPayload = {
  user_name: string
  password: string
}

export type BackendRegisterAccountPayload = BackendLoginPayload & {
  name: BackendName
  shipping_address: BackendAddress
  email: string
  phone: BackendPhone
}

export type BackendOrderPayload = {
  items: Array<{
    product_name: string
    quantity: number
    price: number
  }>
  shipping_address: BackendAddress
  payment?: BackendPayment
}
