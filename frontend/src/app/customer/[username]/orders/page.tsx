import { Metadata } from "next"
import { notFound } from "next/navigation"
import { listOrders } from "../../../../api/backend"
import { retrieveCustomer } from "@lib/data/customer"
import { formatBackendMoney } from "../../../../lib/backend-native"
import LocalizedClientLink from "@modules/common/components/localized-client-link"

export const dynamic = "force-dynamic"

type Props = { params: Promise<{ username: string }> }

export async function generateMetadata(props: Props): Promise<Metadata> {
  return { title: "Orders | Shopping Web" }
}

export default async function OrdersPage(props: Props) {
  const { username } = await props.params
  const customer = await retrieveCustomer()

  if (!customer) {
    return notFound()
  }

  let orders: any[] = []
  try {
    orders = await listOrders()
  } catch {
    orders = []
  }

  return (
    <div className="py-12">
      <div className="content-container">
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-[2rem] leading-[2.75rem]">My Orders</h1>
          <LocalizedClientLink
            href={`/customer/${encodeURIComponent(username)}/hall`}
            className="text-small-regular text-ui-fg-muted hover:text-ui-fg-base"
          >
            Back to Hall
          </LocalizedClientLink>
        </div>

        {orders.length === 0 ? (
          <div className="bg-white py-12 text-center">
            <p className="text-base-regular text-ui-fg-muted">No orders yet</p>
            <LocalizedClientLink
              href="/hall"
              className="text-small-regular text-blue-600 hover:text-blue-800 mt-2 inline-block"
            >
              Start shopping
            </LocalizedClientLink>
          </div>
        ) : (
          <div className="flex flex-col gap-y-4">
            {orders.map((order: any) => (
              <div key={order.order_number} className="bg-white border border-ui-border-base rounded-lg p-6">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <p className="text-base-regular font-medium">Order #{order.order_number}</p>
                    <p className="text-small-regular text-ui-fg-muted">
                      {order.order_date ? new Date(order.order_date).toLocaleDateString() : "Just now"} · {order.status}
                    </p>
                  </div>
                  <p className="text-xl-semi">
                    {order.payment ? formatBackendMoney(order.payment.amount || 0) : "—"}
                  </p>
                </div>
                {order.items && (
                  <ul className="border-t border-ui-border-base pt-3">
                    {order.items.slice(0, 3).map((item: any, i: number) => (
                      <li key={i} className="flex justify-between py-1 text-small-regular">
                        <span>{item.product_title || item.product_name || "Item"}</span>
                        <span className="text-ui-fg-muted">x{item.quantity}</span>
                      </li>
                    ))}
                    {order.items.length > 3 && (
                      <li className="text-small-regular text-ui-fg-muted py-1">
                        ...and {order.items.length - 3} more items
                      </li>
                    )}
                  </ul>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
