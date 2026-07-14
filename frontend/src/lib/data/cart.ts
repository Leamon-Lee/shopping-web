"use server"

import {
  addCartItem,
  createCartPaymentSession,
  deleteCartItem,
  getCart,
  getCartShippingOptions,
  placeOrder as placeBackendOrder,
  setCartAddresses as setBackendAddresses,
  setCartShippingMethod as setBackendShippingMethod,
  updateCartItem,
} from "../../api/backend"

type CartMutationInput = {
  productName?: string
  lineId?: string
  quantity?: number
}

export async function retrieveCart(): Promise<any | null> {
  return getCart().catch(() => null)
}

export async function getOrSetCart(..._args: any[]): Promise<any> {
  return getCart()
}

export async function updateCart(..._args: any[]) {
  return getCart()
}

export async function addToCart({
  productName,
  variantId,
  quantity,
}: {
  productName?: string
  variantId?: string
  quantity: number
  countryCode?: string
}) {
  const backendProductName = productName || variantId
  if (!backendProductName) {
    return null
  }

  return addCartItem({ product_name: backendProductName, quantity })
}

export async function updateLineItem({
  productName,
  lineId,
  quantity,
}: CartMutationInput) {
  const backendProductName = productName || lineId
  if (!backendProductName || typeof quantity !== "number") {
    return null
  }

  return updateCartItem(backendProductName, quantity)
}

export async function deleteLineItem(productNameOrLineId: string) {
  return deleteCartItem(productNameOrLineId)
}

// ── Checkout operations ─────────────────────────────────────────────

export async function setAddresses(
  _prevState: unknown,
  formData: FormData
): Promise<string | null> {
  const payload: Record<string, unknown> = {}
  formData.forEach((value, key) => {
    payload[key] = value
  })

  try {
    await setBackendAddresses(payload)
    return null
  } catch (e: unknown) {
    return e instanceof Error ? e.message : "Failed to save address."
  }
}

export async function setShippingMethod({
  cartId,
  shippingMethodId,
}: {
  cartId: string
  shippingMethodId: string
}) {
  try {
    return await setBackendShippingMethod(shippingMethodId)
  } catch (e: unknown) {
    throw e instanceof Error ? e : new Error("Failed to set shipping method.")
  }
}

export async function initiatePaymentSession(
  cart: any,
  data: { provider_id: string }
) {
  try {
    return await createCartPaymentSession(data.provider_id)
  } catch (e: unknown) {
    throw e instanceof Error ? e : new Error("Failed to create payment session.")
  }
}

export async function listCartOptions() {
  try {
    const options = await getCartShippingOptions()
    return { shipping_options: options }
  } catch {
    return { shipping_options: [] }
  }
}

export async function placeOrder(): Promise<{ type: string; order: any }> {
  const order = await placeBackendOrder()
  return { type: "order", order }
}

// ── Stubs for legacy compatibility ──────────────────────────────────

export async function applyPromotions(..._args: any[]) {
  return getCart().catch(() => null)
}
export async function applyGiftCard(..._args: any[]) {
  return getCart().catch(() => null)
}
export async function removeDiscount(..._args: any[]) {
  return getCart().catch(() => null)
}
export async function removeGiftCard(..._args: any[]) {
  return getCart().catch(() => null)
}
export async function submitPromotionForm(..._args: any[]) {
  return null
}
export async function updateRegion(..._args: any[]) {
  return getCart().catch(() => null)
}
