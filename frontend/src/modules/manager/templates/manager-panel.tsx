"use client"

import { Badge, Button, Table } from "@medusajs/ui"
import Spinner from "@modules/common/icons/spinner"
import Input from "@modules/common/components/input"
import { useEffect, useMemo, useState } from "react"
import {
  getManagerPanel, getManagerProducts, getManagerOrders,
  getManagerShops, createManagerShop, createManagerProduct,
  updateManagerOrderStatus, createManagerShipment,
  getManagerIncome, getManagerReports, getManagerShipments,
} from "api/backend-client"

type ManagerView =
  | "Dashboard" | "My Shops" | "Products" | "Orders"
  | "Shipments" | "Income" | "Reports" | "Profile"

type Row = Record<string, string | number>

const getBadgeColor = (status: string) => {
  const s = status.toLowerCase()
  if (["active", "approved", "completed", "paid", "shipped", "listed"].includes(s)) return "green"
  if (["blocked", "disabled", "rejected", "failed", "canceled", "hidden"].includes(s)) return "red"
  if (["pending", "draft", "under review", "low stock"].includes(s)) return "purple"
  return "orange"
}

const formatColumn = (col: string) =>
  col.replace(/([A-Z])/g, " $1").replace(/^./, (l) => l.toUpperCase())

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
  title: string; description: string; rows: Row[]; actions?: React.ReactNode; query: string; compact?: boolean
}) => {
  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return rows
    return rows.filter((r) => Object.values(r).some((v) => String(v).toLowerCase().includes(q)))
  }, [query, rows])
  const columns = Object.keys(rows[0] || {})
  return (
    <div className="rounded-rounded border border-ui-border-base bg-white">
      <div className="flex flex-col justify-between gap-4 border-b border-ui-border-base p-5 small:flex-row small:items-center">
        <div><h2 className="text-base-semi">{title}</h2><p className="mt-1 text-small-regular text-ui-fg-subtle">{description}</p></div>
        {actions}
      </div>
      {rows.length > 0 ? (
        <div className="overflow-x-auto">
          <Table>
            <Table.Header className="border-t-0">
              <Table.Row className="text-ui-fg-subtle txt-medium-plus">
                {columns.map((col, i) => (
                  <Table.HeaderCell key={col} className={i > 1 && compact ? "hidden small:table-cell" : ""}>{formatColumn(col)}</Table.HeaderCell>
                ))}
              </Table.Row>
            </Table.Header>
            <Table.Body>
              {filtered.map((row, ri) => (
                <Table.Row key={`${title}-${ri}`}>
                  {columns.map((col, ci) => {
                    const val = row[col]
                    const isBadge = ["status", "payment_status"].includes(col)
                    return (
                      <Table.Cell key={col} className={ci > 1 && compact ? "hidden small:table-cell" : ci > 0 ? "text-ui-fg-subtle" : ""}>
                        {isBadge ? <Badge color={getBadgeColor(String(val))}>{String(val)}</Badge> : String(val)}
                      </Table.Cell>
                    )
                  })}
                </Table.Row>
              ))}
            </Table.Body>
          </Table>
        </div>
      ) : null}
      {filtered.length === 0 && (
        <div className="border-t border-ui-border-base p-6 text-small-regular text-ui-fg-subtle">
          {rows.length === 0 ? "No data available yet." : "No records match this search."}
        </div>
      )}
    </div>
  )
}

// ── Main component ──────────────────────────────────────────────────

const ManagerPanel = () => {
  const [activeView, setActiveView] = useState<ManagerView>("Dashboard")
  const [query, setQuery] = useState("")
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [dashboard, setDashboard] = useState<Record<string, unknown> | null>(null)
  const [managerProducts, setManagerProducts] = useState<Row[]>([])
  const [managerOrders, setManagerOrders] = useState<Row[]>([])
  const [shops, setShops] = useState<Record<string, unknown>[]>([])
  const [shipments, setShipments] = useState<Record<string, unknown>[]>([])
  const [income, setIncome] = useState<Record<string, unknown> | null>(null)
  const [reports, setReports] = useState<Record<string, unknown> | null>(null)

  // Create form state
  const [newShopName, setNewShopName] = useState("")
  const [newShopDesc, setNewShopDesc] = useState("")
  const [newProdName, setNewProdName] = useState("")
  const [newProdPrice, setNewProdPrice] = useState("")
  const [newProdShopId, setNewProdShopId] = useState("")
  const [shipOrderNum, setShipOrderNum] = useState("")
  const [shipCarrier, setShipCarrier] = useState("")
  const [shipTracking, setShipTracking] = useState("")
  const [actionMsg, setActionMsg] = useState("")

  const fetchData = async () => {
    setLoading(true)
    setError(null)
    try {
      const [dashResp, prodsResp, ordsResp, shopsResp, shipResp, incResp, repResp] = await Promise.all([
        getManagerPanel().catch(() => null),
        getManagerProducts().catch(() => null),
        getManagerOrders().catch(() => null),
        getManagerShops().catch(() => null),
        getManagerShipments().catch(() => null),
        getManagerIncome().catch(() => null),
        getManagerReports().catch(() => null),
      ])
      setDashboard(dashResp as Record<string, unknown> | null)
      if (prodsResp) setManagerProducts((prodsResp as { products: Row[] }).products.map((p: Record<string, unknown>) => ({
        product: p.name as string,
        category: p.category as string,
        price: `CNY ${Number(p.price).toFixed(2)}`,
        stock: p.available_item_count as number,
        status: p.status as string,
        id: p.id as string,
      })))
      if (ordsResp) setManagerOrders((ordsResp as { orders: Row[] }).orders.map((o: Record<string, unknown>) => ({
        order: o.order_number as string,
        items: o.items_count as number,
        total: `CNY ${Number(o.total).toFixed(2)}`,
        status: o.status as string,
      })))
      if (shopsResp) setShops((shopsResp as { shops: Record<string, unknown>[] }).shops)
      if (shipResp) setShipments((shipResp as { shipments: Record<string, unknown>[] }).shipments)
      if (incResp) setIncome(incResp)
      if (repResp) setReports(repResp)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load data.")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchData() }, [])

  const stats = dashboard?.stats as Record<string, number> | undefined
  const lowStock = (dashboard?.low_stock as string[]) || []
  const metrics = stats ? [
    { label: "Products", value: String(stats.products), detail: `${stats.low_stock_products} low-stock items` },
    { label: "Orders", value: String(stats.orders), detail: "Total orders" },
    { label: "Shops", value: String(stats.shops || 0), detail: "Managed shops" },
    { label: "Low stock alerts", value: String(stats.low_stock_products), detail: lowStock.slice(0, 3).join(", ") || "None" },
  ] : []

  const navItems: ManagerView[] = ["Dashboard", "My Shops", "Products", "Orders", "Shipments", "Income", "Reports", "Profile"]

  const handleCreateShop = async () => {
    if (!newShopName) return
    setActionMsg("Creating shop...")
    try {
      await createManagerShop({ name: newShopName, description: newShopDesc })
      setActionMsg("Shop created! Pending admin approval.")
      setNewShopName(""); setNewShopDesc("")
      fetchData()
    } catch (e: any) { setActionMsg(`Error: ${e.message}`) }
  }

  const handleCreateProduct = async () => {
    if (!newProdName || !newProdPrice || !newProdShopId) return
    setActionMsg("Creating product...")
    try {
      await createManagerProduct({ shop_id: newProdShopId, name: newProdName, price: parseFloat(newProdPrice), available_item_count: 10 })
      setActionMsg("Product created!")
      setNewProdName(""); setNewProdPrice(""); setNewProdShopId("")
      fetchData()
    } catch (e: any) { setActionMsg(`Error: ${e.message}`) }
  }

  const handleProcessOrder = async (orderNumber: string, newStatus: string) => {
    setActionMsg(`Updating ${orderNumber} to ${newStatus}...`)
    try {
      await updateManagerOrderStatus(orderNumber, newStatus)
      setActionMsg(`Order ${orderNumber} -> ${newStatus}`)
      fetchData()
    } catch (e: any) { setActionMsg(`Error: ${e.message}`) }
  }

  const handleCreateShipment = async () => {
    if (!shipOrderNum) return
    setActionMsg("Creating shipment...")
    try {
      await createManagerShipment(shipOrderNum, { carrier: shipCarrier, tracking_number: shipTracking })
      setActionMsg("Shipment created!")
      setShipOrderNum(""); setShipCarrier(""); setShipTracking("")
      fetchData()
    } catch (e: any) { setActionMsg(`Error: ${e.message}`) }
  }

  if (error) {
    return (
      <div className="min-h-screen bg-ui-bg-base flex items-center justify-center">
        <div className="text-center">
          <p className="text-rose-500 text-base-semi">Failed to load manager data</p>
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
            <span className="text-ui-fg-base">MANAGER PANEL</span>
            <span className="hidden text-ui-fg-muted small:inline">Shop operations</span>
          </div>
          <div className="flex items-center gap-x-3">
            <a className="hidden hover:text-ui-fg-base small:block" href="/">Customer View</a>
            <Button variant="secondary" className="h-9" onClick={() => { document.cookie = "shopping_token=; Max-Age=0"; window.location.href = "/auth/login" }}>Sign out</Button>
          </div>
        </div>
      </header>

      <div className="content-container grid grid-cols-1 gap-8 py-8 small:grid-cols-[240px_1fr]">
        <aside className="small:sticky small:top-24 small:self-start">
          <nav className="flex flex-row gap-2 overflow-x-auto border-b border-ui-border-base pb-4 small:flex-col small:overflow-visible small:border-b-0 small:pb-0">
            {navItems.map((item) => (
              <button key={item} onClick={() => { setActiveView(item); setQuery(""); setActionMsg("") }}
                className={activeView === item
                  ? "whitespace-nowrap rounded-md bg-ui-bg-subtle px-3 py-2 text-left text-small-semi text-ui-fg-base small:w-full"
                  : "whitespace-nowrap rounded-md px-3 py-2 text-left text-small-regular text-ui-fg-subtle hover:bg-ui-bg-subtle hover:text-ui-fg-base small:w-full"}
              >{item}</button>
            ))}
          </nav>
        </aside>

        <main className="flex flex-col gap-y-8">
          <section className="flex flex-col justify-between gap-4 border-b border-ui-border-base pb-8 small:flex-row small:items-end">
            <div>
              <p className="txt-xsmall-plus uppercase text-ui-fg-muted">{activeView}</p>
              <h1 className="mt-2 text-2xl-semi text-ui-fg-base">
                {activeView === "Dashboard" ? "Shop operation overview" : `${activeView} management`}
              </h1>
            </div>
            {actionMsg && <p className="text-small-regular text-ui-fg-subtle">{actionMsg}</p>}
            {activeView !== "Dashboard" && activeView !== "Profile" && (
              <div className="w-full small:w-72">
                <Input label={`Search ${activeView.toLowerCase()}`} name="manager-search" value={query} onChange={(e) => setQuery(e.target.value)} />
              </div>
            )}
          </section>

          {loading ? (
            <div className="flex items-center justify-center py-20"><Spinner /></div>
          ) : (
            <>
              {activeView === "Dashboard" && (
                <>
                  <section className="grid grid-cols-1 gap-4 small:grid-cols-2 medium:grid-cols-4">
                    {metrics.map((m) => <MetricCard key={m.label} {...m} />)}
                  </section>
                  <TableView title="Recent orders" description="Latest orders." rows={managerOrders.slice(0, 5)} query="" compact />
                </>
              )}

              {activeView === "My Shops" && (
                <div className="flex flex-col gap-6">
                  <div className="rounded-rounded border border-ui-border-base bg-white p-5">
                    <h2 className="text-base-semi mb-4">Create a new shop</h2>
                    <div className="flex flex-col gap-3 small:flex-row small:items-end">
                      <Input label="Shop name" name="shop-name" value={newShopName} onChange={(e) => setNewShopName(e.target.value)} />
                      <Input label="Description" name="shop-desc" value={newShopDesc} onChange={(e) => setNewShopDesc(e.target.value)} />
                      <Button onClick={handleCreateShop} className="h-10">Create</Button>
                    </div>
                  </div>
                  {shops.length > 0 ? (
                    <TableView title="My shops" description={`${shops.length} shop(s)`} rows={shops.map((s: any) => ({
                      shop: s.name, slug: s.slug, status: s.status, category: s.category || ""
                    }))} query={query} />
                  ) : (
                    <div className="rounded-rounded border border-ui-border-base bg-ui-bg-subtle p-12 text-center">
                      <p className="text-small-regular text-ui-fg-subtle">No shops yet. Create one above.</p>
                    </div>
                  )}
                </div>
              )}

              {activeView === "Products" && (
                <div className="flex flex-col gap-6">
                  {shops.length > 0 && (
                    <div className="rounded-rounded border border-ui-border-base bg-white p-5">
                      <h2 className="text-base-semi mb-4">Add product to shop</h2>
                      <div className="flex flex-col gap-3 small:flex-row small:items-end">
                        <select className="h-10 border rounded px-3 text-small-regular" value={newProdShopId} onChange={(e) => setNewProdShopId(e.target.value)}>
                          <option value="">Select shop</option>
                          {shops.filter((s: any) => s.status === "active").map((s: any) => <option key={s.id} value={s.id}>{s.name}</option>)}
                        </select>
                        <Input label="Product name" name="prod-name" value={newProdName} onChange={(e) => setNewProdName(e.target.value)} />
                        <Input label="Price (CNY)" name="prod-price" value={newProdPrice} onChange={(e) => setNewProdPrice(e.target.value)} />
                        <Button onClick={handleCreateProduct} className="h-10">Add</Button>
                      </div>
                    </div>
                  )}
                  <TableView title="Products" description="Your shop products." rows={managerProducts} query={query} />
                </div>
              )}

              {activeView === "Orders" && (
                <div className="flex flex-col gap-6">
                  <TableView title="Orders" description="Orders containing your products." rows={managerOrders} query={query} />
                  <div className="rounded-rounded border border-ui-border-base bg-white p-5">
                    <h2 className="text-base-semi mb-4">Process order</h2>
                    <div className="flex flex-col gap-3 small:flex-row small:items-end">
                      <Input label="Order number" name="order-num" value={shipOrderNum} onChange={(e) => setShipOrderNum(e.target.value)} />
                      <Button variant="secondary" onClick={() => handleProcessOrder(shipOrderNum, "processing")} className="h-10">Mark Processing</Button>
                      <Button variant="secondary" onClick={() => handleProcessOrder(shipOrderNum, "shipped")} className="h-10">Mark Shipped</Button>
                    </div>
                  </div>
                </div>
              )}

              {activeView === "Shipments" && (
                <div className="flex flex-col gap-6">
                  <div className="rounded-rounded border border-ui-border-base bg-white p-5">
                    <h2 className="text-base-semi mb-4">Create shipment</h2>
                    <div className="flex flex-col gap-3 small:flex-row small:items-end">
                      <Input label="Order number" name="ship-order-num" value={shipOrderNum} onChange={(e) => setShipOrderNum(e.target.value)} />
                      <Input label="Carrier" name="ship-carrier" value={shipCarrier} onChange={(e) => setShipCarrier(e.target.value)} />
                      <Input label="Tracking number" name="ship-tracking" value={shipTracking} onChange={(e) => setShipTracking(e.target.value)} />
                      <Button onClick={handleCreateShipment} className="h-10">Ship</Button>
                    </div>
                  </div>
                  {shipments.length > 0 ? (
                    <TableView title="Shipments" description="Your shipment history." rows={shipments.map((s: any) => ({
                      carrier: s.carrier || "—", tracking: s.tracking_number || "—", status: s.status, created: (s.created_at as string)?.slice(0, 10) || "—"
                    }))} query={query} />
                  ) : (
                    <div className="rounded-rounded border border-ui-border-base bg-ui-bg-subtle p-12 text-center">
                      <p className="text-small-regular text-ui-fg-subtle">No shipments yet.</p>
                    </div>
                  )}
                </div>
              )}

              {activeView === "Income" && income && (
                <div className="flex flex-col gap-6">
                  <section className="grid grid-cols-1 gap-4 small:grid-cols-3">
                    <MetricCard label="Total Income" value={`CNY ${(income.total_income as number)?.toFixed(2) || "0.00"}`} detail="Completed payments" />
                    <MetricCard label="Pending Income" value={`CNY ${(income.pending_income as number)?.toFixed(2) || "0.00"}`} detail="Awaiting payment" />
                    <MetricCard label="By Shop" value={(income.by_shop as any[])?.length?.toString() || "0"} detail="Breakdown below" />
                  </section>
                  {(income.by_shop as any[])?.length > 0 && (
                    <TableView title="Income by shop" description="" rows={(income.by_shop as any[]).map((bs: any) => ({
                      shop: bs.shop, income: `CNY ${bs.income.toFixed(2)}`
                    }))} query="" />
                  )}
                </div>
              )}

              {activeView === "Reports" && reports && (
                <div className="flex flex-col gap-6">
                  {(reports.top_products as any[])?.length > 0 && (
                    <TableView title="Top selling products" description="" rows={(reports.top_products as any[]).map((p: any) => ({
                      product: p.name, sold: p.sold
                    }))} query="" />
                  )}
                  {(reports.low_stock as any[])?.length > 0 && (
                    <TableView title="Low stock products" description="5 or fewer available." rows={(reports.low_stock as any[]).map((p: any) => ({
                      product: p.name, stock: p.stock
                    }))} query="" />
                  )}
                  {(reports.recent_orders as any[])?.length > 0 && (
                    <TableView title="Recent orders" description="" rows={(reports.recent_orders as any[]).map((o: any) => ({
                      order: o.order_number, status: o.status, date: (o.date as string)?.slice(0, 10) || "—"
                    }))} query="" />
                  )}
                </div>
              )}

              {activeView === "Profile" && (
                <InfoPanel title="Manager profile">
                  <p>Profile management is available through the account settings page.</p>
                  <Button variant="secondary" className="h-10">Edit profile</Button>
                </InfoPanel>
              )}
            </>
          )}
        </main>
      </div>
    </div>
  )
}

export default ManagerPanel
