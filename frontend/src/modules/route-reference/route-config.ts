export function customerLinks(username: string) {
  const base = `/customer/${username}`
  return [
    { href: `${base}/hall`, label: "Hall" },
    { href: `${base}/profile`, label: "Profile" },
    { href: `${base}/cart`, label: "Cart" },
    { href: `${base}/orders`, label: "Orders" },
    { href: `${base}/payment`, label: "Payment" },
    { href: `${base}/wishlist`, label: "Wishlist" },
    { href: `${base}/reviews`, label: "Reviews" },
    { href: `${base}/settings`, label: "Settings" },
  ]
}

export function managerLinks(username: string) {
  const base = `/manager/${username}`
  return [
    { href: `${base}/dashboard`, label: "Dashboard" },
    { href: `${base}/shop/apply`, label: "Apply for shop" },
    { href: `${base}/shop`, label: "Shop" },
    { href: `${base}/products`, label: "Products" },
    { href: `${base}/products/create`, label: "Create product" },
    { href: `${base}/orders`, label: "Orders" },
    { href: `${base}/analytics`, label: "Analytics" },
    { href: `${base}/income`, label: "Income" },
    { href: `${base}/settings`, label: "Settings" },
  ]
}

export function adminLinks(username: string) {
  const base = `/admin/${username}`
  return [
    { href: `${base}/dashboard`, label: "Dashboard" },
    { href: `${base}/shops`, label: "Shops" },
    { href: `${base}/shops/pending`, label: "Pending shops" },
    { href: `${base}/products`, label: "Products" },
    { href: `${base}/products/pending`, label: "Pending products" },
    { href: `${base}/users`, label: "Users" },
    { href: `${base}/categories`, label: "Categories" },
    { href: `${base}/reports`, label: "Reports" },
    { href: `${base}/settings`, label: "Settings" },
  ]
}

export const customerStats = [
  { label: "Cart items", value: "3", detail: "Across 2 shops" },
  { label: "Active orders", value: "4", detail: "2 shipments in transit" },
  { label: "Wishlist", value: "12", detail: "Saved products" },
  { label: "Reviews", value: "5", detail: "Pending review" },
]

export const managerStats = [
  { label: "Shops", value: "3", detail: "2 active" },
  { label: "Products", value: "248", detail: "14 low stock" },
  { label: "Orders", value: "37", detail: "Today" },
  { label: "Income", value: "CNY 82,460", detail: "Monthly net" },
]

export const adminStats = [
  { label: "Shops", value: "128", detail: "12 pending" },
  { label: "Products", value: "301", detail: "Live catalog" },
  { label: "Users", value: "4,812", detail: "All roles" },
  { label: "Reports", value: "9", detail: "Open review" },
]

export function titleFromSegment(segment: string) {
  return segment
    .split("/")
    .filter(Boolean)
    .map((part) =>
      part
        .replace(/-/g, " ")
        .replace(/^./, (letter) => letter.toUpperCase())
    )
    .join(" / ")
}
