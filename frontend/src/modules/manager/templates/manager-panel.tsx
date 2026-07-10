"use client"

import { Badge, Button, Table } from "@medusajs/ui"
import Spinner from "@modules/common/icons/spinner"
import Input from "@modules/common/components/input"
import { useEffect, useMemo, useState } from "react"
import { getManagerPanel, getManagerProducts, getManagerOrders } from "api/backend-client"

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

// ── Reusable sub-components ─────────────────────────────────────────

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

  const fetchData = async () => {
    setLoading(true)
    setError(null)
    try {
      const [dashResp, prodsResp, ordsResp] = await Promise.all([
        getManagerPanel().catch(() => null),
        getManagerProducts().catch(() => null),
        getManagerOrders().catch(() => null),
      ])
      setDashboard(dashResp as Record<string, unknown> | null)

      if (prodsResp) setManagerProducts((prodsResp as { products: Row[] }).products.map((p: Record<string, unknown>) => ({
        product: p.name as string,
        category: p.category as string,
        sku: (p.slug as string)?.toUpperCase().slice(0, 20) || "—",
        price: `CNY ${Number(p.price).toFixed(2)}`,
        stock: p.available_item_count as number,
        status: (p.available_item_count as number) === 0 ? "Hidden" : (p.available_item_count as number) <= 10 ? "Low stock" : "Listed",
      })))

      if (ordsResp) setManagerOrders((ordsResp as { orders: Row[] }).orders.map((o: Record<string, unknown>) => ({
        order: o.order_number as string,
        items: o.items_count as number,
        payment: o.payment_status as string,
        total: `CNY ${Number(o.total).toFixed(2)}`,
        date: (o.date as string)?.slice(0, 10) || "—",
        status: o.status as string,
      })))
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
              <button key={item} onClick={() => { setActiveView(item); setQuery("") }}
                className={activeView === item
                  ? "whitespace-nowrap rounded-md bg-ui-bg-subtle px-3 py-2 text-left text-small-semi text-ui-fg-base small:w-full"
                  : "whitespace-nowrap rounded-md px-3 py-2 text-left text-small-regular text-ui-fg-subtle hover:bg-ui-bg-subtle hover:text-ui-fg-base small:w-full"}
              >{item}</button>
            ))}
          </nav>
        </aside>

        <main className="flex flex-col gap-y-8">
          {/* Header */}
          <section className="flex flex-col justify-between gap-4 border-b border-ui-border-base pb-8 small:flex-row small:items-end">
            <div>
              <p className="txt-xsmall-plus uppercase text-ui-fg-muted">{activeView}</p>
              <h1 className="mt-2 text-2xl-semi text-ui-fg-base">
                {activeView === "Dashboard" ? "Shop operation overview" : `${activeView} management`}
              </h1>
              <p className="mt-2 max-w-2xl text-small-regular text-ui-fg-subtle">
                {activeView === "Dashboard" ? "Track shop health, pending work, order status, and product inventory." : `Manage ${activeView.toLowerCase()}.`}
              </p>
            </div>
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
                  <div className="grid grid-cols-1 gap-6 medium:grid-cols-[1fr_320px]">
                    <TableView title="Recent orders" description="Latest orders." rows={managerOrders.slice(0, 5)} query="" compact />
                    <div className="flex flex-col gap-4">
                      <InfoPanel title="Low stock products">
                        {lowStock.length > 0 ? lowStock.slice(0, 5).map((name) => <p key={name}>{name}</p>) : <p>All products are well-stocked.</p>}
                      </InfoPanel>
                      <InfoPanel title="Quick actions">
                        <p>Create product</p><p>Process orders</p><p>Update inventory</p>
                      </InfoPanel>
                    </div>
                  </div>
                </>
              )}
              {activeView === "Products" && (
                <TableView title="Products" description="All products in your catalog." rows={managerProducts} query={query} actions={<Button variant="secondary">Create product</Button>} />
              )}
              {activeView === "Orders" && (
                <TableView title="Orders" description="Orders for your shops." rows={managerOrders} query={query} actions={<Button variant="secondary">Process selected</Button>} />
              )}
              {activeView === "My Shops" && (
                <div className="rounded-rounded border border-ui-border-base bg-ui-bg-subtle p-12 text-center">
                  <h2 className="text-base-semi">My Shops</h2>
                  <p className="mt-2 text-small-regular text-ui-fg-subtle">Shop management will be available when the shop-owner relation is added to the database.</p>
                </div>
              )}
              {activeView === "Shipments" && (
                <div className="rounded-rounded border border-ui-border-base bg-ui-bg-subtle p-12 text-center">
                  <h2 className="text-base-semi">Shipments</h2>
                  <p className="mt-2 text-small-regular text-ui-fg-subtle">Shipment tracking will be available when the shipment model is fully integrated.</p>
                </div>
              )}
              {activeView === "Income" && (
                <div className="rounded-rounded border border-ui-border-base bg-ui-bg-subtle p-12 text-center">
                  <h2 className="text-base-semi">Income</h2>
                  <p className="mt-2 text-small-regular text-ui-fg-subtle">Revenue analytics will be derived from order payment data.</p>
                </div>
              )}
              {activeView === "Reports" && (
                <div className="rounded-rounded border border-ui-border-base bg-ui-bg-subtle p-12 text-center">
                  <h2 className="text-base-semi">Reports</h2>
                  <p className="mt-2 text-small-regular text-ui-fg-subtle">Reports and analytics coming soon.</p>
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
