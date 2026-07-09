"use client"

import { Badge, Button, Table } from "@medusajs/ui"
import Input from "@modules/common/components/input"
import NativeSelect from "@modules/common/components/native-select"
import { FormEvent, ReactNode, useMemo, useState } from "react"

const TEST_MANAGER_EMAIL = "manager@email.com"
const TEST_MANAGER_PASSWORD = "leamonlee04"

const stats = [
  { label: "Shops", value: "3", detail: "2 active, 1 under review" },
  { label: "Active products", value: "248", detail: "14 low-stock items" },
  { label: "Orders today", value: "37", detail: "9 waiting shipment" },
  { label: "Monthly income", value: "CNY 82,460", detail: "Net after refunds" },
  { label: "Pending applications", value: "1", detail: "Shop review in progress" },
  { label: "Product approvals", value: "6", detail: "3 need confirmation" },
  { label: "Refund requests", value: "4", detail: "2 waiting response" },
  { label: "Average order value", value: "CNY 214", detail: "Up 8% this month" },
]

const shops = [
  {
    name: "Northline Home",
    status: "Active",
    products: 84,
    orders: 412,
    monthlyIncome: "CNY 38,240",
    rating: "4.8",
  },
  {
    name: "Desk Goods",
    status: "Active",
    products: 42,
    orders: 188,
    monthlyIncome: "CNY 19,860",
    rating: "4.6",
  },
  {
    name: "Everyday Carry Studio",
    status: "Under review",
    products: 0,
    orders: 0,
    monthlyIncome: "CNY 0",
    rating: "New",
  },
]

const applications = [
  {
    shop: "Everyday Carry Studio",
    category: "Bags",
    submitted: "2026-07-07",
    reviewer: "Platform Admin",
    status: "Under review",
  },
  {
    shop: "Northline Home",
    category: "Home",
    submitted: "2026-05-19",
    reviewer: "Platform Admin",
    status: "Approved",
  },
  {
    shop: "Desk Goods",
    category: "Stationery",
    submitted: "2026-06-03",
    reviewer: "Platform Admin",
    status: "Changes requested",
  },
]

const productApprovals = [
  {
    id: "PA-2041",
    product: "Canvas Storage Basket",
    shop: "Northline Home",
    price: "CNY 149",
    status: "Draft",
  },
  {
    id: "PA-2040",
    product: "Aluminum Pen Tray",
    shop: "Desk Goods",
    price: "CNY 89",
    status: "Pending",
  },
  {
    id: "PA-2039",
    product: "Compact Sling Bag",
    shop: "Everyday Carry Studio",
    price: "CNY 299",
    status: "Confirmed",
  },
  {
    id: "PA-2038",
    product: "Walnut Desk Shelf",
    shop: "Desk Goods",
    price: "CNY 468",
    status: "Rejected",
  },
]

const products = [
  {
    product: "Linen Organizer Bin",
    shop: "Northline Home",
    sku: "NLH-BIN-01",
    price: "CNY 129",
    stock: 42,
    status: "Listed",
  },
  {
    product: "Desk Lamp Pro",
    shop: "Desk Goods",
    sku: "DSK-LMP-02",
    price: "CNY 368",
    stock: 8,
    status: "Low stock",
  },
  {
    product: "Cable Dock",
    shop: "Desk Goods",
    sku: "DSK-CBL-01",
    price: "CNY 59",
    stock: 126,
    status: "Listed",
  },
  {
    product: "Wool Throw",
    shop: "Northline Home",
    sku: "NLH-THR-04",
    price: "CNY 299",
    stock: 0,
    status: "Hidden",
  },
]

const orders = [
  {
    order: "ORD-10842",
    customer: "Nora Lee",
    shop: "Northline Home",
    payment: "Paid",
    shipment: "Preparing",
    total: "CNY 428",
    date: "2026-07-09",
    status: "Unshipped",
  },
  {
    order: "ORD-10841",
    customer: "Sam Carter",
    shop: "Desk Goods",
    payment: "Paid",
    shipment: "Shipped",
    total: "CNY 189",
    date: "2026-07-09",
    status: "Shipped",
  },
  {
    order: "ORD-10840",
    customer: "June Wu",
    shop: "Northline Home",
    payment: "Refund requested",
    shipment: "Delivered",
    total: "CNY 518",
    date: "2026-07-08",
    status: "Refund",
  },
]

const shipments = [
  {
    shipment: "SHP-7102",
    order: "ORD-10842",
    customer: "Nora Lee",
    method: "SF Express",
    tracking: "Pending",
    status: "Preparing",
  },
  {
    shipment: "SHP-7101",
    order: "ORD-10841",
    customer: "Sam Carter",
    method: "JD Logistics",
    tracking: "JD780029141",
    status: "In transit",
  },
  {
    shipment: "SHP-7100",
    order: "ORD-10836",
    customer: "Maya Lin",
    method: "Cainiao",
    tracking: "CN92818301",
    status: "Delivered",
  },
]

const revenueRows = [
  { month: "July 2026", orders: 312, gross: "CNY 91,820", refunds: "CNY 4,180", net: "CNY 82,460" },
  { month: "June 2026", orders: 286, gross: "CNY 79,410", refunds: "CNY 3,290", net: "CNY 72,880" },
  { month: "May 2026", orders: 251, gross: "CNY 70,250", refunds: "CNY 2,810", net: "CNY 64,930" },
]

const transactions = [
  { id: "PAY-8842", order: "ORD-10842", method: "Credit card", amount: "CNY 428", status: "Completed" },
  { id: "PAY-8841", order: "ORD-10841", method: "Alipay", amount: "CNY 189", status: "Completed" },
  { id: "REF-0192", order: "ORD-10840", method: "Refund", amount: "CNY 518", status: "Pending" },
]

const bestSellers = [
  { product: "Desk Lamp Pro", units: 86, revenue: "CNY 31,648", shop: "Desk Goods" },
  { product: "Linen Organizer Bin", units: 74, revenue: "CNY 9,546", shop: "Northline Home" },
  { product: "Cable Dock", units: 61, revenue: "CNY 3,599", shop: "Desk Goods" },
]

const activities = [
  "ORD-10842 is paid and waiting shipment.",
  "Canvas Storage Basket product approval was saved as draft.",
  "Everyday Carry Studio shop application moved to under review.",
  "Desk Lamp Pro stock dropped below 10 units.",
]

const navItems = [
  "Dashboard",
  "My Shops",
  "Apply for Shop",
  "Shop Preview",
  "Product Approvals",
  "Products",
  "Orders",
  "Shipments",
  "Income",
  "Reports",
  "Profile",
] as const

type ManagerView = (typeof navItems)[number]
type Row = Record<string, string | number>

const getBadgeColor = (status: string) => {
  if (
    [
      "Active",
      "Approved",
      "Confirmed",
      "Listed",
      "Paid",
      "Completed",
      "Delivered",
      "Shipped",
    ].includes(status)
  ) {
    return "green"
  }
  if (["Rejected", "Hidden", "Refund", "Blocked"].includes(status)) {
    return "red"
  }
  if (["Under review", "Changes requested", "Low stock"].includes(status)) {
    return "purple"
  }
  return "orange"
}

const ManagerPanel = () => {
  const [isSignedIn, setIsSignedIn] = useState(false)
  const [loginError, setLoginError] = useState("")
  const [activeView, setActiveView] = useState<ManagerView>("Dashboard")
  const [query, setQuery] = useState("")

  const handleLogin = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()

    const formData = new FormData(event.currentTarget)
    const email = String(formData.get("email") || "").trim().toLowerCase()
    const password = String(formData.get("password") || "")

    if (email !== TEST_MANAGER_EMAIL || password !== TEST_MANAGER_PASSWORD) {
      setLoginError("Invalid manager email or password.")
      return
    }

    setLoginError("")
    setIsSignedIn(true)
  }

  const handleViewChange = (item: ManagerView) => {
    setActiveView(item)
    setQuery("")
  }

  if (!isSignedIn) {
    return (
      <div className="min-h-screen bg-ui-bg-base">
        <div className="content-container flex min-h-screen items-center justify-center py-16">
          <div className="flex w-full max-w-sm flex-col">
            <div className="mb-8">
              <p className="txt-xsmall-plus uppercase text-ui-fg-muted">
                Manager Panel
              </p>
              <h1 className="mt-2 text-xl-semi text-ui-fg-base">
                Sign in to manage shops
              </h1>
              <p className="mt-2 text-small-regular text-ui-fg-subtle">
                Shop managers can apply for shops, create product approvals,
                process orders, and track income.
              </p>
            </div>
            <form className="flex flex-col gap-y-4" onSubmit={handleLogin}>
              <Input
                label="Email"
                name="email"
                type="email"
                autoComplete="email"
                required
              />
              <Input
                label="Password"
                name="password"
                type="password"
                autoComplete="current-password"
                required
              />
              <Button type="submit" className="mt-2 h-10 w-full">
                Sign in
              </Button>
              {loginError && (
                <p className="text-small-regular text-rose-500">
                  {loginError}
                </p>
              )}
              <p className="text-small-regular text-ui-fg-muted">
                Test account: {TEST_MANAGER_EMAIL}
              </p>
            </form>
          </div>
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
            <span className="hidden text-ui-fg-muted small:inline">
              Shop operations
            </span>
          </div>
          <div className="flex items-center gap-x-3">
            <a className="hidden hover:text-ui-fg-base small:block" href="/">
              Customer View
            </a>
            <a className="hidden hover:text-ui-fg-base small:block" href="/admin">
              Admin View
            </a>
            <Button
              variant="secondary"
              className="h-9"
              onClick={() => setIsSignedIn(false)}
            >
              Sign out
            </Button>
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

        <main className="flex flex-col gap-y-8">
          <ViewHeader activeView={activeView} query={query} setQuery={setQuery} />
          <ManagerViewContent activeView={activeView} query={query} />
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
  activeView: ManagerView
  query: string
  setQuery: (value: string) => void
}) => {
  const titles: Record<ManagerView, string> = {
    Dashboard: "Shop operation overview",
    "My Shops": "Manage your shops",
    "Apply for Shop": "New shop application",
    "Shop Preview": "Public shop preview",
    "Product Approvals": "Create and track product approvals",
    Products: "Product catalog management",
    Orders: "Order processing",
    Shipments: "Shipment tracking",
    Income: "Income and sales data",
    Reports: "Reports and analytics",
    Profile: "Manager profile",
  }

  return (
    <section className="flex flex-col justify-between gap-4 border-b border-ui-border-base pb-8 small:flex-row small:items-end">
      <div>
        <p className="txt-xsmall-plus uppercase text-ui-fg-muted">
          {activeView}
        </p>
        <h1 className="mt-2 text-2xl-semi text-ui-fg-base">
          {titles[activeView]}
        </h1>
        <p className="mt-2 max-w-2xl text-small-regular text-ui-fg-subtle">
          {getViewDescription(activeView)}
        </p>
      </div>
      {["Dashboard", "Apply for Shop", "Shop Preview", "Income", "Reports", "Profile"].includes(activeView) ? (
        <QuickHeaderAction activeView={activeView} />
      ) : (
        <div className="w-full small:w-72">
          <Input
            label={`Search ${activeView.toLowerCase()}`}
            name="manager-search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
        </div>
      )}
    </section>
  )
}

const QuickHeaderAction = ({ activeView }: { activeView: ManagerView }) => {
  const labels: Partial<Record<ManagerView, string>> = {
    Dashboard: "Create product approval",
    "Apply for Shop": "Save draft",
    "Shop Preview": "Open public page",
    Income: "Export income CSV",
    Reports: "Download report",
    Profile: "Edit profile",
  }

  return (
    <Button variant="secondary" className="h-10 w-full small:w-auto">
      {labels[activeView]}
    </Button>
  )
}

const ManagerViewContent = ({
  activeView,
  query,
}: {
  activeView: ManagerView
  query: string
}) => {
  if (activeView === "Dashboard") {
    return <DashboardView />
  }

  if (activeView === "My Shops") {
    return (
      <TableView
        title="My shops"
        description="Open shop details, edit shop information, preview the public page, and inspect shop-level products, orders, and income."
        rows={shops}
        actions={<Button variant="secondary">Preview selected shop</Button>}
        query={query}
      />
    )
  }

  if (activeView === "Apply for Shop") {
    return <ShopApplicationView />
  }

  if (activeView === "Shop Preview") {
    return <ShopPreviewView />
  }

  if (activeView === "Product Approvals") {
    return <ProductApprovalsView query={query} />
  }

  if (activeView === "Products") {
    return (
      <TableView
        title="Products"
        description="Manage listed products, variants, images, stock, SKU, status, and public product links."
        rows={products}
        actions={<Button variant="secondary">Update stock</Button>}
        query={query}
      />
    )
  }

  if (activeView === "Orders") {
    return <OrdersView query={query} />
  }

  if (activeView === "Shipments") {
    return (
      <TableView
        title="Shipments"
        description="Add tracking numbers, monitor delivery progress, and connect shipments to related orders."
        rows={shipments}
        actions={<Button variant="secondary">Add tracking number</Button>}
        query={query}
      />
    )
  }

  if (activeView === "Income") {
    return <IncomeView />
  }

  if (activeView === "Reports") {
    return <ReportsView />
  }

  return <ProfileView />
}

const DashboardView = () => {
  return (
    <>
      <section className="grid grid-cols-1 gap-4 small:grid-cols-2 medium:grid-cols-4">
        {stats.map((stat) => (
          <MetricCard key={stat.label} {...stat} />
        ))}
      </section>

      <section className="grid grid-cols-1 gap-6 medium:grid-cols-[1fr_320px]">
        <TableView
          title="Today queue"
          description="Orders, product approvals, and shop application work that needs manager attention."
          rows={[
            { item: "Unshipped orders", count: 9, owner: "Fulfillment", status: "Pending" },
            { item: "Product approvals", count: 3, owner: "Catalog", status: "Draft" },
            { item: "Refund requests", count: 2, owner: "Support", status: "Under review" },
          ]}
          actions={<Badge color="orange">14 open</Badge>}
          query=""
          compact
        />
        <div className="flex flex-col gap-4">
          <InfoPanel title="Quick actions">
            <Button variant="secondary" className="h-10 justify-start">
              Apply for a new shop
            </Button>
            <Button variant="secondary" className="h-10 justify-start">
              Create product approval
            </Button>
            <Button variant="secondary" className="h-10 justify-start">
              Prepare shipments
            </Button>
          </InfoPanel>
          <InfoPanel title="Recent activity">
            {activities.map((activity) => (
              <p key={activity}>{activity}</p>
            ))}
          </InfoPanel>
        </div>
      </section>
    </>
  )
}

const ShopApplicationView = () => {
  return (
    <div className="grid grid-cols-1 gap-6 medium:grid-cols-[1fr_340px]">
      <div className="rounded-rounded border border-ui-border-base bg-white">
        <div className="border-b border-ui-border-base p-5">
          <h2 className="text-base-semi">Shop information</h2>
          <p className="mt-1 text-small-regular text-ui-fg-subtle">
            Submit shop details for admin review before the shop can sell products.
          </p>
        </div>
        <form className="grid grid-cols-1 gap-4 p-5 small:grid-cols-2">
          <Input label="Shop name" name="shop-name" defaultValue="Everyday Carry Studio" required />
          <Input label="Contact email" name="contact-email" defaultValue="manager@email.com" required />
          <Input label="Business owner" name="business-owner" defaultValue="Avery Chen" required />
          <Input label="Business phone" name="business-phone" defaultValue="+86 138 0000 0000" />
          <NativeSelect name="shop-category" defaultValue="bags">
            <option value="home">Home</option>
            <option value="stationery">Stationery</option>
            <option value="bags">Bags</option>
            <option value="electronics">Electronics</option>
          </NativeSelect>
          <Input label="Business license no." name="license" defaultValue="SH-2026-7812" />
          <div className="small:col-span-2">
            <TextArea
              label="Shop description"
              name="shop-description"
              defaultValue="Curated everyday carry goods with durable materials, compact forms, and practical details."
            />
          </div>
          <div className="small:col-span-2">
            <TextArea
              label="Application reason"
              name="application-reason"
              defaultValue="We already operate two stores and want to separate travel bags into a focused shop."
            />
          </div>
          <UploadPlaceholder title="Logo upload" description="Square shop logo placeholder" />
          <UploadPlaceholder title="Banner upload" description="Wide storefront banner placeholder" />
          <div className="flex flex-col gap-3 small:col-span-2 small:flex-row">
            <Button className="h-10 w-full small:w-auto">Submit application</Button>
            <Button variant="secondary" className="h-10 w-full small:w-auto">
              Save draft
            </Button>
          </div>
        </form>
      </div>
      <div className="flex flex-col gap-4">
        <InfoPanel title="Application status">
          {applications.map((application) => (
            <div
              key={application.shop}
              className="flex items-center justify-between gap-3 border-b border-ui-border-base pb-3 last:border-b-0 last:pb-0"
            >
              <div>
                <p className="text-small-semi text-ui-fg-base">
                  {application.shop}
                </p>
                <p className="text-small-regular text-ui-fg-muted">
                  {application.submitted}
                </p>
              </div>
              <Badge color={getBadgeColor(application.status)}>
                {application.status}
              </Badge>
            </div>
          ))}
        </InfoPanel>
        <InfoPanel title="Review steps">
          <p>Draft application</p>
          <p>Submit business and contact information</p>
          <p>Admin review and category check</p>
          <p>Approved shops can receive confirmed products</p>
        </InfoPanel>
      </div>
    </div>
  )
}

const ShopPreviewView = () => {
  const previewProducts = products.filter((product) => product.shop === "Northline Home")

  return (
    <div className="flex flex-col gap-6">
      <section className="overflow-hidden rounded-rounded border border-ui-border-base bg-white">
        <div className="flex min-h-[220px] items-end bg-ui-bg-subtle p-6">
          <div className="flex flex-col gap-4 small:flex-row small:items-end">
            <div className="flex h-24 w-24 items-center justify-center rounded-rounded border border-ui-border-base bg-white text-xl-semi">
              NH
            </div>
            <div>
              <p className="txt-xsmall-plus uppercase text-ui-fg-muted">
                Public shop preview
              </p>
              <h2 className="mt-2 text-2xl-semi">Northline Home</h2>
              <p className="mt-2 max-w-2xl text-small-regular text-ui-fg-subtle">
                Quiet home storage, soft textiles, and small details for organized living.
              </p>
              <div className="mt-3 flex flex-wrap gap-2">
                <Badge color="green">4.8 rating</Badge>
                <Badge color="green">84 products</Badge>
                <Badge color="orange">Home</Badge>
              </div>
            </div>
          </div>
        </div>
      </section>
      <section className="grid grid-cols-1 gap-4 small:grid-cols-3">
        <InfoPanel title="Featured categories">
          <p>Storage</p>
          <p>Textiles</p>
          <p>Kitchen</p>
        </InfoPanel>
        <InfoPanel title="Best sellers">
          <p>Linen Organizer Bin</p>
          <p>Wool Throw</p>
          <p>Oak Serving Tray</p>
        </InfoPanel>
        <InfoPanel title="Customer reviews">
          <p>Clean packaging and fast delivery.</p>
          <p>Product quality matched the photos.</p>
        </InfoPanel>
      </section>
      <section>
        <h2 className="mb-4 text-base-semi">Product grid preview</h2>
        <div className="grid grid-cols-2 gap-x-6 gap-y-8 small:grid-cols-3 medium:grid-cols-4">
          {previewProducts.map((product) => (
            <div key={product.sku} className="group">
              <div className="relative aspect-[11/14] w-full overflow-hidden rounded-large bg-ui-bg-subtle p-4 shadow-elevation-card-rest transition-shadow duration-150 ease-in-out group-hover:shadow-elevation-card-hover">
                <div className="flex h-full items-center justify-center border border-dashed border-ui-border-base text-small-regular text-ui-fg-muted">
                  Product image
                </div>
              </div>
              <div className="mt-4 flex justify-between gap-3 txt-compact-medium">
                <p>{product.product}</p>
                <p className="text-ui-fg-subtle">{product.price}</p>
              </div>
              <p className="mt-1 text-small-regular text-ui-fg-muted">
                {product.status}
              </p>
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}

const ProductApprovalsView = ({ query }: { query: string }) => {
  return (
    <div className="grid grid-cols-1 gap-6 medium:grid-cols-[1fr_340px]">
      <TableView
        title="Product approval records"
        description="Managers create ProductApproval records that contain new products. Confirmed records can be listed in a shop."
        rows={productApprovals}
        actions={<Button variant="secondary">Create approval</Button>}
        query={query}
      />
      <InfoPanel title="New product draft">
        <Input label="Product name" name="approval-product" defaultValue="Canvas Storage Basket" />
        <NativeSelect name="approval-shop" defaultValue="northline">
          <option value="northline">Northline Home</option>
          <option value="desk">Desk Goods</option>
        </NativeSelect>
        <Input label="SKU" name="approval-sku" defaultValue="NLH-BSK-02" />
        <Input label="Price" name="approval-price" defaultValue="CNY 149" />
        <div className="grid grid-cols-2 gap-3">
          <Input label="Variant" name="approval-variant" defaultValue="Natural" />
          <Input label="Stock" name="approval-stock" defaultValue="60" />
        </div>
        <UploadPlaceholder title="Product images" description="ProductImage upload placeholders" />
        <Button className="h-10">Save approval draft</Button>
      </InfoPanel>
    </div>
  )
}

const OrdersView = ({ query }: { query: string }) => {
  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap gap-2">
        {["All", "Paid", "Unshipped", "Shipped", "Refund"].map((filter) => (
          <Button key={filter} variant="secondary" className="h-9">
            {filter}
          </Button>
        ))}
      </div>
      <TableView
        title="Orders"
        description="Process shop orders, prepare shipments, mark shipped, add tracking, cancel orders, and handle refund records."
        rows={orders}
        actions={<Button variant="secondary">Prepare shipment</Button>}
        query={query}
      />
      <InfoPanel title="Selected order detail">
        <p>Customer: Nora Lee</p>
        <p>Items: Linen Organizer Bin x2, Cable Dock x1</p>
        <p>Shipping address: 388 Wuding Road, Shanghai</p>
        <p>Next action: add package weight and tracking number.</p>
      </InfoPanel>
    </div>
  )
}

const IncomeView = () => {
  return (
    <div className="flex flex-col gap-6">
      <section className="grid grid-cols-1 gap-4 small:grid-cols-2 medium:grid-cols-4">
        <MetricCard label="Today income" value="CNY 7,820" detail="37 paid orders" />
        <MetricCard label="Weekly income" value="CNY 24,610" detail="114 paid orders" />
        <MetricCard label="Monthly net" value="CNY 82,460" detail="After CNY 4,180 refunds" />
        <MetricCard label="Average order" value="CNY 214" detail="8% above last month" />
      </section>
      <div className="grid grid-cols-1 gap-6 medium:grid-cols-2">
        <TableView
          title="Monthly revenue"
          description="Static frontend mockup for manager income review."
          rows={revenueRows}
          query=""
        />
        <TableView
          title="Recent transactions"
          description="Payment and refund transactions for managed shops."
          rows={transactions}
          query=""
        />
      </div>
      <TableView
        title="Product sales ranking"
        description="Best-selling products by units and revenue."
        rows={bestSellers}
        query=""
      />
    </div>
  )
}

const ReportsView = () => {
  return (
    <div className="grid grid-cols-1 gap-6 medium:grid-cols-2">
      <InfoPanel title="Sales report">
        <p>Monthly sales are 13% higher than June 2026.</p>
        <p>Home storage products generated the strongest revenue share.</p>
        <p>Refund rate is 4.5%, mostly from delayed delivery requests.</p>
      </InfoPanel>
      <InfoPanel title="Product performance">
        <p>Desk Lamp Pro leads revenue but stock is below reorder threshold.</p>
        <p>Wool Throw has strong views but low conversion this week.</p>
        <p>Two hidden products should be replenished or archived.</p>
      </InfoPanel>
      <InfoPanel title="Customer behavior">
        <p>Repeat customers account for 38% of July orders.</p>
        <p>Most checkout activity happens from 19:00 to 22:00.</p>
        <p>Product reviews mention packaging quality most often.</p>
      </InfoPanel>
      <InfoPanel title="Inventory risk">
        <p>14 products are below low-stock threshold.</p>
        <p>3 products have no active ProductVariant stock.</p>
        <p>Recommended action: reorder Desk Lamp Pro and Wool Throw.</p>
      </InfoPanel>
    </div>
  )
}

const ProfileView = () => {
  return (
    <div className="grid grid-cols-1 gap-6 medium:grid-cols-[1fr_340px]">
      <InfoPanel title="Account information">
        <p>Name: Avery Chen</p>
        <p>Email: manager@email.com</p>
        <p>Status: Active manager account</p>
        <p>Managed shops: Northline Home, Desk Goods, Everyday Carry Studio</p>
      </InfoPanel>
      <InfoPanel title="Security and settings">
        <p>Password updated: 2026-06-28</p>
        <p>Two-step verification: Enabled</p>
        <p>Notification email: manager@email.com</p>
        <Button variant="secondary" className="h-10">
          Manage security
        </Button>
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
                const isStatus = column === "status" || column === "payment" || column === "shipment"
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

const TextArea = ({
  label,
  name,
  defaultValue,
}: {
  label: string
  name: string
  defaultValue?: string
}) => {
  return (
    <label className="flex flex-col gap-2 text-small-regular text-ui-fg-subtle">
      {label}
      <textarea
        name={name}
        defaultValue={defaultValue}
        rows={4}
        className="block w-full resize-none rounded-md border border-ui-border-base bg-ui-bg-field px-4 py-3 text-base-regular text-ui-fg-base outline-none hover:bg-ui-bg-field-hover focus:shadow-borders-interactive-with-active"
      />
    </label>
  )
}

const UploadPlaceholder = ({
  title,
  description,
}: {
  title: string
  description: string
}) => {
  return (
    <div className="flex min-h-[140px] flex-col items-center justify-center rounded-rounded border border-dashed border-ui-border-base bg-ui-bg-subtle p-5 text-center">
      <p className="text-small-semi text-ui-fg-base">{title}</p>
      <p className="mt-1 text-small-regular text-ui-fg-muted">{description}</p>
      <Button variant="secondary" className="mt-4 h-9">
        Choose file
      </Button>
    </div>
  )
}

const getViewDescription = (view: ManagerView) => {
  const descriptions: Record<ManagerView, string> = {
    Dashboard:
      "Track shop health, pending work, order status, product approvals, refunds, and income signals.",
    "My Shops":
      "Manage shops owned by this manager and open shop detail workflows.",
    "Apply for Shop":
      "Create a shop application with business details, contact information, description, and upload placeholders.",
    "Shop Preview":
      "Preview the customer-facing shop page with banner, logo, product grid, categories, best sellers, and reviews.",
    "Product Approvals":
      "Create ProductApproval records that contain Product data before products are confirmed for listing.",
    Products:
      "Manage shop products, variants, images, categories, stock, SKU, status, and public product pages.",
    Orders:
      "Process orders from managed shops, update shipment status, cancel orders, and handle refund records.",
    Shipments:
      "Manage shipment status, tracking number, shipping address, related order, customer, and delivery progress.",
    Income:
      "Review today, weekly, monthly, and net income data, plus transactions and product sales ranking.",
    Reports:
      "Use static analytics mockups for sales reports, product performance, customer behavior, and inventory risk.",
    Profile:
      "Review manager account status, personal information, managed shops, and security settings.",
  }

  return descriptions[view]
}

const formatColumn = (column: string) =>
  column
    .replace(/([A-Z])/g, " $1")
    .replace(/^./, (letter) => letter.toUpperCase())

export default ManagerPanel
