import { Metadata } from "next"
import { redirect } from "next/navigation"
import { cookies } from "next/headers"

import { deleteCartItem, getCart } from "../../../api/backend"
import EmptyCartMessage from "@modules/cart/components/empty-cart-message"
import CartItemSelector from "@modules/cart/components/cart-item-selector"

export const dynamic = "force-dynamic"

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
    redirect("/checkout")
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
