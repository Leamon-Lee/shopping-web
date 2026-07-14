"use client"

import { Badge, Button, Table } from "@medusajs/ui"
import Spinner from "@modules/common/icons/spinner"
import Input from "@modules/common/components/input"
import { useEffect, useMemo, useState } from "react"
import {
  getAdminPanel, getAdminUsers, getAdminProducts, getAdminOrders,
  getAdminShops, approveShop, updateUserStatus, updateUserRole,
  updateProductStatus, getAdminCategories, createAdminCategory,
  updateAdminCategory, deleteAdminCategory,
} from "api/backend-client"

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
  const [users, setUsers] = useState<any[]>([])
  const [adminProducts, setAdminProducts] = useState<Row[]>([])
  const [adminOrders, setAdminOrders] = useState<Row[]>([])
  const [shops, setShops] = useState<any[]>([])
  const [categories, setCategories] = useState<any[]>([])
  const [actionMsg, setActionMsg] = useState("")

  // Form state
  const [newCatName, setNewCatName] = useState("")
  const [newCatDesc, setNewCatDesc] = useState("")
  const [editCatId, setEditCatId] = useState("")
  const [editCatName, setEditCatName] = useState("")
  const [editCatDesc, setEditCatDesc] = useState("")

  const fetchData = async () => {
    setLoading(true)
    setError(null)
    try {
      const results = await Promise.all([
        getAdminPanel().catch(() => null),
        getAdminUsers().catch(() => null),
        getAdminProducts().catch(() => null),
        getAdminOrders().catch(() => null),
        getAdminShops().catch(() => null),
        getAdminCategories().catch(() => null),
      ])
      setDashboard(results[0] as any)
      if (results[1]) setUsers((results[1] as any).users)
      if (results[2]) setAdminProducts((results[2] as any).products.map((p: any) => ({
        product: p.name, category: p.category, price: `CNY ${Number(p.price).toFixed(2)}`,
        stock: p.available_item_count, status: p.status || "active", id: p.id,
      })))
      if (results[3]) setAdminOrders((results[3] as any).orders.map((o: any) => ({
        order: o.order_number, items: o.items_count, payment: o.payment_status,
        total: `CNY ${Number(o.total).toFixed(2)}`, status: o.status,
      })))
      if (results[4]) setShops((results[4] as any).shops)
      if (results[5]) setCategories((results[5] as any).categories)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load data.")
    } finally { setLoading(false) }
  }

  useEffect(() => { fetchData() }, [])

  const stats = dashboard?.stats as Record<string, number> | undefined
  const metrics = stats ? [
    { label: "Products", value: String(stats.products), detail: "Platform catalog" },
    { label: "Categories", value: String(stats.categories), detail: "Product categories" },
    { label: "Orders", value: String(stats.orders), detail: "All orders" },
    { label: "Users", value: String(stats.total_users), detail: `${stats.customers} customers, ${stats.managers} managers, ${stats.admins} admins` },
  ] : []

  const navItems: AdminView[] = ["Dashboard", "Users", "Shops", "Categories", "Products", "Orders", "Reports", "Settings"]

  // Actions
  const doApprove = async (shopId: string, status: string) => {
    setActionMsg(`Updating shop...`)
    try { await approveShop(shopId, status); fetchData(); setActionMsg(`Shop ${status}`) }
    catch (e: any) { setActionMsg(`Error: ${e.message}`) }
  }
  const doUserStatus = async (userId: string, status: string) => {
    try { await updateUserStatus(userId, status); fetchData(); setActionMsg(`User ${status}`) }
    catch (e: any) { setActionMsg(`Error: ${e.message}`) }
  }
  const doUserRole = async (userId: string, role: string) => {
    try { await updateUserRole(userId, role); fetchData(); setActionMsg(`User role -> ${role}`) }
    catch (e: any) { setActionMsg(`Error: ${e.message}`) }
  }
  const doProductStatus = async (productId: string, status: string) => {
    try { await updateProductStatus(productId, status); fetchData(); setActionMsg(`Product ${status}`) }
    catch (e: any) { setActionMsg(`Error: ${e.message}`) }
  }
  const doCreateCategory = async () => {
    if (!newCatName) return
    try { await createAdminCategory({ name: newCatName, description: newCatDesc }); setNewCatName(""); setNewCatDesc(""); fetchData(); setActionMsg("Category created") }
    catch (e: any) { setActionMsg(`Error: ${e.message}`) }
  }
  const doUpdateCategory = async () => {
    if (!editCatId || !editCatName) return
    try { await updateAdminCategory(editCatId, { name: editCatName, description: editCatDesc }); fetchData(); setActionMsg("Category updated") }
    catch (e: any) { setActionMsg(`Error: ${e.message}`) }
  }
  const doDeleteCategory = async (catId: string) => {
    try { await deleteAdminCategory(catId); fetchData(); setActionMsg("Category deleted") }
    catch (e: any) { setActionMsg(`Error: ${e.message}`) }
  }

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
          <section className="flex flex-col justify-between gap-4 border-b border-ui-border-base pb-8 small:flex-row small:items-end">
            <div>
              <p className="txt-xsmall-plus uppercase text-ui-fg-muted">{activeView}</p>
              <h1 className="mt-2 text-2xl-semi text-ui-fg-base">
                {activeView === "Dashboard" ? "Platform overview" : `${activeView} management`}
              </h1>
            </div>
            {actionMsg && <p className="text-small-regular text-ui-fg-subtle">{actionMsg}</p>}
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

              {activeView === "Users" && users.length > 0 && (
                <div className="flex flex-col gap-6">
                  {users.map((u: any) => (
                    <div key={u.id} className="flex items-center justify-between rounded-rounded border border-ui-border-base bg-white p-4">
                      <div>
                        <p className="text-base-regular">{u.first_name} {u.last_name} ({u.user_name})</p>
                        <p className="text-small-regular text-ui-fg-subtle">{u.email} — <Badge color={getBadgeColor(u.role)}>{u.role}</Badge> <Badge color={getBadgeColor(u.status)}>{u.status}</Badge></p>
                      </div>
                      <div className="flex gap-2">
                        <Button variant="secondary" className="h-8 text-small-regular" onClick={() => doUserStatus(u.id, "active")}>Active</Button>
                        <Button variant="secondary" className="h-8 text-small-regular" onClick={() => doUserStatus(u.id, "blocked")}>Block</Button>
                        <Button variant="secondary" className="h-8 text-small-regular" onClick={() => doUserRole(u.id, "manager")}>Make Manager</Button>
                        <Button variant="secondary" className="h-8 text-small-regular" onClick={() => doUserRole(u.id, "admin")}>Make Admin</Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {activeView === "Shops" && (
                <div className="flex flex-col gap-4">
                  {shops.length > 0 ? shops.map((s: any) => (
                    <div key={s.id} className="flex items-center justify-between rounded-rounded border border-ui-border-base bg-white p-4">
                      <div>
                        <p className="text-base-regular">{s.name}</p>
                        <p className="text-small-regular text-ui-fg-subtle">{s.slug} — owner: {s.owner_email} — <Badge color={getBadgeColor(s.status)}>{s.status}</Badge></p>
                      </div>
                      <div className="flex gap-2">
                        {s.status === "pending" && (
                          <>
                            <Button variant="secondary" className="h-8" onClick={() => doApprove(s.id, "active")}>Approve</Button>
                            <Button variant="secondary" className="h-8" onClick={() => doApprove(s.id, "rejected")}>Reject</Button>
                          </>
                        )}
                      </div>
                    </div>
                  )) : (
                    <div className="rounded-rounded border border-ui-border-base bg-ui-bg-subtle p-12 text-center">
                      <p className="text-small-regular text-ui-fg-subtle">No shops registered.</p>
                    </div>
                  )}
                </div>
              )}

              {activeView === "Categories" && (
                <div className="flex flex-col gap-6">
                  <div className="rounded-rounded border border-ui-border-base bg-white p-5">
                    <h2 className="text-base-semi mb-4">Create category</h2>
                    <div className="flex flex-col gap-3 small:flex-row small:items-end">
                      <Input label="Name" name="cat-name" value={newCatName} onChange={(e) => setNewCatName(e.target.value)} />
                      <Input label="Description" name="cat-desc" value={newCatDesc} onChange={(e) => setNewCatDesc(e.target.value)} />
                      <Button onClick={doCreateCategory} className="h-10">Create</Button>
                    </div>
                  </div>
                  {categories.length > 0 ? categories.map((c: any) => (
                    <div key={c.id} className="flex items-center justify-between rounded-rounded border border-ui-border-base bg-white p-4">
                      <div>
                        <p className="text-base-regular">{c.name}</p>
                        <p className="text-small-regular text-ui-fg-subtle">{c.description}</p>
                      </div>
                      <div className="flex gap-2">
                        <Button variant="secondary" className="h-8" onClick={() => { setEditCatId(c.id); setEditCatName(c.name); setEditCatDesc(c.description) }}>Edit</Button>
                        <Button variant="secondary" className="h-8" onClick={() => doDeleteCategory(c.id)}>Delete</Button>
                      </div>
                    </div>
                  )) : (
                    <div className="rounded-rounded border border-ui-border-base bg-ui-bg-subtle p-12 text-center">
                      <p className="text-small-regular text-ui-fg-subtle">No categories yet.</p>
                    </div>
                  )}
                  {editCatId && (
                    <div className="rounded-rounded border border-ui-border-base bg-white p-5">
                      <h2 className="text-base-semi mb-4">Edit category</h2>
                      <div className="flex flex-col gap-3 small:flex-row small:items-end">
                        <Input label="Name" name="edit-cat-name" value={editCatName} onChange={(e) => setEditCatName(e.target.value)} />
                        <Input label="Description" name="edit-cat-desc" value={editCatDesc} onChange={(e) => setEditCatDesc(e.target.value)} />
                        <Button onClick={doUpdateCategory} className="h-10">Update</Button>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {activeView === "Products" && (
                <div className="flex flex-col gap-4">
                  {adminProducts.length > 0 ? adminProducts.map((p: any) => (
                    <div key={p.id || p.product} className="flex items-center justify-between rounded-rounded border border-ui-border-base bg-white p-4">
                      <div>
                        <p className="text-base-regular">{p.product}</p>
                        <p className="text-small-regular text-ui-fg-subtle">{p.category} — {p.price} — Stock: {p.stock} — <Badge color={getBadgeColor(p.status)}>{p.status}</Badge></p>
                      </div>
                      <div className="flex gap-2">
                        <Button variant="secondary" className="h-8" onClick={() => doProductStatus(p.id, "active")}>Active</Button>
                        <Button variant="secondary" className="h-8" onClick={() => doProductStatus(p.id, "hidden")}>Hidden</Button>
                        <Button variant="secondary" className="h-8" onClick={() => doProductStatus(p.id, "rejected")}>Reject</Button>
                      </div>
                    </div>
                  )) : (
                    <div className="rounded-rounded border border-ui-border-base bg-ui-bg-subtle p-12 text-center">
                      <p className="text-small-regular text-ui-fg-subtle">No products in catalog.</p>
                    </div>
                  )}
                </div>
              )}

              {activeView === "Orders" && (
                <TableView title="Platform orders" description="" rows={adminOrders} query={query} />
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
