import CustomerPanel from "@modules/customer/templates/customer-panel"
import { getCart, listOrders, listProducts } from "../../api/backend"
import { Metadata } from "next"

export const metadata: Metadata = {
  title: "My Account",
  description: "Customer account center.",
}

export default async function CustomerPage() {
  const [cart, orders, products] = await Promise.all([
    getCart().catch(() => null),
    listOrders().catch(() => []),
    listProducts(undefined, undefined, 8).catch(() => []),
  ])

  return <CustomerPanel cart={cart} orders={orders} products={products} />
}
