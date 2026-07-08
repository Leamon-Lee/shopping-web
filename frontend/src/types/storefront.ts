import type {
  BackendAccountStatus,
  BackendOrderStatus,
  BackendPaymentStatus,
  BackendShipmentStatus,
} from "./backend"

export type FrontendCategory = {
  name: string
  description: string
}

export type FrontendProduct = {
  id: string
  name: string
  title: string
  description: string
  price: number
  displayPrice: string
  availableItemCount: number
  category: FrontendCategory
}

export type FrontendCartItem = {
  id: string
  quantity: number
  unitPrice: number
  lineTotal: number
  product: FrontendProduct
}

export type FrontendCart = {
  items: FrontendCartItem[]
  subtotal: number
  displaySubtotal: string
}

export type FrontendAddress = {
  street: string
  city: string
  state: string
  postalCode: string
  country: string
}

export type FrontendUser = {
  userName: string
  status: BackendAccountStatus
  firstName: string
  lastName: string
  email: string
  phone: string
  shippingAddress: FrontendAddress
}

export type FrontendPayment = {
  status: BackendPaymentStatus
  amount: number | null
  currency: string | null
}

export type FrontendShipmentEvent = {
  status: BackendShipmentStatus
  creationDate: string
}

export type FrontendShipment = {
  shipmentDate: string
  estimatedArrival: string
  shipmentMethod: string
  shipmentLogs: FrontendShipmentEvent[]
}

export type FrontendOrderStatusEvent = {
  status: BackendOrderStatus
  creationDate: string
}

export type FrontendOrder = {
  orderNumber: string
  status: BackendOrderStatus
  orderDate: string | null
  items: FrontendCartItem[]
  orderLogs: FrontendOrderStatusEvent[]
  shipments: FrontendShipment[]
  payment: FrontendPayment | null
}

export type ProductFormValues = {
  name: string
  description: string
  price: number
  availableItemCount: number
  categoryName: string
  categoryDescription: string
}

export type AddressFormValues = FrontendAddress

export type LoginFormValues = {
  userName: string
  password: string
}

export type RegisterFormValues = LoginFormValues & {
  firstName: string
  lastName: string
  email: string
  countryCode: string
  phoneNumber: string
  shippingAddress: FrontendAddress
}

export type OrderFormValues = {
  items: FrontendCartItem[]
  shippingAddress: FrontendAddress
  payment?: FrontendPayment
}
