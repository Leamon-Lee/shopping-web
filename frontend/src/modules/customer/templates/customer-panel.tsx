"use client"

import { Badge, Button, Table } from "@medusajs/ui"
import Spinner from "@modules/common/icons/spinner"
import Input from "@modules/common/components/input"
import { useEffect, useMemo, useState } from "react"
import type { CartItem, Order, Product, ShoppingCart } from "types/backend"
import { getCart, listOrders, listProducts } from "api/backend-client"
import { signout } from "@lib/data/customer"

// ── Types ────────────────────────────────────────────────────────────

type CustomerView =
  | "Dashboard" | "Cart" | "Orders" | "Order Detail"
  | "Wishlist" | "Preferences" | "Reviews"
  | "Addresses" | "Payment Methods" | "Notifications"

type Row = Record<string, string | number>

// ── Helpers ──────────────────────────────────────────────────────────

const getBadgeColor = (status: string) => {
  if (["Paid", "In transit", "In stock", "Published", "Default", "Completed", "Read", "completed", "shipped"].includes(status)) return "green"
  if (["Unavailable", "Refund", "Blocked", "failed", "canceled"].includes(status)) return "red"
  if (["Low stock", "Needs check", "pending"].includes(status)) return "purple"
  return "orange"
}

const formatColumn = (column: string) =>
  column.replace(/([A-Z])/g, " $1").replace(/^./, (letter) => letter.toUpperCase())

const getViewTitle = (view: CustomerView) => {
  const titles: Record<CustomerView, string> = {
    Dashboard: "Customer dashboard", Cart: "Shopping cart",
    Orders: "My orders", "Order Detail": "Order detail",
    Wishlist: "Wishlist", Preferences: "Preference center",
    Reviews: "Product reviews", Addresses: "Saved addresses",
    "Payment Methods": "Payment methods", Notifications: "Notifications",
  }
  return titles[view]
}

const getViewDescription = (view: CustomerView) => {
  const descriptions: Record<CustomerView, string> = {
    Dashboard: "View cart, active orders, completed orders, wishlist, reviews, addresses, payment methods, and recommended items.",
    Cart: "Manage cart items before checkout, including quantity, product variants, stock status, and shop grouping.",
    Orders: "Track payment, shipment, order status, refunds, reviews, and order-level actions.",
    "Order Detail": "Review order summary, shop info, items, payment info, shipment info, order log, and customer actions.",
    Wishlist: "Save products for later and use wishlist data to improve recommendations.",
    Preferences: "Choose favourite categories, shops, price ranges, brand preferences, and personalisation settings.",
    Reviews: "Write pending reviews and manage published reviews for purchased products.",
    Addresses: "Manage shipping addresses and choose a default address for checkout.",
    "Payment Methods": "Manage credit card and electronic bank transfer style payment methods.",
    Notifications: "Read order, shipment, payment, recommendation, shop, and product updates.",
  }
  return descriptions[view]
}

// ── Components ───────────────────────────────────────────────────────

const MetricCard = ({ label, value, detail }: { label: string; value: string; detail: string }) => (
  <div className="rounded-rounded border border-ui-border-base bg-white p-5">
    <p className="text-small-regular text-ui-fg-subtle">{label}</p>
    <p className="mt-3 text-xl-semi text-ui-fg-base">{value}</p>
    <p className="mt-1 text-small-regular text-ui-fg-muted">{detail}</p>
  </div>
)

const InfoPanel = ({ title, children }: { title: string; children: React.ReactNode }) => (
  <div className="rounded-rounded border border-ui-border-base bg-white p-5">
    <h2 className="text-base-semi">{title}</h2>
    <div className="mt-4 flex flex-col gap-y-3 text-small-regular text-ui-fg-subtle">{children}</div>
  </div>
)

const TableView = ({ title, description, rows, actions, query, compact }: {
  title: string; description: string; rows: Row[]; actions?: React.ReactNode
  query: string; compact?: boolean
}) => {
  const filteredRows = useMemo(() => {
    const normalized = query.trim().toLowerCase()
    if (!normalized) return rows
    return rows.filter((row) =>
      Object.values(row).some((value) => String(value).toLowerCase().includes(normalized))
    )
  }, [query, rows])
  const columns = Object.keys(rows[0] || {})
  return (
    <div className="rounded-rounded border border-ui-border-base bg-white">
      <div className="flex flex-col justify-between gap-4 border-b border-ui-border-base p-5 small:flex-row small:items-center">
        <div>
          <h2 className="text-base-semi">{title}</h2>
          <p className="mt-1 text-small-regular text-ui-fg-subtle">{description}</p>
        </div>
        {actions}
      </div>
      {rows.length > 0 ? (
        <div className="overflow-x-auto">
          <Table>
            <Table.Header className="border-t-0">
              <Table.Row className="text-ui-fg-subtle txt-medium-plus">
                {columns.map((column, index) => (
                  <Table.HeaderCell key={column} className={index > 1 && compact ? "hidden small:table-cell" : ""}>
                    {formatColumn(column)}
                  </Table.HeaderCell>
                ))}
              </Table.Row>
            </Table.Header>
            <Table.Body>
              {filteredRows.map((row, rowIndex) => (
                <Table.Row key={`${title}-${rowIndex}`}>
                  {columns.map((column, columnIndex) => {
                    const value = row[column]
                    const isStatus = ["status", "payment", "shipment", "stock"].includes(column)
                    return (
                      <Table.Cell key={column} className={
                        columnIndex > 1 && compact ? "hidden small:table-cell" : columnIndex > 0 ? "text-ui-fg-subtle" : ""
                      }>
                        {isStatus ? <Badge color={getBadgeColor(String(value))}>{String(value)}</Badge> : String(value)}
                      </Table.Cell>
                    )
                  })}
                </Table.Row>
              ))}
            </Table.Body>
          </Table>
        </div>
      ) : null}
      {filteredRows.length === 0 && (
        <div className="border-t border-ui-border-base p-6 text-small-regular text-ui-fg-subtle">
          {rows.length === 0 ? "No data available yet." : "No records match this search."}
        </div>
      )}
    </div>
  )
}

// ── Main Panel ───────────────────────────────────────────────────────

const CustomerPanel = () => {
  const [activeView, setActiveView] = useState<CustomerView>("Dashboard")
  const [query, setQuery] = useState("")
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [cart, setCart] = useState<ShoppingCart | null>(null)
  const [orders, setOrders] = useState<Order[]>([])
  const [products, setProducts] = useState<Product[]>([])

  const fetchData = async () => {
    setLoading(true)
    setError(null)
    try {
      const [cartData, ordersData, productsData] = await Promise.all([
        getCart().catch(() => null),
        listOrders().catch(() => []),
        listProducts().catch(() => []),
      ])
      setCart(cartData)
      setOrders(ordersData)
      setProducts(productsData)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load data.")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  const handleViewChange = (view: CustomerView) => {
    setActiveView(view)
    setQuery("")
  }

  const navItems: CustomerView[] = [
    "Dashboard", "Cart", "Orders", "Order Detail",
    "Wishlist", "Preferences", "Reviews",
    "Addresses", "Payment Methods", "Notifications",
  ]

  // ── Derived data ─────────────────────────────────────────────────

  const cartRows: Row[] = (cart?.items ?? []).map((item) => ({
    product: item.product_title,
    variant: item.variant?.name ?? "Default",
    shop: (item.product as any)?.shop?.shop_name ?? "—",
    quantity: item.quantity,
    price: `CNY ${item.unit_price?.toFixed(2) ?? "—"}`,
    stock: (item.variant?.inventory_count ?? 0) > 0 ? "In stock" : "Unavailable",
    subtotal: `CNY ${item.total?.toFixed(2) ?? "—"}`,
  }))

  const orderRows: Row[] = orders.map((order) => ({
    order: order.order_number,
    items: order.items.length,
    payment: order.payment?.status ?? "pending",
    shipment: order.shipments?.[0]?.status ?? "Not started",
    total: `CNY ${order.payment?.amount?.toFixed(2) ?? "—"}`,
    date: order.order_date?.slice(0, 10) ?? "—",
    status: order.status,
  }))

  const metrics = [
    { label: "Cart items", value: String(cart?.total_quantity ?? 0), detail: "From API" },
    { label: "Active orders", value: String(orders.filter(o => o.status !== "complete" && o.status !== "canceled").length), detail: `${orders.filter(o => o.status === "shipped").length} shipments in transit` },
    { label: "Completed orders", value: String(orders.filter(o => o.status === "complete").length), detail: "Lifetime" },
    { label: "Wishlist items", value: "0", detail: "Coming soon" },
    { label: "Products available", value: String(products.length), detail: "Across all shops" },
    { label: "Saved addresses", value: "—", detail: "Sign in to view" },
    { label: "Payment methods", value: "—", detail: "Sign in to view" },
    { label: "Cart subtotal", value: `CNY ${cart?.subtotal?.toFixed(2) ?? "0.00"}`, detail: `${cart?.items.length ?? 0} items` },
  ]

  // ── Render ──────────────────────────────────────────────────────

  if (error) {
    return (
      <div className="min-h-screen bg-ui-bg-base flex items-center justify-center">
        <div className="text-center">
          <p className="text-rose-500 text-base-semi">Failed to load data</p>
          <p className="mt-2 text-small-regular text-ui-fg-subtle">{error}</p>
          <Button variant="secondary" className="mt-4" onClick={fetchData}>Retry</Button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-ui-bg-base text-ui-fg-base">
      <header className="sticky top-0 z-40 border-b border-ui-border-base bg-white">
        <div className="content-container flex h-16 items-center justify-between txt-xsmall-plus text-ui-fg-subtle">
          <div className="flex items-center gap-x-4">
            <span className="text-ui-fg-base">CUSTOMER PANEL</span>
            <span className="hidden text-ui-fg-muted small:inline">Shopping account</span>
          </div>
          <div className="flex items-center gap-x-4">
            <a className="hover:text-ui-fg-base" href="/hall">Customer View</a>
            <a className="hidden hover:text-ui-fg-base small:block" href="/manager">Manager View</a>
            <a className="hidden hover:text-ui-fg-base small:block" href="/admin">Admin View</a>
            <button
              type="button"
              className="hover:text-ui-fg-base"
              onClick={() => signout()}
            >
              Log out
            </button>
          </div>
        </div>
      </header>

      <div className="content-container grid grid-cols-1 gap-8 py-8 small:grid-cols-[240px_1fr]">
        <aside className="small:sticky small:top-24 small:self-start">
          <nav className="flex flex-row gap-2 overflow-x-auto border-b border-ui-border-base pb-4 small:flex-col small:overflow-visible small:border-b-0 small:pb-0">
            {navItems.map((item) => (
              <button
                key={item}
                onClick={() => handleViewChange(item)}
                className={
                  activeView === item
                    ? "whitespace-nowrap rounded-md bg-ui-bg-subtle px-3 py-2 text-left text-small-semi text-ui-fg-base small:w-full"
                    : "whitespace-nowrap rounded-md px-3 py-2 text-left text-small-regular text-ui-fg-subtle hover:bg-ui-bg-subtle hover:text-ui-fg-base small:w-full"
                }
              >
                {item}
              </button>
            ))}
            <button
              type="button"
              onClick={() => signout()}
              className="whitespace-nowrap rounded-md px-3 py-2 text-left text-small-regular text-ui-fg-subtle hover:bg-ui-bg-subtle hover:text-ui-fg-base small:w-full"
            >
              Log out
            </button>
          </nav>
        </aside>

        <main className="flex min-w-0 flex-col gap-y-8">
          <ViewHeader activeView={activeView} query={query} setQuery={setQuery} />
          {loading ? (
            <div className="flex items-center justify-center py-20">
              <Spinner />
            </div>
          ) : (
            <CustomerViewContent activeView={activeView} query={query} cartRows={cartRows} orderRows={orderRows} metrics={metrics} />
          )}
        </main>
      </div>
    </div>
  )
}

// ── View Header ──────────────────────────────────────────────────────

const ViewHeader = ({ activeView, query, setQuery }: {
  activeView: CustomerView; query: string; setQuery: (v: string) => void
}) => (
  <section className="flex flex-col justify-between gap-4 border-b border-ui-border-base pb-8 small:flex-row small:items-end">
    <div>
      <p className="txt-xsmall-plus uppercase text-ui-fg-muted">{activeView}</p>
      <h1 className="mt-2 text-2xl-semi text-ui-fg-base">{getViewTitle(activeView)}</h1>
      <p className="mt-2 max-w-2xl text-small-regular text-ui-fg-subtle">{getViewDescription(activeView)}</p>
    </div>
    {["Dashboard", "Preferences", "Order Detail"].includes(activeView) ? (
      <Button variant="secondary" className="h-10 w-full small:w-auto">
        {activeView === "Dashboard" ? "Continue shopping" : activeView === "Preferences" ? "Save preferences" : "Track shipment"}
      </Button>
    ) : (
      <div className="w-full small:w-72">
        <Input label={`Search ${activeView.toLowerCase()}`} name="customer-search" value={query} onChange={(e) => setQuery(e.target.value)} />
      </div>
    )}
  </section>
)

// ── View Content ─────────────────────────────────────────────────────

const CustomerViewContent = ({ activeView, query, cartRows, orderRows, metrics }: {
  activeView: CustomerView; query: string; cartRows: Row[]; orderRows: Row[]; metrics: { label: string; value: string; detail: string }[]
}) => {
  if (activeView === "Dashboard") {
    return (
      <>
        <section className="grid grid-cols-1 gap-4 small:grid-cols-2 medium:grid-cols-4">
          {metrics.map((m) => <MetricCard key={m.label} {...m} />)}
        </section>
        <section className="grid grid-cols-1 gap-6 medium:grid-cols-[1fr_320px]">
          <TableView title="Active orders" description="Recent customer orders with payment and shipment status." rows={orderRows} query="" compact />
          <InfoPanel title="Quick actions">
            <p>Continue shopping</p><p>View cart</p><p>Track orders</p><p>Manage preferences</p><p>Write reviews</p>
          </InfoPanel>
        </section>
      </>
    )
  }

  if (activeView === "Cart") {
    return (
      <div className="flex flex-col gap-6">
        <TableView title="Shopping cart" description="Review product variants, quantity, price, stock status, subtotal, and shop before checkout." rows={cartRows} query={query} actions={<Button>Checkout</Button>} />
        <div className="flex flex-col justify-between gap-4 rounded-rounded border border-ui-border-base bg-ui-bg-subtle p-5 small:flex-row small:items-center">
          <p className="text-small-regular text-ui-fg-subtle">Cart data loaded from the backend API.</p>
          <Button variant="secondary" className="h-10">Continue shopping</Button>
        </div>
      </div>
    )
  }

  if (activeView === "Orders") {
    return (
      <div className="flex flex-col gap-6">
        <div className="flex flex-wrap gap-2">
          {["All", "Pay now", "Unshipped", "Shipped", "Completed", "Refund"].map((f) => (
            <Button key={f} variant="secondary" className="h-9">{f}</Button>
          ))}
        </div>
        <TableView title="My orders" description="Pay, track shipment, confirm received, write reviews, or request refunds." rows={orderRows} query={query} actions={<Button variant="secondary">Track selected order</Button>} />
      </div>
    )
  }

  if (activeView === "Order Detail") {
    return (
      <div className="grid grid-cols-1 gap-6 medium:grid-cols-[1fr_340px]">
        <InfoPanel title="Order detail">
          <p>Select an order from the Orders view to see details.</p>
          <p>Order summary, items, payment info, and shipment info will appear here.</p>
        </InfoPanel>
        <InfoPanel title="Customer actions">
          <p>Track shipment</p><p>Request refund</p><p>Contact shop</p>
        </InfoPanel>
      </div>
    )
  }

  // Placeholder views for features not yet backed by API
  return (
    <div className="rounded-rounded border border-ui-border-base bg-ui-bg-subtle p-12 text-center">
      <h2 className="text-base-semi">{getViewTitle(activeView)}</h2>
      <p className="mt-2 text-small-regular text-ui-fg-subtle">{getViewDescription(activeView)}</p>
      <p className="mt-4 text-small-regular text-ui-fg-muted">This view will be connected to the backend in a future update.</p>
    </div>
  )
}

export default CustomerPanel
