"use client"

import { Badge, Button } from "@medusajs/ui"
import Input from "@modules/common/components/input"
import { useMemo, useState } from "react"
import type { Order, Product, ShoppingCart } from "types/backend"
import RecommendedProducts from "@modules/products/components/recommended-products"

type CustomerPanelProps = {
  username?: string
  cart: ShoppingCart | null
  orders: Order[]
  products: Product[]
}

type View = "home" | "orders" | "cart" | "wishlist" | "profile"

const money = (value?: number | null) => `CN¥${(value ?? 0).toFixed(2)}`

const itemTitle = (item: any) =>
  item.product_title || item.product?.title || item.product?.name || "Product"

const itemImage = (item: any) =>
  item.thumbnail ||
  item.product?.thumbnail ||
  item.product?.images?.[0]?.url ||
  item.product?.images?.[0]?.image_url ||
  "/images/placeholder.png"

const productImage = (product: any) =>
  product.thumbnail ||
  product.images?.[0]?.url ||
  product.images?.[0]?.image_url ||
  "/images/placeholder.png"

const orderTotal = (order: any) =>
  order.payment?.amount ?? order.total ?? order.subtotal ?? 0

const orderStatus = (order: any) =>
  order.shipments?.[0]?.status || order.fulfillment_status || order.status || "processing"

const statusColor = (status: string) => {
  const value = status.toLowerCase()
  if (["complete", "completed", "delivered", "shipped", "paid"].includes(value)) return "green"
  if (["canceled", "failed", "refunded"].includes(value)) return "red"
  if (["pending", "processing"].includes(value)) return "purple"
  return "orange"
}

const StatButton = ({
  label,
  value,
  onClick,
}: {
  label: string
  value: string
  onClick: () => void
}) => (
  <button
    className="flex h-20 flex-col items-center justify-center border border-ui-border-base bg-white text-center hover:bg-ui-bg-subtle"
    onClick={onClick}
    type="button"
  >
    <span className="text-xl-semi text-ui-fg-base">{value}</span>
    <span className="mt-1 text-small-regular text-ui-fg-subtle">{label}</span>
  </button>
)

const SectionTitle = ({
  title,
  action,
}: {
  title: string
  action?: React.ReactNode
}) => (
  <div className="flex items-center justify-between border-b border-ui-border-base pb-3">
    <h2 className="text-base-semi text-ui-fg-base">{title}</h2>
    {action}
  </div>
)

const CartPreview = ({ cart }: { cart: ShoppingCart | null }) => {
  const items = cart?.items ?? []

  return (
    <section className="flex flex-col gap-4">
      <SectionTitle
        title="Shopping Cart"
        action={
          <a className="text-small-regular text-ui-fg-interactive" href="/shop">
            Shop more
          </a>
        }
      />
      {items.length ? (
        <div className="grid grid-cols-1 gap-3 medium:grid-cols-2">
          {items.slice(0, 4).map((item: any) => (
            <a
              className="grid grid-cols-[72px_1fr] gap-3 border border-ui-border-base bg-white p-3 hover:bg-ui-bg-subtle"
              href={`/shop/${item.product_handle || item.product?.handle || ""}`}
              key={item.id}
            >
              <img
                alt={itemTitle(item)}
                className="h-[72px] w-[72px] object-cover"
                src={itemImage(item)}
              />
              <div className="min-w-0">
                <p className="truncate text-small-semi text-ui-fg-base">{itemTitle(item)}</p>
                <p className="mt-1 text-small-regular text-ui-fg-subtle">
                  Qty {item.quantity}
                </p>
                <p className="mt-2 text-small-semi text-ui-fg-base">
                  {money(item.total ?? item.unit_price ?? item.price)}
                </p>
              </div>
            </a>
          ))}
        </div>
      ) : (
        <div className="border border-ui-border-base bg-white p-8 text-center text-small-regular text-ui-fg-subtle">
          Your cart is empty.
        </div>
      )}
      <div className="flex items-center justify-between border border-ui-border-base bg-white p-4">
        <span className="text-small-regular text-ui-fg-subtle">
          {cart?.total_quantity ?? 0} items
        </span>
        <span className="text-base-semi text-ui-fg-base">{money(cart?.subtotal)}</span>
      </div>
    </section>
  )
}

const OrdersView = ({ orders, query }: { orders: Order[]; query: string }) => {
  const filteredOrders = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return orders
    return orders.filter((order: any) =>
      [order.order_number, order.status, order.email]
        .filter(Boolean)
        .some((value) => String(value).toLowerCase().includes(q))
    )
  }, [orders, query])

  return (
    <section className="flex flex-col gap-4">
      <SectionTitle title="Orders" />
      <div className="flex flex-wrap gap-2">
        {["All", "To Pay", "To Ship", "To Receive", "To Review", "Refunds"].map((label) => (
          <button
            className="h-9 border border-ui-border-base bg-white px-3 text-small-regular text-ui-fg-subtle hover:bg-ui-bg-subtle hover:text-ui-fg-base"
            key={label}
            type="button"
          >
            {label}
          </button>
        ))}
      </div>
      {filteredOrders.length ? (
        <div className="flex flex-col gap-3">
          {filteredOrders.map((order: any) => (
            <a
              className="border border-ui-border-base bg-white p-4 hover:bg-ui-bg-subtle"
              href={`/account/orders/details/${order.order_number}`}
              key={order.id || order.order_number}
            >
              <div className="flex flex-col justify-between gap-3 small:flex-row small:items-center">
                <div>
                  <p className="text-small-semi text-ui-fg-base">
                    {order.order_number || "Order"}
                  </p>
                  <p className="mt-1 text-small-regular text-ui-fg-subtle">
                    {(order.order_date || order.created_at || "").slice(0, 10) || "Recent order"}
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  <Badge color={statusColor(orderStatus(order))}>{orderStatus(order)}</Badge>
                  <span className="text-small-semi text-ui-fg-base">{money(orderTotal(order))}</span>
                </div>
              </div>
            </a>
          ))}
        </div>
      ) : (
        <div className="border border-ui-border-base bg-white p-8 text-center text-small-regular text-ui-fg-subtle">
          No orders yet.
        </div>
      )}
    </section>
  )
}

const ProductGrid = ({ products }: { products: Product[] }) => (
  <section className="flex flex-col gap-4">
    <SectionTitle title="Recommended For You" />
    <div className="grid grid-cols-2 gap-3 medium:grid-cols-4">
      {products.slice(0, 8).map((product: any) => (
        <a
          className="border border-ui-border-base bg-white hover:bg-ui-bg-subtle"
          href={`/shop/${product.handle || product.slug || product.name}`}
          key={product.id || product.name}
        >
          <img
            alt={product.title || product.name}
            className="aspect-square w-full object-cover"
            src={productImage(product)}
          />
          <div className="p-3">
            <p className="line-clamp-2 min-h-[40px] text-small-regular text-ui-fg-base">
              {product.title || product.name}
            </p>
            <p className="mt-2 text-small-semi text-ui-fg-base">{money(product.price)}</p>
          </div>
        </a>
      ))}
    </div>
  </section>
)

const PlaceholderView = ({ title }: { title: string }) => (
  <section className="border border-ui-border-base bg-white p-8">
    <h2 className="text-base-semi text-ui-fg-base">{title}</h2>
    <div className="mt-6 grid grid-cols-1 gap-3 small:grid-cols-3">
      {["Personal info", "Shipping addresses", "Account security"].map((label) => (
        <button
          className="h-16 border border-ui-border-base bg-ui-bg-base text-small-regular text-ui-fg-subtle hover:bg-ui-bg-subtle"
          key={label}
          type="button"
        >
          {label}
        </button>
      ))}
    </div>
  </section>
)

const CustomerPanel = ({ username, cart, orders, products }: CustomerPanelProps) => {
  const [activeView, setActiveView] = useState<View>("home")
  const [query, setQuery] = useState("")

  const pendingPayment = orders.filter((order: any) =>
    ["pending", "requires_payment"].includes(String(order.payment?.status || order.status).toLowerCase())
  ).length
  const toReceive = orders.filter((order: any) =>
    ["shipped", "in_transit"].includes(String(orderStatus(order)).toLowerCase())
  ).length
  const toReview = orders.filter((order: any) =>
    ["complete", "completed", "delivered"].includes(String(orderStatus(order)).toLowerCase())
  ).length

  const navItems: Array<{ id: View; label: string }> = [
    { id: "home", label: "Home" },
    { id: "orders", label: "Orders" },
    { id: "cart", label: "Cart" },
    { id: "wishlist", label: "Wishlist" },
    { id: "profile", label: "Profile" },
  ]

  return (
    <div className="min-h-screen bg-ui-bg-base text-ui-fg-base">
      <header className="border-b border-ui-border-base bg-white">
        <div className="content-container flex min-h-[96px] flex-col justify-center gap-4 py-5 small:flex-row small:items-center small:justify-between">
          <div>
            <p className="text-small-regular text-ui-fg-subtle">My Account</p>
            <h1 className="mt-1 text-2xl-semi text-ui-fg-base">
              {username ? decodeURIComponent(username) : "Welcome back"}
            </h1>
          </div>
          <div className="flex flex-wrap gap-2">
            <a className="border border-ui-border-base bg-white px-4 py-2 text-small-regular hover:bg-ui-bg-subtle" href="/hall">
              Hall
            </a>
            <a className="border border-ui-border-base bg-white px-4 py-2 text-small-regular hover:bg-ui-bg-subtle" href="/shop">
              Shop
            </a>
            <a className="border border-ui-border-base bg-white px-4 py-2 text-small-regular hover:bg-ui-bg-subtle" href={username ? `/${username}/cart` : "/guest/cart"}>
              Cart
            </a>
          </div>
        </div>
      </header>

      <div className="content-container grid grid-cols-1 gap-8 py-8 small:grid-cols-[220px_minmax(0,1fr)]">
        <aside className="small:sticky small:top-6 small:self-start">
          <nav className="grid grid-cols-5 gap-2 small:grid-cols-1">
            {navItems.map((item) => (
              <button
                className={
                  activeView === item.id
                    ? "h-11 border border-ui-fg-base bg-ui-fg-base px-3 text-small-semi text-ui-bg-base small:text-left"
                    : "h-11 border border-ui-border-base bg-white px-3 text-small-regular text-ui-fg-subtle hover:bg-ui-bg-subtle hover:text-ui-fg-base small:text-left"
                }
                key={item.id}
                onClick={() => setActiveView(item.id)}
                type="button"
              >
                {item.label}
              </button>
            ))}
          </nav>
        </aside>

        <main className="flex min-w-0 flex-col gap-8">
          {activeView === "home" && (
            <>
              <section className="grid grid-cols-2 gap-3 medium:grid-cols-4">
                <StatButton label="To Pay" onClick={() => setActiveView("orders")} value={String(pendingPayment)} />
                <StatButton label="To Receive" onClick={() => setActiveView("orders")} value={String(toReceive)} />
                <StatButton label="To Review" onClick={() => setActiveView("orders")} value={String(toReview)} />
                <StatButton label="Cart Items" onClick={() => setActiveView("cart")} value={String(cart?.total_quantity ?? 0)} />
              </section>
              <section className="grid grid-cols-1 gap-8 large:grid-cols-[minmax(0,1fr)_360px]">
                <OrdersView orders={orders.slice(0, 3)} query="" />
                <CartPreview cart={cart} />
              </section>
              <RecommendedProducts
                endpoint={`/recommendations/users/${encodeURIComponent(username || "guest")}`}
                title="Recommended For You"
                compact
              />
            </>
          )}

          {activeView === "orders" && (
            <>
              <div className="w-full small:w-80">
                <Input
                  label="Search orders"
                  name="order-search"
                  onChange={(event) => setQuery(event.target.value)}
                  value={query}
                />
              </div>
              <OrdersView orders={orders} query={query} />
            </>
          )}

          {activeView === "cart" && <CartPreview cart={cart} />}
          {activeView === "wishlist" && (
            <RecommendedProducts
              endpoint={`/recommendations/users/${encodeURIComponent(username || "guest")}`}
              title="Recommended For You"
              compact
            />
          )}
          {activeView === "profile" && <PlaceholderView title="Profile" />}
        </main>
      </div>
    </div>
  )
}

export default CustomerPanel
