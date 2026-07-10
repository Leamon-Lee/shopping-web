"use client"

import { Badge, Button, Table } from "@medusajs/ui"
import Spinner from "@modules/common/icons/spinner"
import Input from "@modules/common/components/input"
import { useEffect, useMemo, useState } from "react"
import { getAdminPanel, getAdminUsers, getAdminProducts, getAdminOrders } from "api/backend-client"

type AdminView =
  | "Dashboard" | "Users" | "Shops" | "Categories"
  | "Products" | "Orders" | "Reports" | "Settings"

type Row = Record<string, string | number>

const getBadgeColor = (status: string) => {
  const s = status.toLowerCase()
  if (["active", "approved", "completed", "paid", "admin"].includes(s)) return "green"
  if (["blocked", "disabled", "rejected", "failed", "canceled"].includes(s)) return "red"
  if (["pending", "review", "manager"].includes(s)) return "purple"
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
                    const isBadge = ["status", "role", "payment_status"].includes(col)
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

const AdminPanel = () => {
  const [activeView, setActiveView] = useState<AdminView>("Dashboard")
  const [query, setQuery] = useState("")
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [dashboard, setDashboard] = useState<Record<string, unknown> | null>(null)
  const [users, setUsers] = useState<Row[]>([])
  const [adminProducts, setAdminProducts] = useState<Row[]>([])
  const [adminOrders, setAdminOrders] = useState<Row[]>([])

  const fetchData = async () => {
    setLoading(true)
    setError(null)
    try {
      const [dashResp, usersResp, productsResp, ordersResp] = await Promise.all([
        getAdminPanel().catch(() => null),
        getAdminUsers().catch(() => null),
        getAdminProducts().catch(() => null),
        getAdminOrders().catch(() => null),
      ])
      setDashboard(dashResp as Record<string, unknown> | null)

      if (usersResp) setUsers(usersResp.users.map((u: Record<string, unknown>) => ({
        name: `${u.first_name || ""} ${u.last_name || ""}`.trim() || (u.user_name as string),
        email: u.email as string,
        role: u.role as string,
        status: u.status as string,
      })))

      if (productsResp) setAdminProducts(productsResp.products.map((p: Record<string, unknown>) => ({
        product: p.name as string,
        category: p.category as string,
        price: `CNY ${Number(p.price).toFixed(2)}`,
        stock: p.available_item_count as number,
        variants: p.variants as number,
      })))

      if (ordersResp) setAdminOrders(ordersResp.orders.map((o: Record<string, unknown>) => ({
        order: o.order_number as string,
        items: o.items_count as number,
        payment: o.payment_status as string,
        total: `CNY ${Number(o.total).toFixed(2)}`,
        status: o.status as string,
        date: (o.date as string)?.slice(0, 10) || "—",
      })))
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load data.")
    } finally {
      setLoading(false)
    }
  }

  // Fetch on mount
  useEffect(() => { fetchData() }, [])

  const stats = dashboard?.stats as Record<string, number> | undefined
  const metrics = stats ? [
    { label: "Products", value: String(stats.products), detail: "Platform catalog" },
    { label: "Categories", value: String(stats.categories), detail: "Product categories" },
    { label: "Orders", value: String(stats.orders), detail: "All orders" },
    { label: "Users", value: String(stats.total_users), detail: `${stats.customers} customers, ${stats.managers} managers, ${stats.admins} admins` },
  ] : []

  const navItems: AdminView[] = ["Dashboard", "Users", "Shops", "Categories", "Products", "Orders", "Reports", "Settings"]

  if (error) {
    return (
      <div className="min-h-screen bg-ui-bg-base flex items-center justify-center">
        <div className="text-center">
          <p className="text-rose-500 text-base-semi">Failed to load admin data</p>
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
            <span className="text-ui-fg-base">ADMIN PANEL</span>
            <span className="hidden text-ui-fg-muted small:inline">Platform operations</span>
          </div>
          <div className="flex items-center gap-x-3">
            <a className="hidden hover:text-ui-fg-base small:block" href="/">Store</a>
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
                {activeView === "Dashboard" ? "Platform overview" : `${activeView} management`}
              </h1>
              <p className="mt-2 max-w-2xl text-small-regular text-ui-fg-subtle">
                {activeView === "Dashboard" ? "Review shops, maintain platform categories, and monitor operational activity." : `Manage platform ${activeView.toLowerCase()}.`}
              </p>
            </div>
            {activeView !== "Dashboard" && (
              <div className="w-full small:w-72">
                <Input label={`Search ${activeView.toLowerCase()}`} name="admin-search" value={query} onChange={(e) => setQuery(e.target.value)} />
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
                  <TableView title="Recent orders" description="Latest platform orders." rows={adminOrders.slice(0, 5)} query="" compact />
                </>
              )}
              {activeView === "Users" && (
                <TableView title="Platform users" description="All registered accounts." rows={users} query={query} />
              )}
              {activeView === "Products" && (
                <TableView title="Platform products" description="All products across shops." rows={adminProducts} query={query} />
              )}
              {activeView === "Orders" && (
                <TableView title="Platform orders" description="All orders across the platform." rows={adminOrders} query={query} />
              )}
              {activeView === "Shops" && (
                <div className="rounded-rounded border border-ui-border-base bg-ui-bg-subtle p-12 text-center">
                  <h2 className="text-base-semi">Shop management</h2>
                  <p className="mt-2 text-small-regular text-ui-fg-subtle">Shop approval and management will be available when the shop model is fully integrated.</p>
                </div>
              )}
              {activeView === "Categories" && (
                <div className="rounded-rounded border border-ui-border-base bg-ui-bg-subtle p-12 text-center">
                  <h2 className="text-base-semi">Category management</h2>
                  <p className="mt-2 text-small-regular text-ui-fg-subtle">Category CRUD operations will be available when the admin category API is implemented.</p>
                </div>
              )}
              {activeView === "Reports" && (
                <div className="rounded-rounded border border-ui-border-base bg-ui-bg-subtle p-12 text-center">
                  <h2 className="text-base-semi">Reports</h2>
                  <p className="mt-2 text-small-regular text-ui-fg-subtle">Analytics and reports will be built on the order and product data pipeline.</p>
                </div>
              )}
              {activeView === "Settings" && (
                <div className="rounded-rounded border border-ui-border-base bg-ui-bg-subtle p-12 text-center">
                  <h2 className="text-base-semi">Platform settings</h2>
                  <p className="mt-2 text-small-regular text-ui-fg-subtle">Settings management is coming soon.</p>
                </div>
              )}
            </>
          )}
        </main>
      </div>
    </div>
  )
}

export default AdminPanel
