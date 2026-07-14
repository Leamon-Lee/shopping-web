import CustomerPanel from "@modules/customer/templates/customer-panel"
import { getCartForUsername, listOrders } from "../../../api/backend"
import { Metadata } from "next"

export const metadata: Metadata = {
  title: "My Account",
  description: "Customer account center.",
}

export const dynamic = "force-dynamic"

export default async function CustomerPage(props: {
  params: Promise<{ username: string }>
}) {
  const { username } = await props.params
  const [cart, orders] = await Promise.all([
    getCartForUsername(username).catch(() => null),
    listOrders().catch(() => []),
  ])

  return (
    <CustomerPanel
      username={username}
      cart={cart}
      orders={orders}
      products={[]}
    />
  )
}
