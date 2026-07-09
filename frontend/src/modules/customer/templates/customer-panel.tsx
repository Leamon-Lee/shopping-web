"use client"

import { Badge, Button, Table } from "@medusajs/ui"
import Input from "@modules/common/components/input"
import NativeSelect from "@modules/common/components/native-select"
import { ReactNode, useMemo, useState } from "react"

const metrics = [
  { label: "Cart items", value: "3", detail: "Across 2 shops" },
  { label: "Active orders", value: "4", detail: "2 shipments in transit" },
  { label: "Completed orders", value: "28", detail: "6 this month" },
  { label: "Wishlist items", value: "12", detail: "Feeds recommendations" },
  { label: "Pending reviews", value: "5", detail: "Purchased products" },
  { label: "Saved addresses", value: "3", detail: "1 default address" },
  { label: "Payment methods", value: "2", detail: "Credit card and bank transfer" },
  { label: "Recommended items", value: "18", detail: "Personalisation enabled" },
]

const cartItems = [
  { product: "Linen Organizer Bin", variant: "Natural / Medium", shop: "Northline Home", quantity: 2, price: "CNY 129", stock: "In stock", subtotal: "CNY 258" },
  { product: "Cable Dock", variant: "Black", shop: "Desk Goods", quantity: 1, price: "CNY 59", stock: "In stock", subtotal: "CNY 59" },
  { product: "Desk Lamp Pro", variant: "Silver", shop: "Desk Goods", quantity: 1, price: "CNY 368", stock: "Low stock", subtotal: "CNY 368" },
]

const orders = [
  { order: "ORD-10842", shop: "Northline Home", items: 2, payment: "Paid", shipment: "Preparing", total: "CNY 428", date: "2026-07-09", status: "Unshipped" },
  { order: "ORD-10831", shop: "Desk Goods", items: 1, payment: "Paid", shipment: "In transit", total: "CNY 189", date: "2026-07-07", status: "Shipped" },
  { order: "ORD-10810", shop: "Everyday Carry Studio", items: 3, payment: "Pending", shipment: "Not started", total: "CNY 688", date: "2026-07-04", status: "Pay now" },
]

const wishlist = [
  { product: "Compact Sling Bag", shop: "Everyday Carry Studio", category: "Bags", price: "CNY 299", status: "In stock" },
  { product: "Aluminum Pen Tray", shop: "Desk Goods", category: "Stationery", price: "CNY 89", status: "In stock" },
  { product: "Wool Throw", shop: "Northline Home", category: "Home", price: "CNY 299", status: "Unavailable" },
]

const reviews = [
  { product: "Linen Organizer Bin", order: "ORD-10782", type: "Pending review", status: "Open" },
  { product: "Cable Dock", order: "ORD-10733", type: "Published review", status: "Published" },
  { product: "Desk Lamp Pro", order: "ORD-10692", type: "Edit requested", status: "Needs check" },
]

const addresses = [
  { label: "Home", receiver: "Nora Lee", phone: "+86 138 0000 0000", city: "Shanghai", status: "Default" },
  { label: "Office", receiver: "Nora Lee", phone: "+86 139 0000 0000", city: "Hangzhou", status: "Saved" },
]

const payments = [
  { method: "Credit card", detail: "Visa ending 4242", billing: "Nora Lee", status: "Default" },
  { method: "Electronic bank transfer", detail: "ICBC transfer account", billing: "Nora Lee", status: "Saved" },
]

const notifications = [
  { type: "Shipment", message: "ORD-10831 is in transit.", related: "ORD-10831", status: "Unread" },
  { type: "Payment", message: "ORD-10810 is waiting for payment.", related: "ORD-10810", status: "Unread" },
  { type: "Recommendation", message: "New home storage products match your preferences.", related: "Home", status: "Read" },
]

const navItems = [
  "Dashboard",
  "Cart",
  "Orders",
  "Order Detail",
  "Wishlist",
  "Preferences",
  "Reviews",
  "Addresses",
  "Payment Methods",
  "Notifications",
] as const

type CustomerView = (typeof navItems)[number]
type Row = Record<string, string | number>

const CustomerPanel = () => {
  const [activeView, setActiveView] = useState<CustomerView>("Dashboard")
  const [query, setQuery] = useState("")

  const handleViewChange = (view: CustomerView) => {
    setActiveView(view)
    setQuery("")
  }

  return (
    <div className="min-h-screen bg-ui-bg-base text-ui-fg-base">
      <header className="sticky top-0 z-40 border-b border-ui-border-base bg-white">
        <div className="content-container flex h-16 items-center justify-between txt-xsmall-plus text-ui-fg-subtle">
          <div className="flex items-center gap-x-4">
            <a className="text-ui-fg-base hover:text-ui-fg-base" href="/customer-panel">
              CUSTOMER PANEL
            </a>
            <span className="hidden text-ui-fg-muted small:inline">
              Shopping account
            </span>
          </div>
          <div className="flex items-center gap-x-4">
            <a className="hover:text-ui-fg-base" href="/hall">
              Customer View
            </a>
            <a className="hidden hover:text-ui-fg-base small:block" href="/manager">
              Manager View
            </a>
            <a className="hidden hover:text-ui-fg-base small:block" href="/admin">
              Admin View
            </a>
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
          </nav>
        </aside>

        <main className="flex min-w-0 flex-col gap-y-8">
          <ViewHeader activeView={activeView} query={query} setQuery={setQuery} />
          <CustomerViewContent activeView={activeView} query={query} />
        </main>
      </div>
    </div>
  )
}

const ViewHeader = ({
  activeView,
  query,
  setQuery,
}: {
  activeView: CustomerView
  query: string
  setQuery: (value: string) => void
}) => {
  return (
    <section className="flex flex-col justify-between gap-4 border-b border-ui-border-base pb-8 small:flex-row small:items-end">
      <div>
        <p className="txt-xsmall-plus uppercase text-ui-fg-muted">
          {activeView}
        </p>
        <h1 className="mt-2 text-2xl-semi text-ui-fg-base">
          {getViewTitle(activeView)}
        </h1>
        <p className="mt-2 max-w-2xl text-small-regular text-ui-fg-subtle">
          {getViewDescription(activeView)}
        </p>
      </div>
      {activeView === "Dashboard" || activeView === "Preferences" || activeView === "Order Detail" ? (
        <Button variant="secondary" className="h-10 w-full small:w-auto">
          {activeView === "Dashboard" ? "Continue shopping" : activeView === "Preferences" ? "Save preferences" : "Track shipment"}
        </Button>
      ) : (
        <div className="w-full small:w-72">
          <Input
            label={`Search ${activeView.toLowerCase()}`}
            name="customer-search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
        </div>
      )}
    </section>
  )
}

const CustomerViewContent = ({
  activeView,
  query,
}: {
  activeView: CustomerView
  query: string
}) => {
  if (activeView === "Dashboard") {
    return <DashboardView />
  }

  if (activeView === "Cart") {
    return (
      <div className="flex flex-col gap-6">
        <TableView
          title="Shopping cart"
          description="Review product variants, quantity, price, stock status, subtotal, and shop before checkout."
          rows={cartItems}
          actions={<Button>Checkout</Button>}
          query={query}
        />
        <div className="flex flex-col justify-between gap-4 rounded-rounded border border-ui-border-base bg-ui-bg-subtle p-5 small:flex-row small:items-center">
          <p className="text-small-regular text-ui-fg-subtle">
            Cart subtotal: CNY 685. Shipping and discounts are calculated during checkout.
          </p>
          <Button variant="secondary" className="h-10">
            Continue shopping
          </Button>
        </div>
      </div>
    )
  }

  if (activeView === "Orders") {
    return (
      <div className="flex flex-col gap-6">
        <div className="flex flex-wrap gap-2">
          {["All", "Pay now", "Unshipped", "Shipped", "Completed", "Refund"].map((item) => (
            <Button key={item} variant="secondary" className="h-9">
              {item}
            </Button>
          ))}
        </div>
        <TableView
          title="My orders"
          description="Pay, track shipment, confirm received, write reviews, or request refunds."
          rows={orders}
          actions={<Button variant="secondary">Track selected order</Button>}
          query={query}
        />
      </div>
    )
  }

  if (activeView === "Order Detail") {
    return <OrderDetailView />
  }

  if (activeView === "Wishlist") {
    return (
      <TableView
        title="Wishlist"
        description="Saved products can be moved to cart and also improve personalised recommendations."
        rows={wishlist}
        actions={<Button variant="secondary">Move selected to cart</Button>}
        query={query}
      />
    )
  }

  if (activeView === "Preferences") {
    return <PreferencesView />
  }

  if (activeView === "Reviews") {
    return (
      <TableView
        title="Reviews"
        description="Write, edit, or remove product reviews connected to purchased products."
        rows={reviews}
        actions={<Button variant="secondary">Write review</Button>}
        query={query}
      />
    )
  }

  if (activeView === "Addresses") {
    return (
      <TableView
        title="Saved addresses"
        description="Add, edit, delete, and set default shipping addresses."
        rows={addresses}
        actions={<Button variant="secondary">Add address</Button>}
        query={query}
      />
    )
  }

  if (activeView === "Payment Methods") {
    return (
      <TableView
        title="Payment methods"
        description="Manage credit card and electronic bank transfer payment methods."
        rows={payments}
        actions={<Button variant="secondary">Add payment method</Button>}
        query={query}
      />
    )
  }

  return (
    <TableView
      title="Notifications"
      description="Order status, shipment status, payment reminders, recommendations, and shop updates."
      rows={notifications}
      actions={<Button variant="secondary">Mark all as read</Button>}
      query={query}
    />
  )
}

const DashboardView = () => {
  return (
    <>
      <section className="grid grid-cols-1 gap-4 small:grid-cols-2 medium:grid-cols-4">
        {metrics.map((metric) => (
          <MetricCard key={metric.label} {...metric} />
        ))}
      </section>
      <section className="grid grid-cols-1 gap-6 medium:grid-cols-[1fr_320px]">
        <TableView
          title="Active orders"
          description="Recent customer orders with payment and shipment status."
          rows={orders}
          query=""
          compact
        />
        <InfoPanel title="Quick actions">
          <Button variant="secondary" className="h-10 justify-start">
            Continue shopping
          </Button>
          <Button variant="secondary" className="h-10 justify-start">
            View cart
          </Button>
          <Button variant="secondary" className="h-10 justify-start">
            Track orders
          </Button>
          <Button variant="secondary" className="h-10 justify-start">
            Manage preferences
          </Button>
          <Button variant="secondary" className="h-10 justify-start">
            Write reviews
          </Button>
        </InfoPanel>
      </section>
    </>
  )
}

const OrderDetailView = () => {
  return (
    <div className="grid grid-cols-1 gap-6 medium:grid-cols-[1fr_340px]">
      <div className="flex flex-col gap-6">
        <InfoPanel title="Order summary">
          <p>Order: ORD-10842</p>
          <p>Shop: Northline Home</p>
          <p>Total: CNY 428</p>
          <p>Status: paid, preparing shipment</p>
        </InfoPanel>
        <TableView
          title="Order items"
          description="OrderItem records in this order."
          rows={[
            { product: "Linen Organizer Bin", variant: "Natural / Medium", quantity: 2, subtotal: "CNY 258", status: "Preparing" },
            { product: "Cable Dock", variant: "Black", quantity: 1, subtotal: "CNY 59", status: "Preparing" },
          ]}
          query=""
        />
        <InfoPanel title="Order log">
          <p>2026-07-09 10:12 Payment completed.</p>
          <p>2026-07-09 10:16 Shop accepted order.</p>
          <p>2026-07-09 11:02 Shipment is being prepared.</p>
        </InfoPanel>
      </div>
      <div className="flex flex-col gap-6">
        <InfoPanel title="Payment info">
          <p>Payment: PAY-8842</p>
          <p>Method: Credit card ending 4242</p>
          <p>Status: Completed</p>
        </InfoPanel>
        <InfoPanel title="Shipment info">
          <p>Method: SF Express</p>
          <p>Tracking: Pending</p>
          <p>Address: 388 Wuding Road, Shanghai</p>
        </InfoPanel>
        <InfoPanel title="Customer actions">
          <Button variant="secondary" className="h-10">
            Track shipment
          </Button>
          <Button variant="secondary" className="h-10">
            Request refund
          </Button>
          <Button variant="secondary" className="h-10">
            Contact shop
          </Button>
        </InfoPanel>
      </div>
    </div>
  )
}

const PreferencesView = () => {
  return (
    <div className="grid grid-cols-1 gap-6 medium:grid-cols-[1fr_340px]">
      <div className="rounded-rounded border border-ui-border-base bg-white p-5">
        <h2 className="text-base-semi">Preference center</h2>
        <p className="mt-1 text-small-regular text-ui-fg-subtle">
          Recommendations can be based on browsing history, wishlist, orders,
          and selected preferences.
        </p>
        <div className="mt-5 grid grid-cols-1 gap-4 small:grid-cols-2">
          <NativeSelect name="favourite-category" defaultValue="home">
            <option value="home">Home</option>
            <option value="stationery">Stationery</option>
            <option value="bags">Bags</option>
            <option value="electronics">Electronics</option>
          </NativeSelect>
          <NativeSelect name="favourite-shop" defaultValue="Northline Home">
            <option value="Northline Home">Northline Home</option>
            <option value="Desk Goods">Desk Goods</option>
            <option value="Everyday Carry Studio">Everyday Carry Studio</option>
          </NativeSelect>
          <Input label="Preferred price range" name="price-range" defaultValue="CNY 50 - CNY 400" />
          <Input label="Brand preferences" name="brand-preferences" defaultValue="Minimal, durable, compact" />
        </div>
        <div className="mt-5 flex flex-col gap-3 text-small-regular text-ui-fg-subtle">
          <label className="flex items-center gap-2">
            <input type="checkbox" defaultChecked className="h-4 w-4" />
            Enable personalised recommendations
          </label>
          <label className="flex items-center gap-2">
            <input type="checkbox" defaultChecked className="h-4 w-4" />
            Use wishlist and order history
          </label>
          <label className="flex items-center gap-2">
            <input type="checkbox" className="h-4 w-4" />
            Include trending products outside favourite categories
          </label>
        </div>
      </div>
      <InfoPanel title="Recommendation sources">
        <p>Browsing history: electronics and home storage.</p>
        <p>Wishlist: bags, desk accessories, soft home goods.</p>
        <p>Orders: Northline Home and Desk Goods.</p>
        <p>Future data source: Hadoop, Hive, and Spark analytical outputs.</p>
      </InfoPanel>
    </div>
  )
}

const TableView = ({
  title,
  description,
  rows,
  actions,
  query,
  compact,
}: {
  title: string
  description: string
  rows: Row[]
  actions?: ReactNode
  query: string
  compact?: boolean
}) => {
  const filteredRows = useMemo(() => {
    const normalized = query.trim().toLowerCase()
    if (!normalized) {
      return rows
    }
    return rows.filter((row) =>
      Object.values(row).some((value) =>
        String(value).toLowerCase().includes(normalized)
      )
    )
  }, [query, rows])

  const columns = Object.keys(rows[0] || {})

  return (
    <div className="rounded-rounded border border-ui-border-base bg-white">
      <div className="flex flex-col justify-between gap-4 border-b border-ui-border-base p-5 small:flex-row small:items-center">
        <div>
          <h2 className="text-base-semi">{title}</h2>
          <p className="mt-1 text-small-regular text-ui-fg-subtle">
            {description}
          </p>
        </div>
        {actions}
      </div>
      <div className="overflow-x-auto">
        <Table>
          <Table.Header className="border-t-0">
            <Table.Row className="text-ui-fg-subtle txt-medium-plus">
              {columns.map((column, index) => (
                <Table.HeaderCell
                  key={column}
                  className={index > 1 && compact ? "hidden small:table-cell" : ""}
                >
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
                    <Table.Cell
                      key={column}
                      className={
                        columnIndex > 1 && compact
                          ? "hidden small:table-cell"
                          : columnIndex > 0
                          ? "text-ui-fg-subtle"
                          : ""
                      }
                    >
                      {isStatus ? (
                        <Badge color={getBadgeColor(String(value))}>
                          {String(value)}
                        </Badge>
                      ) : (
                        String(value)
                      )}
                    </Table.Cell>
                  )
                })}
              </Table.Row>
            ))}
          </Table.Body>
        </Table>
      </div>
      {filteredRows.length === 0 && (
        <div className="border-t border-ui-border-base p-6 text-small-regular text-ui-fg-subtle">
          No records match this search.
        </div>
      )}
    </div>
  )
}

const MetricCard = ({
  label,
  value,
  detail,
}: {
  label: string
  value: string
  detail: string
}) => {
  return (
    <div className="rounded-rounded border border-ui-border-base bg-white p-5">
      <p className="text-small-regular text-ui-fg-subtle">{label}</p>
      <p className="mt-3 text-xl-semi text-ui-fg-base">{value}</p>
      <p className="mt-1 text-small-regular text-ui-fg-muted">{detail}</p>
    </div>
  )
}

const InfoPanel = ({
  title,
  children,
}: {
  title: string
  children: ReactNode
}) => {
  return (
    <div className="rounded-rounded border border-ui-border-base bg-white p-5">
      <h2 className="text-base-semi">{title}</h2>
      <div className="mt-4 flex flex-col gap-y-3 text-small-regular text-ui-fg-subtle">
        {children}
      </div>
    </div>
  )
}

const getBadgeColor = (status: string) => {
  if (["Paid", "In transit", "In stock", "Published", "Default", "Completed", "Read"].includes(status)) {
    return "green"
  }
  if (["Unavailable", "Refund", "Blocked"].includes(status)) {
    return "red"
  }
  if (["Low stock", "Needs check"].includes(status)) {
    return "purple"
  }
  return "orange"
}

const getViewTitle = (view: CustomerView) => {
  const titles: Record<CustomerView, string> = {
    Dashboard: "Customer dashboard",
    Cart: "Shopping cart",
    Orders: "My orders",
    "Order Detail": "Order detail",
    Wishlist: "Wishlist",
    Preferences: "Preference center",
    Reviews: "Product reviews",
    Addresses: "Saved addresses",
    "Payment Methods": "Payment methods",
    Notifications: "Notifications",
  }

  return titles[view]
}

const getViewDescription = (view: CustomerView) => {
  const descriptions: Record<CustomerView, string> = {
    Dashboard:
      "View cart, active orders, completed orders, wishlist, reviews, addresses, payment methods, and recommended items.",
    Cart:
      "Manage cart items before checkout, including quantity, product variants, stock status, and shop grouping.",
    Orders:
      "Track payment, shipment, order status, refunds, reviews, and order-level actions.",
    "Order Detail":
      "Review order summary, shop info, items, payment info, shipment info, order log, and customer actions.",
    Wishlist:
      "Save products for later and use wishlist data to improve recommendations.",
    Preferences:
      "Choose favourite categories, shops, price ranges, brand preferences, and personalisation settings.",
    Reviews:
      "Write pending reviews and manage published reviews for purchased products.",
    Addresses:
      "Manage shipping addresses and choose a default address for checkout.",
    "Payment Methods":
      "Manage credit card and electronic bank transfer style payment methods.",
    Notifications:
      "Read order, shipment, payment, recommendation, shop, and product updates.",
  }

  return descriptions[view]
}

const formatColumn = (column: string) =>
  column
    .replace(/([A-Z])/g, " $1")
    .replace(/^./, (letter) => letter.toUpperCase())

export default CustomerPanel
