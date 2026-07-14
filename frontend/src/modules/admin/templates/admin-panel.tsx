"use client"

import { Badge, Button, Table } from "@medusajs/ui"
import Spinner from "@modules/common/icons/spinner"
import Input from "@modules/common/components/input"
import { useEffect, useMemo, useRef, useState } from "react"
import { getAdminUsers, getAdminProducts, getAdminOrders, getAdminShops, approveShop, getAdminCategoryPreferences, getAdminDailyRankings } from "api/backend-client"
import { signout } from "@lib/data/customer"
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts"

type AdminView =
  | "Dashboard" | "Users" | "Shops" | "Categories"
  | "Products" | "Orders" | "Reports" | "Settings"
  | "Customer Preferences" | "Daily Rankings"

type Row = Record<string, string | number>

const getBadgeColor = (status: string) => {
  const s = status.toLowerCase()
  if (["active", "approved", "completed", "paid", "admin"].includes(s)) return "green"
  if (["blocked", "disabled", "rejected", "failed", "canceled"].includes(s)) return "red"
  if (["pending", "pending_deletion", "review", "manager"].includes(s)) return "purple"
  return "orange"
}

const COLORS = ["#3b82f6", "#ef4444", "#22c55e", "#f59e0b", "#8b5cf6", "#ec4899", "#06b6d4", "#f97316", "#84cc16", "#14b8a6", "#6366f1"]

const formatColumn = (col: string) =>
  col.replace(/([A-Z])/g, " $1").replace(/^./, (l) => l.toUpperCase())

// ── Reusable sub-components ─────────────────────────────────────────

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
  const [users, setUsers] = useState<Row[]>([])
  const [adminProducts, setAdminProducts] = useState<Row[]>([])
  const [adminOrders, setAdminOrders] = useState<Row[]>([])
  const [adminShops, setAdminShops] = useState<Row[]>([])
  const rawShopsRef = useRef<Record<string, unknown>[]>([])
  const [prefStartDate, setPrefStartDate] = useState("")
  const [prefEndDate, setPrefEndDate] = useState("")
  const [prefData, setPrefData] = useState<Array<{ category_name: string; order_count: number; sales_amount: number }>>([])
  const [prefLoading, setPrefLoading] = useState(false)
  const [rankDate, setRankDate] = useState("")
  const [rankData, setRankData] = useState<{ date: string; shop_rankings: any[]; product_rankings: any[] } | null>(null)
  const [rankLoading, setRankLoading] = useState(false)

  const fetchData = async () => {
    setLoading(true)
    setError(null)
    try {
      const [usersResp, shopsResp] = await Promise.all([
        getAdminUsers().catch(() => null),
        getAdminShops().catch(() => null),
      ])

      if (usersResp) setUsers(usersResp.users.map((u: Record<string, unknown>) => ({
        name: `${u.first_name || ""} ${u.last_name || ""}`.trim() || (u.user_name as string),
        email: u.email as string,
        role: u.role as string,
        status: u.status as string,
      })))

      if (shopsResp) {
        rawShopsRef.current = shopsResp.shops as Record<string, unknown>[]
        setAdminShops(rawShopsRef.current.map((s) => ({
          name: s.name as string,
          slug: s.slug as string,
          owner: (s.owner_email as string) || "—",
          status: s.status as string,
          category: (s.category as string) || "—",
        })))
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load data.")
    } finally {
      setLoading(false)
    }
  }

  // Fetch on mount
  useEffect(() => { fetchData() }, [])

  const fetchCategoryPreferences = async () => {
    if (!prefStartDate || !prefEndDate) return
    setPrefLoading(true)
    try {
      const resp = await getAdminCategoryPreferences({ start_date: prefStartDate, end_date: prefEndDate })
      setPrefData(resp.data)
    } catch { /* ignore */ }
    finally { setPrefLoading(false) }
  }

  const fetchDailyRankings = async () => {
    if (!rankDate) return
    setRankLoading(true)
    try {
      const resp = await getAdminDailyRankings({ date: rankDate })
      setRankData(resp)
    } catch { /* ignore */ }
    finally { setRankLoading(false) }
  }

  // Set default dates
  useEffect(() => {
    if (activeView === "Customer Preferences" && !prefStartDate) {
      const today = new Date()
      const weekAgo = new Date(today)
      weekAgo.setDate(weekAgo.getDate() - 7)
      setPrefStartDate(weekAgo.toISOString().slice(0, 10))
      setPrefEndDate(today.toISOString().slice(0, 10))
    }
    if (activeView === "Daily Rankings" && !rankDate) {
      setRankDate(new Date().toISOString().slice(0, 10))
    }
  }, [activeView])

  const fetchAdminShops = async () => {
    try {
      const resp = await getAdminShops()
      rawShopsRef.current = resp.shops as Record<string, unknown>[]
      setAdminShops(rawShopsRef.current.map((s) => ({
        name: s.name as string,
        slug: s.slug as string,
        owner: (s.owner_email as string) || "—",
        status: s.status as string,
        category: (s.category as string) || "—",
      })))
    } catch { /* ignore */ }
  }

  const handleApprove = async (shopId: string, status: "active" | "rejected") => {
    try {
      await approveShop(shopId, status)
      fetchAdminShops()
    } catch { /* ignore */ }
  }

  useEffect(() => {
    if (activeView === "Products" && adminProducts.length === 0) {
      getAdminProducts().then((resp) => {
        if (resp) setAdminProducts(resp.products.map((p: Record<string, unknown>) => ({
          product: p.name as string, category: p.category as string,
          price: `CNY ${Number(p.price).toFixed(2)}`, stock: p.available_item_count as number, variants: p.variants as number,
        })))
      }).catch(() => {})
    }
    if (activeView === "Orders" && adminOrders.length === 0) {
      getAdminOrders().then((resp) => {
        if (resp) setAdminOrders(resp.orders.map((o: Record<string, unknown>) => ({
          order: o.order_number as string, items: o.items_count as number, payment: o.payment_status as string,
          total: `CNY ${Number(o.total).toFixed(2)}`, status: o.status as string,
          date: (o.date as string)?.slice(0, 10) || "—",
        })))
      }).catch(() => {})
    }
  }, [activeView, adminProducts.length, adminOrders.length])

  const navItems: AdminView[] = ["Dashboard", "Customer Preferences", "Daily Rankings", "Users", "Shops"]

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
      <header className="sticky top-0 z-40 border-b border-ui-border-base bg-gray-200">
        <div className="content-container flex h-16 items-center justify-between txt-xsmall-plus text-ui-fg-subtle">
          <div className="flex items-center gap-x-4">
            <span className="text-ui-fg-base">ADMIN PANEL</span>
            <span className="hidden text-ui-fg-muted small:inline">Platform operations</span>
          </div>
          <div className="flex items-center gap-x-3">
            <a className="hidden hover:text-ui-fg-base small:block" href="/hall">Hall</a>
            <Button variant="secondary" className="h-9" onClick={() => signout()}>Sign out</Button>
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
                {activeView === "Dashboard" ? "Review shop applications, manage shops, and monitor platform users." : `Manage platform ${activeView.toLowerCase()}.`}
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
                <div className="flex flex-col gap-y-6">
                  {/* Pending shop approvals */}
                  {rawShopsRef.current.filter((s) => s.status === "pending" || s.status === "pending_deletion").length > 0 && (
                    <div className="rounded-rounded border border-amber-300 bg-amber-50 p-5">
                      <h3 className="text-base-semi text-amber-800">
                        Pending shop actions ({rawShopsRef.current.filter((s) => s.status === "pending" || s.status === "pending_deletion").length})
                      </h3>
                      <div className="mt-3 flex flex-col gap-3">
                        {rawShopsRef.current.filter((s) => s.status === "pending" || s.status === "pending_deletion").map((shop, i) => (
                          <div key={i} className="flex items-center justify-between border-b border-amber-200 pb-3 last:border-b-0 last:pb-0">
                            <div>
                              <p className="text-base-regular font-medium">{shop.name as string}</p>
                              <p className="text-small-regular text-ui-fg-muted">
                                {shop.status === "pending_deletion" ? "Delete request — " : ""}
                                Owner: {shop.owner_email as string || "—"} | Category: {shop.category as string || "—"}
                              </p>
                            </div>
                            <div className="flex gap-2">
                              {shop.status === "pending_deletion" ? (
                                <>
                                  <Button variant="secondary" className="h-8 text-small-regular text-rose-600" onClick={() => handleApprove(shop.id as string, "deleted")}>Confirm delete</Button>
                                  <Button variant="secondary" className="h-8 text-small-regular" onClick={() => handleApprove(shop.id as string, "active")}>Reject</Button>
                                </>
                              ) : (
                                <>
                                  <Button variant="secondary" className="h-8 text-small-regular text-green-600" onClick={() => handleApprove(shop.id as string, "active")}>Approve</Button>
                                  <Button variant="secondary" className="h-8 text-small-regular text-rose-600" onClick={() => handleApprove(shop.id as string, "rejected")}>Reject</Button>
                                </>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* All shops */}
                  <TableView title="All shops" description={`${adminShops.length} shops on the platform.`} rows={adminShops} query="" />

                  {/* Users by role in 3 columns */}
                  <div className="rounded-rounded border border-ui-border-base bg-white p-5">
                    <h2 className="text-base-semi">Platform users</h2>
                    <p className="mt-1 text-small-regular text-ui-fg-subtle">{users.length} registered accounts grouped by role.</p>
                    <div className="mt-4 grid grid-cols-1 gap-4 medium:grid-cols-3">
                      {(["customer", "manager", "admin"] as const).map((role) => {
                        const roleUsers = users.filter((u) => u.role === role)
                        return (
                          <div key={role} className="rounded-rounded border border-ui-border-base bg-ui-bg-subtle p-4">
                            <h3 className="text-small-semi capitalize text-ui-fg-base flex items-center gap-2">
                              {role}s <Badge color={getBadgeColor(role)}>{roleUsers.length}</Badge>
                            </h3>
                            <div className="mt-3 flex flex-col gap-1">
                              {roleUsers.length === 0 ? (
                                <p className="text-small-regular text-ui-fg-muted">None</p>
                              ) : (
                                roleUsers.map((u, i) => (
                                  <div key={i} className="flex items-center justify-between py-1 border-b border-ui-border-base last:border-b-0">
                                    <div>
                                      <p className="text-small-regular font-medium">{u.name}</p>
                                      <p className="text-xs text-ui-fg-muted">{u.email}</p>
                                    </div>
                                    <Badge color={getBadgeColor(String(u.status))}>{String(u.status)}</Badge>
                                  </div>
                                ))
                              )}
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  </div>
                </div>
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
                <div className="flex flex-col gap-y-6">
                  <TableView
                    title="Shop management"
                    description="Review and approve shops. Only approved shops appear in the marketplace."
                    rows={adminShops}
                    query={query}
                    actions={undefined}
                  />
                  {adminShops.filter((s) => s.status === "pending").length > 0 && (
                    <div className="rounded-rounded border border-ui-border-base bg-white p-5">
                      <h3 className="text-base-semi mb-4">
                        Pending approval ({adminShops.filter((s) => s.status === "pending").length})
                      </h3>
                      <div className="flex flex-col gap-3">
                        {rawShopsRef.current.filter((s) => s.status === "pending").map((shop, i) => (
                          <div key={i} className="flex items-center justify-between border-b border-ui-border-base pb-3 last:border-b-0 last:pb-0">
                            <div>
                              <p className="text-base-regular font-medium">{shop.name as string}</p>
                              <p className="text-small-regular text-ui-fg-muted">
                                Owner: {shop.owner_email as string || "—"} | Category: {shop.category as string || "—"}
                              </p>
                            </div>
                            <div className="flex gap-2">
                              <Button variant="secondary" className="h-8 text-small-regular text-green-600" onClick={() => handleApprove(shop.id as string, "active")}>Approve</Button>
                              <Button variant="secondary" className="h-8 text-small-regular text-rose-600" onClick={() => handleApprove(shop.id as string, "rejected")}>Reject</Button>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
              {activeView === "Customer Preferences" && (
                <div className="flex flex-col gap-y-6">
                  <div className="flex items-end gap-4 flex-wrap">
                    <div className="flex flex-col gap-1">
                      <label className="text-small-regular text-ui-fg-subtle">Start date</label>
                      <input type="date" className="h-10 rounded-rounded border border-ui-border-base bg-ui-bg-field px-3 text-small-regular"
                        value={prefStartDate} onChange={(e) => setPrefStartDate(e.target.value)} />
                    </div>
                    <div className="flex flex-col gap-1">
                      <label className="text-small-regular text-ui-fg-subtle">End date</label>
                      <input type="date" className="h-10 rounded-rounded border border-ui-border-base bg-ui-bg-field px-3 text-small-regular"
                        value={prefEndDate} onChange={(e) => setPrefEndDate(e.target.value)} />
                    </div>
                    <Button variant="secondary" onClick={fetchCategoryPreferences} isLoading={prefLoading}>Query</Button>
                  </div>
                  {prefData.length > 0 ? (
                    <div className="rounded-rounded border border-ui-border-base bg-white p-5">
                      <h2 className="text-base-semi mb-4">Category Order Distribution</h2>
                      <div className="grid grid-cols-1 gap-6">
                        <ResponsiveContainer width="100%" height={400}>
                          <PieChart>
                            <Pie data={prefData} dataKey="order_count" nameKey="category_name" cx="50%" cy="50%"
                              outerRadius={140}>
                              {prefData.map((_, i) => (
                                <Cell key={i} fill={COLORS[i % COLORS.length]} />
                              ))}
                            </Pie>
                            <Tooltip formatter={(value, _name, props) => [`${value} orders`, (props?.payload as any)?.category_name]} />
                            <Legend />
                          </PieChart>
                        </ResponsiveContainer>
                      </div>
                    </div>
                  ) : prefStartDate && prefEndDate && !prefLoading ? (
                    <div className="rounded-rounded border border-ui-border-base bg-ui-bg-subtle p-12 text-center">
                      <p className="text-small-regular text-ui-fg-muted">No order data found for this date range.</p>
                    </div>
                  ) : null}
                </div>
              )}
              {activeView === "Daily Rankings" && (
                <div className="flex flex-col gap-y-6">
                  <div className="flex items-end gap-4 flex-wrap">
                    <div className="flex flex-col gap-1">
                      <label className="text-small-regular text-ui-fg-subtle">Date</label>
                      <input type="date" className="h-10 rounded-rounded border border-ui-border-base bg-ui-bg-field px-3 text-small-regular"
                        value={rankDate} onChange={(e) => setRankDate(e.target.value)} />
                    </div>
                    <Button variant="secondary" onClick={fetchDailyRankings} isLoading={rankLoading}>Query</Button>
                  </div>
                  {rankData ? (
                    <>
                      <div className="rounded-rounded border border-ui-border-base bg-white p-5">
                        <h2 className="text-base-semi mb-4">Shop Order Rankings — {rankData.date}</h2>
                        {rankData.shop_rankings.length > 0 ? (
                          <ResponsiveContainer width="100%" height={350}>
                            <BarChart data={rankData.shop_rankings} layout="vertical" margin={{ top: 5, right: 30, left: 120, bottom: 5 }}>
                              <CartesianGrid strokeDasharray="3 3" />
                              <XAxis type="number" />
                              <YAxis type="category" dataKey="shop_name" hide />
                              <Tooltip formatter={(_v, _n, props) => {
                                const p = props?.payload as any
                                return [`${p?.order_count} orders, CNY ${Number(p?.sales_amount).toFixed(2)}`, p?.shop_name]
                              }} />
                              <Bar dataKey="order_count" fill="#3b82f6" name="Orders" />
                            </BarChart>
                          </ResponsiveContainer>
                        ) : (
                          <p className="text-small-regular text-ui-fg-muted py-8 text-center">No shop orders on this date.</p>
                        )}
                      </div>
                      <div className="rounded-rounded border border-ui-border-base bg-white p-5">
                        <h2 className="text-base-semi mb-4">Product Order Rankings — {rankData.date}</h2>
                        {rankData.product_rankings.length > 0 ? (
                          <ResponsiveContainer width="100%" height={350}>
                            <BarChart data={rankData.product_rankings} layout="vertical" margin={{ top: 5, right: 30, left: 180, bottom: 5 }}>
                              <CartesianGrid strokeDasharray="3 3" />
                              <XAxis type="number" />
                              <YAxis type="category" dataKey="product_name" hide />
                              <Tooltip formatter={(_v, _n, props) => {
                                const p = props?.payload as any
                                return [`${p?.order_count} orders, CNY ${Number(p?.sales_amount).toFixed(2)}`, p?.product_name]
                              }} />
                              <Bar dataKey="order_count" fill="#a855f7" name="Orders" />
                            </BarChart>
                          </ResponsiveContainer>
                        ) : (
                          <p className="text-small-regular text-ui-fg-muted py-8 text-center">No product orders on this date.</p>
                        )}
                      </div>
                    </>
                  ) : rankDate && !rankLoading ? (
                    <div className="rounded-rounded border border-ui-border-base bg-ui-bg-subtle p-12 text-center">
                      <p className="text-small-regular text-ui-fg-muted">Select a date and click Query to see rankings.</p>
                    </div>
                  ) : null}
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
