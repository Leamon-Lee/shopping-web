import { retrieveOrder } from "@lib/data/orders"
import { getOrder as getBackendOrder } from "../../../../../../api/backend"
import OrderCompletedTemplate from "@modules/order/templates/order-completed-template"
import { Metadata } from "next"
import { notFound } from "next/navigation"

type Props = {
  params: Promise<{ id: string }>
  searchParams: Promise<{ token?: string }>
}

export const metadata: Metadata = {
  title: "Order Confirmed",
  description: "Your purchase was successful",
}

export default async function OrderConfirmedPage(props: Props) {
  const params = await props.params
  const searchParams = await props.searchParams
  const token = searchParams.token

  // For guest orders, pass the access token
  let order
  try {
    if (token) {
      // Direct API call with token query param
      const url = `${process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8001"}/orders/${encodeURIComponent(params.id)}?token=${encodeURIComponent(token)}`
      const res = await fetch(url, { cache: "no-store" })
      if (res.ok) order = await res.json()
    } else {
      order = await retrieveOrder(params.id).catch(() => null)
    }
  } catch {
    order = null
  }

  if (!order) {
    return notFound()
  }

  return <OrderCompletedTemplate order={order} />
}
