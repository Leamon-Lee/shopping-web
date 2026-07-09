"use client"

import { Badge, Button, Table } from "@medusajs/ui"
import Input from "@modules/common/components/input"
import { FormEvent, ReactNode, useMemo, useState } from "react"

const TEST_ADMIN_EMAIL = "admin@email.com"
const TEST_ADMIN_PASSWORD = "leamonlee04"

const stats = [
  { label: "Reviewed shops", value: "128", detail: "12 pending review" },
  { label: "Categories", value: "36", detail: "Managed by platform admin" },
  { label: "Users", value: "4,812", detail: "Managers and customers" },
  { label: "Orders today", value: "214", detail: "7 abnormal orders" },
]

const shops = [
  { name: "Northline Home", manager: "Avery Chen", products: 84, status: "Pending" },
  { name: "Everyday Carry Co.", manager: "Mina Park", products: 123, status: "Approved" },
  { name: "Desk Goods", manager: "Jon Bell", products: 42, status: "Disabled" },
]

const categories = [
  { name: "Home", slug: "home", products: 216, status: "Active" },
  { name: "Stationery", slug: "stationery", products: 87, status: "Active" },
  { name: "Bags", slug: "bags", products: 43, status: "Review" },
]

const managers = [
  { name: "Avery Chen", email: "avery@northline.test", shops: 2, status: "Active" },
  { name: "Mina Park", email: "mina@carry.test", shops: 1, status: "Active" },
  { name: "Jon Bell", email: "jon@desk.test", shops: 1, status: "Blocked" },
]

const customers = [
  { name: "Nora Lee", email: "nora@example.test", orders: 16, status: "Active" },
  { name: "Sam Carter", email: "sam@example.test", orders: 3, status: "Active" },
  { name: "June Wu", email: "june@example.test", orders: 9, status: "Review" },
]

const productApprovals = [
  { product: "Canvas Tote", shop: "Northline Home", manager: "Avery Chen", status: "Pending" },
  { product: "Desk Lamp", shop: "Desk Goods", manager: "Jon Bell", status: "Rejected" },
  { product: "Travel Pouch", shop: "Everyday Carry Co.", manager: "Mina Park", status: "Confirmed" },
]

const orders = [
  { number: "ORD-10031", customer: "Nora Lee", total: "CNY 348.00", status: "Paid" },
  { number: "ORD-10032", customer: "Sam Carter", total: "CNY 79.00", status: "Pending" },
  { number: "ORD-10033", customer: "June Wu", total: "CNY 510.00", status: "Exception" },
]

const payments = [
  { id: "PAY-2201", method: "Credit card", amount: "CNY 348.00", status: "Completed" },
  { id: "PAY-2202", method: "Bank transfer", amount: "CNY 79.00", status: "Pending" },
  { id: "PAY-2203", method: "Credit card", amount: "CNY 510.00", status: "Failed" },
]

const notifications = [
  { source: "OrderLog", receiver: "nora@example.test", channel: "Email", status: "Sent" },
  { source: "ShipmentLog", receiver: "sam@example.test", channel: "SMS", status: "Pending" },
  { source: "System", receiver: "ops@example.test", channel: "Email", status: "Failed" },
]

const navItems = [
  "Dashboard",
  "Shops",
  "Categories",
  "Managers",
  "Customers",
  "Product approvals",
  "Orders",
  "Payments",
  "Notifications",
] as const

type AdminView = (typeof navItems)[number]
type Row = Record<string, string | number>

const getBadgeColor = (status: string) => {
  if (["Approved", "Active", "Confirmed", "Paid", "Completed", "Sent"].includes(status)) {
    return "green"
  }
  if (["Disabled", "Blocked", "Rejected", "Exception", "Failed"].includes(status)) {
    return "red"
  }
  if (["Needs check", "Review"].includes(status)) {
    return "purple"
  }
  return "orange"
}

const AdminPanel = () => {
  const [isSignedIn, setIsSignedIn] = useState(false)
  const [loginError, setLoginError] = useState("")
  const [activeView, setActiveView] = useState<AdminView>("Dashboard")
  const [query, setQuery] = useState("")

  const handleLogin = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()

    const formData = new FormData(event.currentTarget)
    const email = String(formData.get("email") || "").trim().toLowerCase()
    const password = String(formData.get("password") || "")

    if (email !== TEST_ADMIN_EMAIL || password !== TEST_ADMIN_PASSWORD) {
      setLoginError("Invalid admin email or password.")
      return
    }

    setLoginError("")
    setIsSignedIn(true)
  }

  const handleViewChange = (item: AdminView) => {
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
                Admin Panel
              </p>
              <h1 className="mt-2 text-xl-semi text-ui-fg-base">
                Sign in to continue
              </h1>
              <p className="mt-2 text-small-regular text-ui-fg-subtle">
                Platform administrators can review shops, manage categories,
                and monitor operational activity.
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
                Test account: {TEST_ADMIN_EMAIL}
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
            <span className="text-ui-fg-base">ADMIN PANEL</span>
            <span className="hidden text-ui-fg-muted small:inline">
              Platform operations
            </span>
          </div>
          <Button
            variant="secondary"
            className="h-9"
            onClick={() => setIsSignedIn(false)}
          >
            Sign out
          </Button>
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
          <AdminViewContent activeView={activeView} query={query} />
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
  activeView: AdminView
  query: string
  setQuery: (value: string) => void
}) => {
  const copy = {
    Dashboard: "Platform overview",
    Shops: "Shop management",
    Categories: "Category management",
    Managers: "Manager accounts",
    Customers: "Customer accounts",
    "Product approvals": "Product approval monitoring",
    Orders: "Order monitoring",
    Payments: "Payment monitoring",
    Notifications: "Notification logs",
  }[activeView]

  return (
    <section className="flex flex-col justify-between gap-4 border-b border-ui-border-base pb-8 small:flex-row small:items-end">
      <div>
        <p className="txt-xsmall-plus uppercase text-ui-fg-muted">
          {activeView}
        </p>
        <h1 className="mt-2 text-2xl-semi text-ui-fg-base">{copy}</h1>
        <p className="mt-2 max-w-2xl text-small-regular text-ui-fg-subtle">
          {getViewDescription(activeView)}
        </p>
      </div>
      {activeView === "Dashboard" ? (
        <Button variant="secondary" className="h-10 w-full small:w-auto">
          Review pending shops
        </Button>
      ) : (
        <div className="w-full small:w-72">
          <Input
            label={`Search ${activeView.toLowerCase()}`}
            name="admin-search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
        </div>
      )}
    </section>
  )
}

const AdminViewContent = ({
  activeView,
  query,
}: {
  activeView: AdminView
  query: string
}) => {
  if (activeView === "Dashboard") {
    return <DashboardView />
  }

  if (activeView === "Shops") {
    return (
      <TableView
        title="All shops"
        description="Review pending shops, inspect shop managers, and disable shops that violate platform policy."
        rows={shops}
        actions={<Button variant="secondary">Open pending shops</Button>}
        query={query}
      />
    )
  }

  if (activeView === "Categories") {
    return (
      <TableView
        title="Platform categories"
        description="Create, edit, and organize the shared category system used by shops."
        rows={categories}
        actions={<Button variant="secondary">Create category</Button>}
        query={query}
      />
    )
  }

  if (activeView === "Managers") {
    return (
      <TableView
        title="Managers"
        description="Monitor manager accounts and the shops they operate."
        rows={managers}
        actions={<Button variant="secondary">Review blocked accounts</Button>}
        query={query}
      />
    )
  }

  if (activeView === "Customers") {
    return (
      <TableView
        title="Customers"
        description="Inspect customer account status, order activity, and review history."
        rows={customers}
        actions={<Button variant="secondary">Review accounts</Button>}
        query={query}
      />
    )
  }

  if (activeView === "Product approvals") {
    return (
      <TableView
        title="Product approvals"
        description="Track products submitted by managers before they are listed in shops."
        rows={productApprovals}
        actions={<Button variant="secondary">View pending approvals</Button>}
        query={query}
      />
    )
  }

  if (activeView === "Orders") {
    return (
      <TableView
        title="Orders"
        description="Monitor order status, abnormal orders, payments, and fulfillment signals."
        rows={orders}
        actions={<Button variant="secondary">View exceptions</Button>}
        query={query}
      />
    )
  }

  if (activeView === "Payments") {
    return (
      <TableView
        title="Payments"
        description="Review payment status, methods, transactions, and failed activity."
        rows={payments}
        actions={<Button variant="secondary">View failed transactions</Button>}
        query={query}
      />
    )
  }

  return (
    <TableView
      title="Notifications"
      description="Inspect order, shipment, and system notifications triggered by domain logs."
      rows={notifications}
      actions={<Button variant="secondary">Retry failed</Button>}
      query={query}
    />
  )
}

const DashboardView = () => {
  return (
    <>
      <section className="grid grid-cols-1 gap-4 small:grid-cols-2 medium:grid-cols-4">
        {stats.map((stat) => (
          <div
            key={stat.label}
            className="rounded-rounded border border-ui-border-base bg-white p-5"
          >
            <p className="text-small-regular text-ui-fg-subtle">
              {stat.label}
            </p>
            <p className="mt-3 text-xl-semi text-ui-fg-base">{stat.value}</p>
            <p className="mt-1 text-small-regular text-ui-fg-muted">
              {stat.detail}
            </p>
          </div>
        ))}
      </section>

      <section className="grid grid-cols-1 gap-6 medium:grid-cols-[1fr_320px]">
        <TableView
          title="Review queue"
          description="Shops and product approval activity that needs attention."
          rows={productApprovals.filter((row) => row.status !== "Confirmed")}
          actions={<Badge color="orange">2 open</Badge>}
          query=""
          compact
        />
        <div className="flex flex-col gap-4">
          <InfoPanel title="Core responsibilities">
            <p>Review and manage shops</p>
            <p>Maintain shared categories</p>
            <p>Monitor users and accounts</p>
            <p>Inspect orders, payments, and notifications</p>
          </InfoPanel>
          <div className="rounded-rounded border border-ui-border-base bg-ui-bg-subtle p-5">
            <p className="txt-xsmall-plus uppercase text-ui-fg-muted">
              Product policy
            </p>
            <p className="mt-2 text-small-regular text-ui-fg-subtle">
              Managers submit product approvals. Admins monitor the flow and
              intervene on suspicious shops or categories.
            </p>
          </div>
        </div>
      </section>
    </>
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
                const isStatus = column === "status"
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

const getViewDescription = (view: AdminView) => {
  const descriptions: Record<AdminView, string> = {
    Dashboard:
      "Review shops, maintain platform categories, and monitor operational activity.",
    Shops:
      "Approve, reject, disable, and inspect shops without directly editing their products.",
    Categories:
      "Maintain the platform-wide category system used to organize products.",
    Managers:
      "Manage store operators and inspect the shops attached to their accounts.",
    Customers:
      "Review customer accounts, orders, and product review history.",
    "Product approvals":
      "Monitor manager-submitted products before they appear in a shop.",
    Orders:
      "Inspect order status, logs, shipments, payment signals, and exceptions.",
    Payments:
      "Monitor payments, methods, transactions, failures, and suspicious activity.",
    Notifications:
      "View notifications triggered by order logs, shipment logs, and system events.",
  }

  return descriptions[view]
}

const formatColumn = (column: string) =>
  column
    .replace(/([A-Z])/g, " $1")
    .replace(/^./, (letter) => letter.toUpperCase())

export default AdminPanel
