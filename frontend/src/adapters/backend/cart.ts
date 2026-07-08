import type { BackendItem, BackendShoppingCart } from "../../types/backend"
import type { FrontendCart, FrontendCartItem } from "../../types/storefront"
import { mapBackendProductToFrontendProduct } from "./product"
import { formatMoney, slugify, unwrapBackendValue } from "./shared"

export function mapBackendItemToFrontendCartItem(
  item: BackendItem
): FrontendCartItem {
  const product = mapBackendProductToFrontendProduct(item.product)
  const quantity = unwrapBackendValue(item.quantity)
  const unitPrice = unwrapBackendValue(item.price)

  return {
    id: `${product.id}-${quantity}`,
    quantity,
    unitPrice,
    lineTotal: quantity * unitPrice,
    product,
  }
}

export function mapBackendCartToFrontendCart(
  cart: BackendShoppingCart
): FrontendCart {
  const items = cart.items.map(mapBackendItemToFrontendCartItem)
  const subtotal = items.reduce((sum, item) => sum + item.lineTotal, 0)

  return {
    items,
    subtotal,
    displaySubtotal: formatMoney(subtotal),
  }
}

export function mapFrontendAddToCartToBackendPayload(input: {
  product: { name: string; price: number }
  quantity: number
}) {
  return {
    product_name: input.product.name,
    quantity: input.quantity,
    price: input.product.price,
  }
}

export function mapFrontendQuantityUpdateToBackendPayload(input: {
  itemId: string
  quantity: number
}) {
  return {
    item_id: slugify(input.itemId),
    quantity: input.quantity,
  }
}
