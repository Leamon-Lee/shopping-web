import { Metadata } from "next"

import { deleteCartItem, getCart, placeOrder } from "../../../api/backend"
import {
  backendLineTotal,
  backendProductName,
  formatBackendMoney,
  unwrapBackendValue,
} from "../../../lib/backend-native"
import EmptyCartMessage from "@modules/cart/components/empty-cart-message"
import { Button } from "@medusajs/ui"

export const metadata: Metadata = {
  title: "Cart",
  description: "View your cart",
}

export default async function Cart() {
  const cart = await getCart()
  const items = cart.items
  const subtotal =
    cart.subtotal ?? items.reduce((sum, item) => sum + backendLineTotal(item), 0)

  async function removeItem(formData: FormData) {
    "use server"
    const productName = String(formData.get("product_name") || "")
    if (productName) {
      await deleteCartItem(productName)
    }
  }

  async function submitOrder() {
    "use server"
    await placeOrder()
  }

  return (
    <div className="py-12">
      <div className="content-container" data-testid="cart-container">
        {items.length ? (
          <div className="grid grid-cols-1 small:grid-cols-[1fr_360px] gap-x-40">
            <div className="flex flex-col bg-white py-6 gap-y-6">
              <div>
                <div className="pb-3 flex items-center">
                  <h1 className="text-[2rem] leading-[2.75rem]">Cart</h1>
                </div>
                <ul className="border-t border-ui-border-base">
                  {items.map((item) => {
                    const productName = backendProductName(item.product)
                    return (
                      <li
                        className="flex items-center justify-between border-b border-ui-border-base py-4"
                        key={productName}
                      >
                        <div>
                          <p className="text-base-regular text-ui-fg-base">
                            {productName}
                          </p>
                          <p className="text-small-regular text-ui-fg-muted">
                            Qty {unwrapBackendValue(item.quantity)}
                          </p>
                        </div>
                        <div className="flex items-center gap-4">
                          <p className="text-base-regular text-ui-fg-subtle">
                            {formatBackendMoney(backendLineTotal(item))}
                          </p>
                          <form action={removeItem}>
                            <input type="hidden" name="product_name" value={productName} />
                            <button className="text-small-regular text-ui-fg-muted hover:text-ui-fg-base">
                              Remove
                            </button>
                          </form>
                        </div>
                      </li>
                    )
                  })}
                </ul>
              </div>
            </div>
            <div className="relative">
              <div className="flex flex-col gap-y-4 sticky top-12 bg-white py-6">
                <h2 className="text-[2rem] leading-[2.75rem]">Summary</h2>
                <div className="flex items-center justify-between text-base-regular">
                  <span>Subtotal</span>
                  <span>{formatBackendMoney(subtotal)}</span>
                </div>
                <form action={submitOrder}>
                  <Button type="submit" className="w-full h-10">
                    Complete order
                  </Button>
                </form>
              </div>
            </div>
          </div>
        ) : (
          <EmptyCartMessage />
        )}
      </div>
    </div>
  )
}
