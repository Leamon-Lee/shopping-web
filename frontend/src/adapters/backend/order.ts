import type {
  BackendOrder,
  BackendOrderLog,
  BackendOrderPayload,
  BackendPayment,
  BackendShipment,
  BackendShipmentLog,
} from "../../types/backend"
import type {
  FrontendOrder,
  FrontendOrderStatusEvent,
  FrontendPayment,
  FrontendShipment,
  FrontendShipmentEvent,
  OrderFormValues,
} from "../../types/storefront"
import { mapBackendItemToFrontendCartItem } from "./cart"
import { mapFrontendAddressFormToBackendAddressPayload } from "./address"
import { unwrapBackendValue } from "./shared"

export function mapBackendPaymentToFrontendPayment(
  payment: BackendPayment
): FrontendPayment {
  return {
    status: payment.status,
    amount:
      payment.amount === null || payment.amount === undefined
        ? null
        : unwrapBackendValue(payment.amount),
    currency: payment.currency ?? null,
  }
}

export function mapBackendShipmentLogToFrontendShipmentEvent(
  log: BackendShipmentLog
): FrontendShipmentEvent {
  return {
    status: log.status,
    creationDate: unwrapBackendValue(log.creation_date),
  }
}

export function mapBackendShipmentToFrontendShipment(
  shipment: BackendShipment
): FrontendShipment {
  return {
    shipmentDate: unwrapBackendValue(shipment.shipment_date),
    estimatedArrival: unwrapBackendValue(shipment.estimated_arrival),
    shipmentMethod: unwrapBackendValue(shipment.shipment_method),
    shipmentLogs: (shipment.shipment_logs ?? []).map(
      mapBackendShipmentLogToFrontendShipmentEvent
    ),
  }
}

export function mapBackendOrderLogToFrontendStatusEvent(
  log: BackendOrderLog
): FrontendOrderStatusEvent {
  return {
    status: log.status,
    creationDate: unwrapBackendValue(log.creation_date),
  }
}

export function mapBackendOrderToFrontendOrder(
  order: BackendOrder
): FrontendOrder {
  return {
    orderNumber: unwrapBackendValue(order.order_number),
    status: order.status,
    orderDate: order.order_date ? unwrapBackendValue(order.order_date) : null,
    items: order.items.map(mapBackendItemToFrontendCartItem),
    orderLogs: (order.order_logs ?? []).map(
      mapBackendOrderLogToFrontendStatusEvent
    ),
    shipments: (order.shipments ?? []).map(mapBackendShipmentToFrontendShipment),
    payment: order.payment ? mapBackendPaymentToFrontendPayment(order.payment) : null,
  }
}

export function mapFrontendOrderFormToCreateOrderPayload(
  form: OrderFormValues
): BackendOrderPayload {
  return {
    items: form.items.map((item) => ({
      product_name: item.product.name,
      quantity: item.quantity,
      price: item.unitPrice,
    })),
    shipping_address: mapFrontendAddressFormToBackendAddressPayload(
      form.shippingAddress
    ),
    payment: form.payment
      ? {
          status: form.payment.status,
          amount: form.payment.amount,
          currency: form.payment.currency,
        }
      : undefined,
  }
}
