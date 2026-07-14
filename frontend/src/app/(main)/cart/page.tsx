import { Metadata } from "next"
import { cookies } from "next/headers"

import { deleteCartItem, getCart } from "../../../api/backend"
import EmptyCartMessage from "@modules/cart/components/empty-cart-message"
import CartItemSelector from "@modules/cart/components/cart-item-selector"

export const dynamic = "force-dynamic"

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8001"
const TOKEN_COOKIE = "shopping_token"

export const metadata: Metadata = {
  title: "Cart",
  description: "View your cart",
}

export default async function Cart() {
  const cart = await getCart()
  const items = cart.items

  async function removeItem(formData: FormData) {
    "use server"
    const productName = String(formData.get("product_name") || "")
    if (productName) await deleteCartItem(productName)
  }

  async function checkoutAction(formData: FormData) {
    "use server"
    const selected = String(formData.get("selected_items") || "")
    const store = await cookies()
    store.set("checkout_items", selected, { path: "/", maxAge: 300 })

    const token = store.get(TOKEN_COOKIE)?.value
    const selectedNames = selected.split("|").filter(Boolean).map((name) => name.toLowerCase())
    const latestCart = await getCart().catch(() => null)
    const selectedItems = (latestCart?.items || []).filter((item: any) =>
      selectedNames.includes((item.product_title || item.product?.name || "").toLowerCase())
    )
    const subtotal = selectedItems.reduce(
      (sum: number, item: any) => sum + (item.unit_price || item.price || 0) * (item.quantity || 1),
      0
    )
    if (selectedItems.length) {
      await fetch(`${BACKEND_URL}/events`, {
        method: "POST",
        headers: {
          "content-type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        cache: "no-store",
        body: JSON.stringify({
          event_type: "checkout_start",
          quantity: selectedItems.reduce((sum: number, item: any) => sum + (item.quantity || 1), 0),
          price: subtotal,
          source_page: "/cart",
          metadata: {
            item_count: selectedItems.length,
            product_names: selectedItems.map((item: any) => item.product_title || item.product?.name).filter(Boolean),
          },
        }),
      }).catch(() => null)
    }
  }

  return (
    <div className="py-12">
      <div className="content-container" data-testid="cart-container">
        {items.length ? (
          <CartItemSelector items={items} removeAction={removeItem} checkoutAction={checkoutAction} />
        ) : (
          <EmptyCartMessage />
        )}
      </div>
    </div>
  )
}
