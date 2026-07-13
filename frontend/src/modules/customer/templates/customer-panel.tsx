"use client"

import { Badge, Button, Table } from "@medusajs/ui"
import ConfirmDialog from "@modules/common/components/confirm-dialog"
import { useEffect, useMemo, useState, useTransition } from "react"
import { useRouter } from "next/navigation"
import type { Account, Address, Order, Product, ShoppingCart } from "types/backend"
import { signout } from "@lib/data/customer"

type CustomerPanelProps = {
  cart: ShoppingCart | null
  orders: Order[]
  products: Product[]
  addresses: Address[]
  customer: Account | null
  completeOrderAction?: (orderNumber: string) => Promise<any>
  deleteOrderAction?: (orderNumber: string) => Promise<any>
  addAddressAction?: (formData: FormData) => Promise<any[]>
  updateAddressAction?: (addressId: string, formData: FormData) => Promise<any[]>
  deleteAddressAction?: (addressId: string) => Promise<any[]>
  addPaymentMethodAction?: (label: string) => Promise<any[]>
  deletePaymentMethodAction?: (pmId: string) => Promise<any[]>
  reviewsCount?: number
  reviews?: any[]
  deleteReviewAction?: (reviewId: string) => Promise<any>
}

// ── Types ────────────────────────────────────────────────────────────

type CustomerView =
  | "Dashboard" | "Cart" | "Orders" | "Order Detail"
  | "Wishlist" | "Preferences" | "Reviews"
  | "Addresses" | "Payment Methods"

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
    "Payment Methods": "Payment methods",
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
  query?: string; compact?: boolean
}) => {
  const filteredRows = useMemo(() => {
    const normalized = (query || "").trim().toLowerCase()
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

const CustomerPanel = ({
  cart, orders: initialOrders, products, addresses: initialAddresses, paymentMethods: initialPMs, customer,
  completeOrderAction, deleteOrderAction,
  addAddressAction, updateAddressAction, deleteAddressAction,
  addPaymentMethodAction, deletePaymentMethodAction, reviewsCount, reviews: initialReviews, deleteReviewAction,
}: CustomerPanelProps) => {
  const router = useRouter()
  const [isPending, startTransition] = useTransition()
  const [activeView, setActiveView] = useState<CustomerView>("Dashboard")
  const [orders, setOrders] = useState<Order[]>(initialOrders)
  const [addresses, setAddresses] = useState<Address[]>(initialAddresses)
  const [paymentMethods, setPaymentMethods] = useState<any[]>(initialPMs)
  const [reviews, setReviews] = useState<any[]>(initialReviews || [])
  const [addressForm, setAddressForm] = useState({ street: "", city: "", state: "", postal_code: "", country: "", is_default_shipping: false })
  const [editingAddrId, setEditingAddrId] = useState<string | null>(null)
  const [showAddrForm, setShowAddrForm] = useState(false)
  const [confirmDialog, setConfirmDialog] = useState<{
    open: boolean; title: string; message: string; onConfirm: () => void
  }>({ open: false, title: "", message: "", onConfirm: () => {} })

  // Sync from server props on navigation
  useEffect(() => {
    setOrders(initialOrders)
    setAddresses(initialAddresses)
    setPaymentMethods(initialPMs)
  }, [initialOrders, initialAddresses, initialPMs])

  const handleViewChange = (view: CustomerView) => {
    setActiveView(view)
    // view changed — data refreshes from server on re-render
  }

  const handleConfirmReceipt = (orderNumber: string) => {
    setConfirmDialog({
      open: true,
      title: "Confirm Receipt",
      message: `Are you sure you have received the items for order #${orderNumber}? This will mark the order as completed.`,
      onConfirm: () => {
        startTransition(async () => {
          try {
            const updated = await completeOrderAction!(orderNumber)
            setOrders((prev) =>
              prev.map((o) => (o.order_number === orderNumber ? updated : o))
            )
          } catch {}
          setConfirmDialog((d) => ({ ...d, open: false }))
        })
      },
    })
  }

  const handleDeleteOrder = (orderNumber: string) => {
    setConfirmDialog({
      open: true,
      title: "Delete Order",
      message: `Are you sure you want to delete order #${orderNumber}? This action cannot be undone.`,
      onConfirm: () => {
        startTransition(async () => {
          try {
            await deleteOrderAction!(orderNumber)
            setOrders((prev) => prev.filter((o) => o.order_number !== orderNumber))
          } catch {}
          setConfirmDialog((d) => ({ ...d, open: false }))
        })
      },
    })
  }

  const handleAddAddress = () => {
    if (!addAddressAction) return
    startTransition(async () => {
      try {
        const fd = new FormData()
        fd.set("street", addressForm.street)
        fd.set("city", addressForm.city)
        fd.set("state", addressForm.state)
        fd.set("postal_code", addressForm.postal_code)
        fd.set("country", addressForm.country)
        fd.set("is_default_shipping", String(addressForm.is_default_shipping))
        const result = await addAddressAction(fd)
        setAddresses(result)
        resetAddrForm()
      } catch {}
    })
  }

  const handleUpdateAddress = () => {
    if (!editingAddrId || !updateAddressAction) return
    startTransition(async () => {
      try {
        const fd = new FormData()
        fd.set("street", addressForm.street)
        fd.set("city", addressForm.city)
        fd.set("state", addressForm.state)
        fd.set("postal_code", addressForm.postal_code)
        fd.set("country", addressForm.country)
        fd.set("is_default_shipping", String(addressForm.is_default_shipping))
        const result = await updateAddressAction(editingAddrId, fd)
        setAddresses(result)
        resetAddrForm()
      } catch {}
    })
  }

  const handleDeleteAddress = (addrId: string) => {
    if (!deleteAddressAction) return
    setConfirmDialog({
      open: true, title: "Delete Address", message: "Are you sure you want to delete this address?",
      onConfirm: () => {
        startTransition(async () => {
          try {
            const result = await deleteAddressAction(addrId)
            setAddresses(result)
          } catch {}
          setConfirmDialog((d) => ({ ...d, open: false }))
        })
      },
    })
  }

  const resetAddrForm = () => {
    setAddressForm({ street: "", city: "", state: "", postal_code: "", country: "", is_default_shipping: false })
    setShowAddrForm(false)
    setEditingAddrId(null)
  }

  const navItems: CustomerView[] = [
    "Dashboard", "Cart", "Orders", "Reviews",
    "Addresses", "Payment Methods",
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
    total: `CNY ${order.payment?.amount?.toFixed(2) ?? "—"}`,
    date: order.order_date?.slice(0, 10) ?? "—",
    status: order.status === "created" ? "active" : order.status,
  }))

  const metrics = [
    { label: "Cart items", value: String(cart?.total_quantity ?? 0), detail: "From API" },
    { label: "Orders", value: String(orders.filter(o => o.status !== "completed" && o.status !== "canceled").length), detail: `${orders.filter(o => o.status === "shipped").length} shipments in transit` },
    { label: "Completed orders", value: String(orders.filter(o => o.status === "completed").length), detail: "Lifetime" },
    { label: "Reviews", value: String(reviewsCount || 0), detail: "Published reviews" },
    { label: "Products available", value: String(products.length), detail: "Across all shops" },
    { label: "Saved addresses", value: String(addresses.length), detail: addresses.length > 0 ? `${addresses.filter(a => a.is_default_shipping).length} default` : "Add one" },
    { label: "Payment methods", value: String(paymentMethods.length), detail: paymentMethods.length > 0 ? "Available" : "Add one" },
    { label: "Cart subtotal", value: `CNY ${cart?.subtotal?.toFixed(2) ?? "0.00"}`, detail: `${cart?.items.length ?? 0} items` },
  ]

  return (
    <div className="min-h-screen bg-ui-bg-base text-ui-fg-base">
      <ConfirmDialog
        open={confirmDialog.open}
        title={confirmDialog.title}
        message={confirmDialog.message}
        onConfirm={confirmDialog.onConfirm}
        onCancel={() => setConfirmDialog((d) => ({ ...d, open: false }))}
        loading={isPending}
      />
      <header className="sticky top-0 z-40 border-b border-ui-border-base bg-gray-200">
        <div className="content-container flex h-16 items-center justify-between txt-xsmall-plus text-ui-fg-subtle">
          <div className="flex items-center gap-x-4">
            <span className="text-ui-fg-base">CUSTOMER PANEL</span>
            <span className="hidden text-ui-fg-muted small:inline">Shopping account</span>
          </div>
          <div className="flex items-center gap-x-4">
            <a className="hover:text-ui-fg-base" href="/hall">Hall</a>
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
          </nav>
        </aside>

        <main className="flex min-w-0 flex-col gap-y-8">
          <ViewHeader activeView={activeView} />
          {activeView === "Orders" ? (
            <OrdersView orders={orders} isPending={isPending} onConfirmReceipt={handleConfirmReceipt} onDeleteOrder={handleDeleteOrder} />
          ) : activeView === "Reviews" ? (
            <ReviewsView reviews={reviews} isPending={isPending} onDelete={(id) => {
              setConfirmDialog({ open: true, title: "Delete Review", message: "Are you sure you want to delete this review?", onConfirm: () => {
                startTransition(async () => { try { if (deleteReviewAction) { await deleteReviewAction(id); setReviews((p) => p.filter((r) => r.id !== id)) } } catch {}; setConfirmDialog((d) => ({ ...d, open: false })) })
              }})
            }} />
          ) : activeView === "Payment Methods" ? (
            <PaymentMethodsView pms={paymentMethods} isPending={isPending}
              onAdd={(label) => { startTransition(async () => { try { const r = await addPaymentMethodAction!(label); setPaymentMethods(r) } catch {} }) }}
              onDelete={(id) => { startTransition(async () => { try { const r = await deletePaymentMethodAction!(id); setPaymentMethods(r) } catch {} }) }} />
          ) : activeView === "Addresses" ? (
            <AddressesView
              addresses={addresses}
              addressForm={addressForm}
              setAddressForm={setAddressForm}
              editingAddrId={editingAddrId}
              showAddrForm={showAddrForm}
              setShowAddrForm={setShowAddrForm}
              isPending={isPending}
              onAdd={handleAddAddress}
              onUpdate={handleUpdateAddress}
              onDelete={handleDeleteAddress}
              onEdit={(addr) => {
                if (!addr.id) return
                setEditingAddrId(addr.id)
                setAddressForm({ street: addr.street || "", city: addr.city || "", state: addr.state || "", postal_code: addr.postal_code || "", country: addr.country || "", is_default_shipping: addr.is_default_shipping || false })
                setShowAddrForm(true)
              }}
              onCancelEdit={resetAddrForm}
            />
          ) : (
            <CustomerViewContent activeView={activeView} cartRows={cartRows} orderRows={orderRows} metrics={metrics} />
          )}
        </main>
      </div>
    </div>
  )
}

// ── View Header ──────────────────────────────────────────────────────

const ViewHeader = ({ activeView }: {
  activeView: CustomerView
}) => (
  <section className="flex flex-col justify-between gap-4 border-b border-ui-border-base pb-8 small:flex-row small:items-end">
    <div>
      <p className="txt-xsmall-plus uppercase text-ui-fg-muted">{activeView}</p>
      <h1 className="mt-2 text-2xl-semi text-ui-fg-base">{getViewTitle(activeView)}</h1>
      <p className="mt-2 max-w-2xl text-small-regular text-ui-fg-subtle">{getViewDescription(activeView)}</p>
    </div>
    {activeView === "Dashboard" ? (
      <a href="/hall"><Button variant="secondary" className="h-10 w-full small:w-auto">Continue shopping</Button></a>
    ) : null}
  </section>
)

// ── View Content ─────────────────────────────────────────────────────

const CustomerViewContent = ({ activeView, cartRows, orderRows, metrics }: {
  activeView: CustomerView; cartRows: Row[]; orderRows: Row[]; metrics: { label: string; value: string; detail: string }[]
}) => {
  if (activeView === "Dashboard") {
    return (
      <>
        <section className="grid grid-cols-1 gap-4 small:grid-cols-2 medium:grid-cols-4">
          {metrics.map((m) => <MetricCard key={m.label} {...m} />)}
        </section>
        <section className="grid grid-cols-1 gap-6 medium:grid-cols-[1fr_320px]">
          <TableView title="Orders" description="Recent customer orders with shipment status." rows={orderRows} compact />
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
        <div className="bg-white border border-ui-border-base rounded-lg p-6">
          <p className="text-base-regular">{cartRows.length} items in your cart</p>
          <p className="text-small-regular text-ui-fg-muted mt-1">Select items and proceed with payment on the full cart page.</p>
          <div className="flex gap-3 mt-4">
            <a href="/cart"><Button>Go to Cart</Button></a>
            <a href="/hall"><Button variant="secondary">Continue shopping</Button></a>
          </div>
        </div>
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

// ── Orders View ────────────────────────────────────────────────────

const OrdersView = ({
  orders, isPending, onConfirmReceipt, onDeleteOrder,
}: {
  orders: Order[]; isPending: boolean
  onConfirmReceipt: (orderNumber: string) => void; onDeleteOrder: (orderNumber: string) => void
}) => {
  const activeOrders = orders.filter((o) => o.status !== "completed" && o.status !== "canceled")
  const completedOrders = orders.filter((o) => o.status === "completed")

  return (
    <div className="grid grid-cols-1 medium:grid-cols-2 gap-6">
      {/* Active Orders */}
      <div className="flex flex-col gap-4">
        <h3 className="text-lg-semi">Active Orders</h3>
        {activeOrders.map((order) => (
          <div key={order.order_number} className="bg-white border border-ui-border-base rounded-lg p-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-base-regular font-medium">Order #{order.order_number}</p>
                <p className="text-small-regular text-ui-fg-muted">
                  {order.order_date ? new Date(order.order_date).toLocaleDateString() : "—"} · Status: {order.status}
                </p>
                <p className="text-small-regular mt-1">
                  {order.items?.length || 0} items · {(order.payment as any)?.amount ? `CNY ${(order.payment as any).amount.toFixed(2)}` : "—"}
                </p>
              </div>
              <Button variant="secondary" className="h-8 text-small-regular" onClick={() => onConfirmReceipt(order.order_number)} disabled={isPending}>
                Confirm Receipt
              </Button>
            </div>
          </div>
        ))}
        {activeOrders.length === 0 && (
          <div className="bg-ui-bg-subtle rounded-lg p-8 text-center text-small-regular text-ui-fg-muted">No active orders</div>
        )}
      </div>

      {/* Completed Orders */}
      <div className="flex flex-col gap-4">
        <h3 className="text-lg-semi">Completed Orders</h3>
        {completedOrders.length === 0 ? (
          <div className="bg-ui-bg-subtle rounded-lg p-8 text-center text-small-regular text-ui-fg-muted">No completed orders</div>
        ) : (
          completedOrders.map((order) => (
            <div key={order.order_number} className="bg-white border border-ui-border-base rounded-lg p-5">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-base-regular font-medium">Order #{order.order_number}</p>
                  <p className="text-small-regular text-ui-fg-muted">
                    {order.order_date ? new Date(order.order_date).toLocaleDateString() : "—"} · Completed
                  </p>
                  <p className="text-small-regular mt-1">
                    {order.items?.length || 0} items · {(order.payment as any)?.amount ? `CNY ${(order.payment as any).amount.toFixed(2)}` : "—"}
                  </p>
                </div>
                <Button variant="secondary" className="h-8 text-small-regular text-rose-600 hover:text-rose-700" onClick={() => onDeleteOrder(order.order_number)} disabled={isPending}>
                  Delete
                </Button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}

// ── Addresses View ─────────────────────────────────────────────────

const AddressesView = ({
  addresses, addressForm, setAddressForm, editingAddrId, showAddrForm, setShowAddrForm,
  isPending, onAdd, onUpdate, onDelete, onEdit, onCancelEdit,
}: {
  addresses: Address[]
  addressForm: any; setAddressForm: any; editingAddrId: string | null; showAddrForm: boolean; setShowAddrForm: (v: boolean) => void
  isPending: boolean
  onAdd: () => void; onUpdate: () => void; onDelete: (id: string) => void
  onEdit: (addr: Address) => void; onCancelEdit: () => void
}) => (
  <div className="flex flex-col gap-4">
    {addresses.map((addr, i) => (
      <div key={addr.id || i} className={`bg-white border border-ui-border-base rounded-lg p-5 ${addr.is_default_shipping ? "border-blue-400 border-2" : ""}`}>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-base-regular">{addr.street}</p>
            <p className="text-small-regular text-ui-fg-muted">
              {addr.city}{addr.state ? `, ${addr.state}` : ""} {addr.postal_code}, {addr.country}
            </p>
            {addr.is_default_shipping && <Badge color="blue">Default</Badge>}
          </div>
          <div className="flex gap-2">
            <Button variant="secondary" className="h-8 text-small-regular" onClick={() => onEdit(addr)}>Edit</Button>
            <Button variant="secondary" className="h-8 text-small-regular text-rose-600" onClick={() => addr.id && onDelete(addr.id)} disabled={isPending}>Delete</Button>
          </div>
        </div>
      </div>
    ))}
    {addresses.length === 0 && !showAddrForm && (
      <div className="bg-ui-bg-subtle rounded-lg p-8 text-center text-small-regular text-ui-fg-muted">No saved addresses</div>
    )}

    {!showAddrForm ? (
      <button className="text-small-regular text-blue-600 hover:text-blue-800 text-left" onClick={() => setShowAddrForm(true)}>+ Add new address</button>
    ) : (
      <div className="border border-ui-border-base rounded-lg p-4 flex flex-col gap-y-3 bg-white">
        <p className="text-small-regular font-medium">{editingAddrId ? "Edit address" : "New address"}</p>
        <input className="border rounded p-2 text-small-regular" placeholder="Street" value={addressForm.street} onChange={(e: any) => setAddressForm({ ...addressForm, street: e.target.value })} />
        <div className="grid grid-cols-2 gap-2">
          <input className="border rounded p-2 text-small-regular" placeholder="City" value={addressForm.city} onChange={(e: any) => setAddressForm({ ...addressForm, city: e.target.value })} />
          <input className="border rounded p-2 text-small-regular" placeholder="State" value={addressForm.state} onChange={(e: any) => setAddressForm({ ...addressForm, state: e.target.value })} />
        </div>
        <div className="grid grid-cols-2 gap-2">
          <input className="border rounded p-2 text-small-regular" placeholder="Postal code" value={addressForm.postal_code} onChange={(e: any) => setAddressForm({ ...addressForm, postal_code: e.target.value })} />
          <input className="border rounded p-2 text-small-regular" placeholder="Country" value={addressForm.country} onChange={(e: any) => setAddressForm({ ...addressForm, country: e.target.value })} />
        </div>
        <label className="flex items-center gap-2 text-small-regular">
          <input type="checkbox" checked={addressForm.is_default_shipping} onChange={(e: any) => setAddressForm({ ...addressForm, is_default_shipping: e.target.checked })} />
          Set as default
        </label>
        <div className="flex gap-2">
          <Button variant="secondary" className="h-8 text-small-regular" onClick={onCancelEdit}>Cancel</Button>
          <Button variant="secondary" className="h-8 text-small-regular" onClick={editingAddrId ? onUpdate : onAdd} disabled={isPending}>
            {editingAddrId ? "Update" : "Save"}
          </Button>
        </div>
      </div>
    )}
  </div>
)

// ── Payment Methods View ────────────────────────────────────────────

const PaymentMethodsView = ({ pms, isPending, onAdd, onDelete }: {
  pms: any[]; isPending: boolean; onAdd: (label: string) => void; onDelete: (id: string) => void
}) => {
  const [newLabel, setNewLabel] = useState("")
  const [showForm, setShowForm] = useState(false)
  return (
    <div className="flex flex-col gap-4">
      {pms.map((pm) => (
        <div key={pm.id} className="bg-white border border-ui-border-base rounded-lg p-5 flex items-center justify-between">
          <div>
            <p className="text-base-regular">{pm.label}</p>
            <p className="text-small-regular text-ui-fg-muted capitalize">{pm.method_type.replace("_", " ")}</p>
          </div>
          <Button variant="secondary" className="h-8 text-small-regular text-rose-600" onClick={() => onDelete(pm.id)} disabled={isPending}>Delete</Button>
        </div>
      ))}
      {pms.length === 0 && !showForm && <div className="bg-ui-bg-subtle rounded-lg p-8 text-center text-small-regular text-ui-fg-muted">No payment methods</div>}
      {!showForm ? (
        <button className="text-small-regular text-blue-600 hover:text-blue-800 text-left" onClick={() => setShowForm(true)}>+ Add payment method</button>
      ) : (
        <div className="flex gap-2">
          <input className="border rounded p-2 text-small-regular flex-1" placeholder="e.g. My Credit Card" value={newLabel} onChange={(e) => setNewLabel(e.target.value)} />
          <Button variant="secondary" className="h-8 text-small-regular" onClick={() => { setShowForm(false); setNewLabel("") }}>Cancel</Button>
          <Button variant="secondary" className="h-8 text-small-regular" onClick={() => { if (!newLabel.trim()) return; onAdd(newLabel.trim()); setNewLabel(""); setShowForm(false) }} disabled={isPending}>Save</Button>
        </div>
      )}
    </div>
  )
}

// ── Reviews View ───────────────────────────────────────────────────

const ReviewsView = ({ reviews, isPending, onDelete }: { reviews: any[]; isPending: boolean; onDelete: (id: string) => void }) => (
  <div className="flex flex-col gap-4">
    {reviews.map((r) => (
      <div key={r.id} className="bg-white border border-ui-border-base rounded-lg p-5 flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-yellow-500">{'★'.repeat(r.rating || 0)}{'☆'.repeat(5 - (r.rating || 0))}</span>
            <span className="text-small-regular text-ui-fg-subtle">{r.created_at ? new Date(r.created_at).toLocaleDateString() : ""}</span>
          </div>
          {r.content && <p className="text-small-regular mt-1">{r.content}</p>}
          {r.product_name && (
            <a href={`/shop/${r.product_slug || r.product_name}`} className="text-small-regular text-blue-600 hover:text-blue-800 mt-1 inline-block">
              {r.product_name}
            </a>
          )}
        </div>
        <Button variant="secondary" className="h-8 text-small-regular text-rose-600" onClick={() => onDelete(r.id)} disabled={isPending}>Delete</Button>
      </div>
    ))}
    {reviews.length === 0 && <div className="bg-ui-bg-subtle rounded-lg p-8 text-center text-small-regular text-ui-fg-muted">No reviews yet</div>}
  </div>
)

export default CustomerPanel
