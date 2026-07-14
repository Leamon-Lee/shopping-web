import { deleteCartItem } from "api/backend"
import {
  backendLineTotal,
  backendProductName,
  formatBackendMoney,
  unwrapBackendValue,
} from "@lib/backend-native"
import EmptyCartMessage from "@modules/cart/components/empty-cart-message"
import LocalizedClientLink from "@modules/common/components/localized-client-link"
import RecommendedProducts from "@modules/products/components/recommended-products"
import { Button } from "@medusajs/ui"
import type { ShoppingCart } from "types/backend"

export default function BackendCartPage({
  cart,
  ownerUsername,
}: {
  cart: ShoppingCart | null
  ownerUsername?: string
}) {
  const items = cart?.items ?? []
  const subtotal =
    cart?.subtotal ?? items.reduce((sum, item) => sum + backendLineTotal(item), 0)

  return (
    <div className="py-12">
      <div className="content-container" data-testid="cart-container">
        {items.length ? (
          <div className="grid grid-cols-1 small:grid-cols-[minmax(0,1fr)_320px] gap-12">
            <div className="flex min-w-0 flex-col bg-white py-6 gap-y-6">
              <div>
                <div className="pb-3 flex items-center">
                  <h1 className="text-[2rem] leading-[2.75rem]">Cart</h1>
                </div>
                <ul className="border-t border-ui-border-base">
                  {items.map((item) => {
                    const productName = backendProductName(item.product)
                    return (
                      <li
                        className="flex flex-col gap-3 border-b border-ui-border-base py-4 small:flex-row small:items-center small:justify-between"
                        key={productName}
                      >
                        <div className="min-w-0">
                          <p className="text-base-regular text-ui-fg-base">
                            {productName}
                          </p>
                          <p className="text-small-regular text-ui-fg-muted">
                            Qty {unwrapBackendValue(item.quantity)}
                          </p>
                        </div>
                        <div className="flex shrink-0 items-center gap-4 small:justify-end">
                          <p className="text-base-regular text-ui-fg-subtle">
                            {formatBackendMoney(backendLineTotal(item))}
                          </p>
                          <form action={removeItem}>
                            <input type="hidden" name="product_name" value={productName} />
                            {ownerUsername ? (
                              <input type="hidden" name="owner_username" value={ownerUsername} />
                            ) : null}
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
            <div className="relative min-w-0">
              <div className="flex flex-col gap-y-4 sticky top-20 bg-white py-6">
                <h2 className="text-[2rem] leading-[2.75rem]">Summary</h2>
                <div className="flex items-center justify-between text-base-regular">
                  <span>Subtotal</span>
                  <span>{formatBackendMoney(subtotal)}</span>
                </div>
                <LocalizedClientLink href="/checkout">
                  <Button className="w-full min-w-0 h-10">
                    Proceed to checkout
                  </Button>
                </LocalizedClientLink>
              </div>
            </div>
          </div>
        ) : (
          <EmptyCartMessage />
        )}
      </div>
      <div className="mt-12">
        <RecommendedProducts endpoint="/recommendations/cart" title="You May Also Like" cartId={cart?.id} />
      </div>
    </div>
  )
}

async function removeItem(formData: FormData) {
  "use server"
  const productName = String(formData.get("product_name") || "")
  const owner = String(formData.get("owner_username") || "")
  if (productName) {
    await deleteCartItem(productName, owner || undefined)
  }
}
