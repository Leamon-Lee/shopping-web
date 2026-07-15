"use client"

import { Badge, Button, Table } from "@medusajs/ui"
import Spinner from "@modules/common/icons/spinner"
import Input from "@modules/common/components/input"
import { useEffect, useMemo, useRef, useState } from "react"
import { getManagerPanel, getManagerProducts, getManagerOrders, getManagerShops, createManagerShop, createProduct, updateProduct, deleteProduct, requestDeleteShop, getManagerShopAnalytics, getManagerDashboardAnalytics, getManagerAnalyticsCategories } from "api/backend-client"
import { signout } from "@lib/data/customer"
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts"

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

const TableView = ({ title, description, rows, actions, query, compact, rowActions }: {
  title: string; description: string; rows: Row[]; actions?: React.ReactNode; query: string; compact?: boolean
  rowActions?: (row: Row, index: number) => React.ReactNode
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
                {rowActions && <Table.HeaderCell>Actions</Table.HeaderCell>}
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
                  {rowActions && <Table.Cell>{rowActions(row, ri)}</Table.Cell>}
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
  const [managerShops, setManagerShops] = useState<Row[]>([])
  const [showCreateShop, setShowCreateShop] = useState(false)
  const [shopForm, setShopForm] = useState({ name: "", description: "", category: "" })
  const [shopLoading, setShopLoading] = useState(false)
  const rawManagerShopsRef = useRef<Record<string, unknown>[]>([])
  const [productForm, setProductForm] = useState({ name: "", description: "", price: 0, stock: 0, categoryName: "", shopId: "" })
  const [productLoading, setProductLoading] = useState(false)
  const [editingProduct, setEditingProduct] = useState<Record<string, unknown> | null>(null)
  const [editForm, setEditForm] = useState({ name: "", description: "", price: 0, stock: 0, categoryName: "" })
  const [imageFiles, setImageFiles] = useState<FileList | null>(null)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [editMode, setEditMode] = useState(false)
  const [shopFilter, setShopFilter] = useState("all")
  const [createError, setCreateError] = useState("")
  const [editFileNames, setEditFileNames] = useState<Record<number, string>>({})
  const [shopAnalytics, setShopAnalytics] = useState<any[]>([])
  const [analyticsShopFilter, setAnalyticsShopFilter] = useState("all")
  const [dashboardAnalytics, setDashboardAnalytics] = useState<Record<string, any> | null>(null)
  const [dashboardCategoryFilter, setDashboardCategoryFilter] = useState("all")
  const [analyticsCategories, setAnalyticsCategories] = useState<Array<{ id: string; name: string }>>([])

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

      if (prodsResp) mapProducts((prodsResp as { products: any[] }).products)

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

  const fetchShops = async () => {
    setShopLoading(true)
    try {
      const resp = await getManagerShops()
      const shops = resp.shops as Record<string, unknown>[]
      rawManagerShopsRef.current = shops
      setManagerShops(shops.map((s) => ({
        name: s.name as string,
        slug: s.slug as string,
        status: s.status as string,
        category: (s.category as string) || "—",
      })))
    } catch { /* ignore */ }
    finally { setShopLoading(false) }
  }

  const handleCreateShop = async () => {
    if (!shopForm.name.trim()) return
    try {
      await createManagerShop({ name: shopForm.name, description: shopForm.description, category: shopForm.category || undefined })
      setShopForm({ name: "", description: "", category: "" })
      setShowCreateShop(false)
      fetchShops()
    } catch { /* ignore */ }
  }

  useEffect(() => { fetchShops() }, [])

  const fetchShopAnalytics = async (shopId?: string) => {
    try {
      const resp = await getManagerShopAnalytics({ days: 7, shop_id: shopId || undefined })
      setShopAnalytics(resp.data)
    } catch { /* ignore */ }
  }

  const fetchDashboardAnalytics = async (categoryId?: string) => {
    try {
      const resp = await getManagerDashboardAnalytics({ category_id: categoryId || undefined })
      setDashboardAnalytics(resp)
    } catch { /* ignore */ }
  }

  useEffect(() => {
    getManagerAnalyticsCategories().then(r => setAnalyticsCategories(r.categories)).catch(() => {})
  }, [])

  useEffect(() => {
    if (activeView === "My Shops") {
      fetchShopAnalytics(analyticsShopFilter === "all" ? undefined : analyticsShopFilter)
    }
    if (activeView === "Dashboard") {
      fetchDashboardAnalytics(dashboardCategoryFilter === "all" ? undefined : dashboardCategoryFilter)
    }
  }, [activeView, analyticsShopFilter, dashboardCategoryFilter])

  const mapProducts = (ps: any[]) => setManagerProducts(ps.map((p: Record<string, unknown>) => ({
    id: p.id as string,
    product: p.name as string,
    category: p.category as string,
    sku: (p.slug as string)?.toUpperCase().slice(0, 20) || "—",
    price: `CNY ${Number(p.price).toFixed(2)}`,
    stock: p.available_item_count as number,
    status: (p.available_item_count as number) === 0 ? "Hidden" : (p.available_item_count as number) <= 10 ? "Low stock" : "Listed",
    shop_ids: (p.shop_ids as string[]) || [],
  })))

  const refreshProducts = async () => {
    const prodsResp = await getManagerProducts()
    if (prodsResp) mapProducts((prodsResp as { products: any[] }).products)
  }

  const filteredProducts = useMemo(() =>
    shopFilter === "all" ? managerProducts :
    managerProducts.filter((p) => (p.shop_ids as string[])?.includes(shopFilter))
  , [managerProducts, shopFilter])

  const handleCreateProduct = async () => {
    if (!productForm.name.trim() || !productForm.price) return
    setProductLoading(true)
    setCreateError("")
    try {
      const result = await createProduct({
        name: productForm.name,
        description: productForm.description,
        price: productForm.price,
        available_item_count: productForm.stock,
        category: { name: productForm.categoryName || "Uncategorized", description: "" },
        shop_id: productForm.shopId || undefined,
      })
      // Upload images if selected
      if (imageFiles && imageFiles.length > 0) {
        const prodId = (result as any).id || (result as any).slug
        if (prodId) {
          const formData = new FormData()
          for (let i = 0; i < imageFiles.length; i++) formData.append("files", imageFiles[i])
          await fetch(`/api/backend/shop/${encodeURIComponent(String(prodId))}/images`, { method: "POST", body: formData, credentials: "include" })
        }
      }
      setProductForm({ name: "", description: "", price: 0, stock: 0, categoryName: "", shopId: "" })
      setImageFiles(null)
      setShowCreateModal(false)
      refreshProducts()
    } catch (e) {
      setCreateError(e instanceof Error ? e.message : "Failed to create product.")
    }
    finally { setProductLoading(false) }
  }

  const startEdit = (p: Record<string, unknown>) => {
    setEditingProduct(p)
    setEditForm({
      name: (p.product as string) || "",
      description: (p.description as string) || "",
      price: parsePrice(p.price as string),
      stock: p.stock as number,
      categoryName: (p.category as string) || "",
    })
  }

  const handleUpdateProduct = async () => {
    if (!editingProduct) return
    try {
      const id = (editingProduct.id as string) || (editingProduct.sku as string)
      await updateProduct(String(id), {
        name: editForm.name,
        description: editForm.description,
        price: editForm.price,
        available_item_count: editForm.stock,
        category: { name: editForm.categoryName || "Uncategorized", description: "" },
      })
      setEditingProduct(null)
      refreshProducts()
    } catch { /* ignore */ }
  }

  const handleDeleteProduct = async (id: string) => {
    if (!confirm("Delete this product?")) return
    try {
      await deleteProduct(id)
      refreshProducts()
      alert("Product deleted.")
    } catch { alert("Failed to delete product.") }
  }

  const handleDeleteShop = async (shopId: string) => {
    if (!confirm("Request deletion of this shop? Admin approval required.")) return
    try {
      await requestDeleteShop(shopId)
      fetchShops()
    } catch { /* ignore */ }
  }

  const parsePrice = (val: string) => Number(val.replace("CNY ", "")) || 0

  const stats = dashboard?.stats as Record<string, number> | undefined
  const lowStock = (dashboard?.low_stock as string[]) || []
  const metrics = stats ? [
    { label: "Products", value: String(stats.products), detail: `${stats.low_stock_products} low-stock items` },
    { label: "Orders", value: String(stats.orders), detail: "Total orders" },
    { label: "Shops", value: String(stats.shops || 0), detail: "Managed shops" },
    { label: "Low stock alerts", value: String(stats.low_stock_products), detail: lowStock.slice(0, 3).join(", ") || "None" },
  ] : []

  const navItems: ManagerView[] = ["Dashboard", "My Shops", "Products", "Orders"]

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
      <header className="sticky top-0 z-40 border-b border-ui-border-base bg-gray-200">
        <div className="content-container flex h-16 items-center justify-between txt-xsmall-plus text-ui-fg-subtle">
          <div className="flex items-center gap-x-4">
            <span className="text-ui-fg-base">MANAGER PANEL</span>
            <span className="hidden text-ui-fg-muted small:inline">Shop operations</span>
          </div>
          <div className="flex items-center gap-x-3">
            <a className="hover:text-ui-fg-base text-small-regular" href="/hall">Hall</a>
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

                  {/* Analytics section */}
                  <div className="flex items-center gap-3">
                    <label className="text-small-regular text-ui-fg-subtle">Filter by category:</label>
                    <select
                      className="h-10 rounded-rounded border border-ui-border-base bg-ui-bg-field px-3 text-small-regular"
                      value={dashboardCategoryFilter}
                      onChange={(e) => setDashboardCategoryFilter(e.target.value)}
                    >
                      <option value="all">All categories</option>
                      {analyticsCategories.map((c) => (
                        <option key={c.id} value={c.id}>{c.name}</option>
                      ))}
                    </select>
                  </div>

                  <section className="grid grid-cols-1 gap-4 small:grid-cols-2 medium:grid-cols-4">
                    <MetricCard
                      label="Top shop (last 7 days)"
                      value={dashboardAnalytics?.top_shop?.shop_name || "—"}
                      detail={
                        dashboardAnalytics?.top_shop
                          ? `${dashboardAnalytics.top_shop.order_count} orders, CNY ${Number(dashboardAnalytics.top_shop.sales_amount).toFixed(2)}`
                          : "No data"
                      }
                    />
                    <MetricCard
                      label="Top product (last 7 days)"
                      value={dashboardAnalytics?.top_product?.product_name || "—"}
                      detail={
                        dashboardAnalytics?.top_product
                          ? `${dashboardAnalytics.top_product.order_count} orders`
                          : "No data"
                      }
                    />
                    <MetricCard
                      label="Predicted top shop (next 7 days)"
                      value={dashboardAnalytics?.predicted_shop?.shop_name || "—"}
                      detail={
                        dashboardAnalytics?.predicted_shop
                          ? `~${dashboardAnalytics.predicted_shop.predicted_daily_orders} orders/day predicted (based on last year same period)`
                          : "No historical data"
                      }
                    />
                    <MetricCard
                      label="Predicted top product (next 7 days)"
                      value={dashboardAnalytics?.predicted_product?.product_name || "—"}
                      detail={
                        dashboardAnalytics?.predicted_product
                          ? `~${dashboardAnalytics.predicted_product.predicted_daily_orders} orders/day predicted (based on last year same period)`
                          : "No historical data"
                      }
                    />
                  </section>
                </>
              )}
              {activeView === "Products" && (
                <div className="flex flex-col gap-y-6">
                  <div className="flex items-center gap-3 flex-wrap">
                    <div className="w-48">
                      <select
                        className="h-10 w-full rounded-rounded border border-ui-border-base bg-ui-bg-field px-3 text-small-regular"
                        value={shopFilter}
                        onChange={(e) => setShopFilter(e.target.value)}
                      >
                        <option value="all">All shops</option>
                        {rawManagerShopsRef.current.map((s) => (
                          <option key={s.id as string} value={s.id as string}>{s.name as string}</option>
                        ))}
                      </select>
                    </div>
                    <div className="flex-1" />
                    <Button variant="secondary" onClick={() => { setShowCreateModal(true); setEditMode(false) }}>Create product</Button>
                    <Button variant={editMode ? "secondary" : "secondary"} onClick={() => setEditMode(!editMode)}>
                      {editMode ? "Done editing" : "Edit products"}
                    </Button>
                  </div>
                  {editMode ? (
                    filteredProducts.length > 0 && (
                      <div className="rounded-rounded border border-ui-border-base bg-white p-3">
                        <h2 className="text-base-semi p-3 pb-0">Edit products</h2>
                        <div className="flex flex-col gap-1 max-h-[60vh] overflow-y-auto p-3">
                          {filteredProducts.map((p, i) => {
                            const prodId = String(p.id || p.sku)
                            const uploadImage = async (files: FileList | null) => {
                              if (!files || files.length === 0) return
                              const fd = new FormData()
                              for (let j = 0; j < files.length; j++) fd.append("files", files[j])
                              await fetch(`/api/backend/shop/${encodeURIComponent(prodId)}/images`, { method: "POST", body: fd, credentials: "include" })
                              refreshProducts()
                            }
                            return (
                            <div key={i} className="flex flex-col gap-2 border-b border-ui-border-base py-2 last:border-b-0">
                              <div className="flex items-center justify-between">
                                <div className="flex-1 min-w-0 grid grid-cols-1 small:grid-cols-4 gap-2">
                                  <input className="h-8 rounded border px-2 text-xs" defaultValue={String(p.product)} onChange={(e) => { p.product = e.target.value }} />
                                  <input className="h-8 rounded border px-2 text-xs" defaultValue={String(p.price)} onChange={(e) => { p.price = e.target.value }} />
                                  <input className="h-8 rounded border px-2 text-xs" type="number" defaultValue={String(p.stock)} onChange={(e) => { p.stock = Number(e.target.value) }} />
                                  <input className="h-8 rounded border px-2 text-xs" defaultValue={String(p.category)} onChange={(e) => { p.category = e.target.value }} />
                                </div>
                                <div className="flex gap-1 shrink-0 ml-2">
                                  <Button variant="secondary" className="h-7 text-xs px-2" onClick={async () => {
                                    try {
                                      await updateProduct(prodId, {
                                        name: String(p.product), price: parsePrice(String(p.price)),
                                        available_item_count: Number(p.stock),
                                        category: { name: String(p.category), description: "" },
                                      })
                                      refreshProducts()
                                      setEditMode(false)
                                      alert("Product saved successfully.")
                                    } catch {
                                      alert("Failed to save product.")
                                    }
                                  }}>Save</Button>
                                  <Button variant="secondary" className="h-7 text-xs px-2 text-rose-600" onClick={() => handleDeleteProduct(prodId)}>Delete</Button>
                                </div>
                              </div>
                              <div className="flex items-center gap-2">
                                <input
                                  type="file" multiple accept="image/*"
                                  id={`img-${i}`} className="hidden"
                                  onChange={(e) => {
                                    if (e.target.files && e.target.files.length > 0) {
                                      setEditFileNames(prev => ({ ...prev, [i]: Array.from(e.target.files!).map(f => f.name).join(", ") }))
                                    }
                                    uploadImage(e.target.files)
                                  }}
                                />
                                <label htmlFor={`img-${i}`} className="inline-flex h-7 items-center rounded-md border border-ui-border-base bg-ui-bg-subtle px-3 text-xs cursor-pointer hover:bg-ui-bg-base">
                                  Choose files
                                </label>
                                <span className="text-xs text-ui-fg-muted truncate max-w-[160px]">{editFileNames[i] || "No file chosen"}</span>
                              </div>
                            </div>
                          )})}
                        </div>
                      </div>
                    )
                  ) : (
                    <TableView
                      title="Products"
                      description="All products in your catalog."
                      rows={filteredProducts}
                      query={query}
                    />
                  )}

                  {showCreateModal && (
                    <div className="fixed inset-0 z-[200] flex items-center justify-center">
                      <div className="fixed inset-0 bg-black/50" onClick={() => setShowCreateModal(false)} />
                      <div className="relative bg-white rounded-lg shadow-xl p-6 max-w-lg w-full mx-4 flex flex-col gap-y-3 max-h-[90vh] overflow-y-auto">
                        <h3 className="text-base-semi">New Product</h3>
                        <div className="grid grid-cols-1 gap-3 small:grid-cols-2">
                          <Input label="Product name" name="prod-name" value={productForm.name} onChange={(e) => setProductForm({ ...productForm, name: e.target.value })} />
                          <Input label="Price (CNY)" name="prod-price" type="number" value={String(productForm.price)} onChange={(e) => setProductForm({ ...productForm, price: Number(e.target.value) || 0 })} />
                          <Input label="Stock" name="prod-stock" type="number" value={String(productForm.stock)} onChange={(e) => setProductForm({ ...productForm, stock: Number(e.target.value) || 0 })} />
                          <Input label="Category name" name="prod-cat" value={productForm.categoryName} onChange={(e) => setProductForm({ ...productForm, categoryName: e.target.value })} />
                        </div>
                        <Input label="Description" name="prod-desc" value={productForm.description} onChange={(e) => setProductForm({ ...productForm, description: e.target.value })} />
                        <div className="flex flex-col gap-y-1">
                          <label className="txt-medium text-ui-fg-base">Images</label>
                          <div className="flex items-center gap-2">
                            <input
                              type="file" multiple accept="image/*"
                              id="create-product-images" className="hidden"
                              onChange={(e) => setImageFiles(e.target.files)}
                            />
                            <label htmlFor="create-product-images" className="inline-flex h-10 items-center rounded-md border border-ui-border-base bg-ui-bg-subtle px-4 text-small-regular cursor-pointer hover:bg-ui-bg-base">
                              Choose files
                            </label>
                            <span className="text-small-regular text-ui-fg-muted">
                              {imageFiles && imageFiles.length > 0
                                ? `${imageFiles.length} file(s) selected`
                                : "No file chosen"}
                            </span>
                          </div>
                        </div>
                        {rawManagerShopsRef.current.filter((s) => s.status === "active").length > 0 ? (
                          <div className="flex flex-col gap-y-1">
                            <label className="txt-medium text-ui-fg-base">Shop</label>
                            <select
                              className="h-10 rounded-rounded border border-ui-border-base bg-ui-bg-field px-3 text-small-regular"
                              value={productForm.shopId}
                              onChange={(e) => setProductForm({ ...productForm, shopId: e.target.value })}
                            >
                              <option value="">No shop (unlisted)</option>
                              {rawManagerShopsRef.current.filter((s) => s.status === "active").map((shop) => (
                                <option key={shop.id as string} value={shop.id as string}>{shop.name as string}</option>
                              ))}
                            </select>
                          </div>
                        ) : (
                          <p className="text-small-regular text-ui-fg-muted">You need an approved shop before you can upload products. Create one in My Shops.</p>
                        )}
                        {createError && <p className="text-rose-500 text-small-regular">{createError}</p>}
                        <div className="flex gap-2 justify-end mt-2">
                          <Button variant="secondary" onClick={() => { setShowCreateModal(false); setCreateError("") }}>Cancel</Button>
                          <Button variant="secondary" onClick={handleCreateProduct} disabled={!productForm.name.trim() || !productForm.price} isLoading={productLoading}>Create product</Button>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}
              {activeView === "Orders" && (
                <TableView title="Orders" description="Orders for your shops." rows={managerOrders} query={query} />
              )}
              {activeView === "My Shops" && (
                <div className="flex flex-col gap-y-6">
                  <TableView
                    title="My Shops"
                    description="Shops you own. New shops require admin approval before appearing in the marketplace."
                    rows={managerShops}
                    query={query}
                    actions={
                      <Button variant="secondary" onClick={() => setShowCreateShop(!showCreateShop)}>
                        {showCreateShop ? "Cancel" : "Create shop"}
                      </Button>
                    }
                    rowActions={(row, i) => {
                      const shop = rawManagerShopsRef.current[i]
                      if (!shop) return null
                      return (
                        <Button variant="secondary" className="h-7 text-xs px-2 text-rose-600" onClick={() => handleDeleteShop(shop.id as string)}>Delete</Button>
                      )
                    }}
                  />

                  {/* Bar chart: order trend */}
                  <div className="rounded-rounded border border-ui-border-base bg-white p-5">
                    <div className="flex items-center justify-between mb-4">
                      <h2 className="text-base-semi">Order Trend (Last 7 Days)</h2>
                      <select
                        className="h-10 rounded-rounded border border-ui-border-base bg-ui-bg-field px-3 text-small-regular"
                        value={analyticsShopFilter}
                        onChange={(e) => setAnalyticsShopFilter(e.target.value)}
                      >
                        <option value="all">All shops</option>
                        {rawManagerShopsRef.current.map((s) => (
                          <option key={s.id as string} value={s.id as string}>{s.name as string}</option>
                        ))}
                      </select>
                    </div>
                    {shopAnalytics.length > 0 ? (
                      <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={shopAnalytics} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="date" />
                          <YAxis yAxisId="left" orientation="left" stroke="#8884d8" />
                          <YAxis yAxisId="right" orientation="right" stroke="#82ca9d" />
                          <Tooltip />
                          <Legend />
                          <Bar yAxisId="left" dataKey="order_count" fill="#8884d8" name="Orders" />
                          <Bar yAxisId="right" dataKey="sales_amount" fill="#82ca9d" name="Sales (CNY)" />
                        </BarChart>
                      </ResponsiveContainer>
                    ) : (
                      <p className="text-small-regular text-ui-fg-muted py-8 text-center">No order data available for the last 7 days.</p>
                    )}
                  </div>
                  {showCreateShop && (
                    <div className="rounded-rounded border border-ui-border-base bg-white p-5 flex flex-col gap-y-3">
                      <h3 className="text-base-semi">New Shop</h3>
                      <Input label="Shop name" name="shop-name" value={shopForm.name} onChange={(e) => setShopForm({ ...shopForm, name: e.target.value })} />
                      <Input label="Description" name="shop-desc" value={shopForm.description} onChange={(e) => setShopForm({ ...shopForm, description: e.target.value })} />
                      <Input label="Category (optional)" name="shop-cat" value={shopForm.category} onChange={(e) => setShopForm({ ...shopForm, category: e.target.value })} />
                      <Button variant="secondary" onClick={handleCreateShop} disabled={!shopForm.name.trim()}>Submit for approval</Button>
                    </div>
                  )}
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
