import { backendCartFixture } from "../../../../api/backend-fixtures"
import { mapBackendCartToFrontendCart } from "../../../../adapters/backend/cart"
import EmptyCartMessage from "@modules/cart/components/empty-cart-message"
import { Metadata } from "next"

export const metadata: Metadata = {
  title: "Cart",
  description: "View your cart",
}

export default async function Cart() {
  const cart = mapBackendCartToFrontendCart(backendCartFixture)

  return (
    <div className="py-12">
      <div className="content-container" data-testid="cart-container">
        {cart.items.length ? (
          <div className="grid grid-cols-1 small:grid-cols-[1fr_360px] gap-x-40">
            <div className="flex flex-col bg-white py-6 gap-y-6">
              <div>
                <div className="pb-3 flex items-center">
                  <h1 className="text-[2rem] leading-[2.75rem]">Cart</h1>
                </div>
                <ul className="border-t border-ui-border-base">
                  {cart.items.map((item) => (
                    <li
                      className="flex items-center justify-between border-b border-ui-border-base py-4"
                      key={item.id}
                    >
                      <div>
                        <p className="text-base-regular text-ui-fg-base">
                          {item.product.name}
                        </p>
                        <p className="text-small-regular text-ui-fg-muted">
                          Qty {item.quantity}
                        </p>
                      </div>
                      <p className="text-base-regular text-ui-fg-subtle">
                        ${item.lineTotal.toFixed(2)}
                      </p>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
            <div className="relative">
              <div className="flex flex-col gap-y-4 sticky top-12 bg-white py-6">
                <h2 className="text-[2rem] leading-[2.75rem]">Summary</h2>
                <div className="flex items-center justify-between text-base-regular">
                  <span>Subtotal</span>
                  <span>{cart.displaySubtotal}</span>
                </div>
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
