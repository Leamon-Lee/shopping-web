import CustomerPanel from "@modules/customer/templates/customer-panel"
import { getCart, listOrders, listProducts } from "../../../api/backend"
import { retrieveCustomer } from "@lib/data/customer"
import { cookies } from "next/headers"
import { Metadata } from "next"

export const metadata: Metadata = {
  title: "Customer Panel",
  description: "Customer dashboard and shopping tools.",
}

export const dynamic = "force-dynamic"

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8001"
const TOKEN_COOKIE = "shopping_token"

async function authFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const store = await cookies()
  const token = store.get(TOKEN_COOKIE)?.value
  const headers: Record<string, string> = {
    "content-type": "application/json",
    ...(init?.headers as Record<string, string> | undefined),
  }
  if (token) headers["Authorization"] = `Bearer ${token}`
  const res = await fetch(`${BACKEND_URL}${path}`, { ...init, headers, cache: "no-store" })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail || `Request failed: ${res.status}`)
  }
  return res.json()
}

export default async function CustomerPage(props: {
  params: Promise<{ username: string }>
}) {
  await props.params

  const customer = await retrieveCustomer()
  const [cart, orders, products, addresses, paymentMethods] = await Promise.all([
    getCart().catch(() => null),
    listOrders().catch(() => []),
    listProducts().catch(() => []),
    authFetch<any[]>("/accounts/me/addresses").catch(() => []),
    authFetch<any[]>("/accounts/me/payment-methods").catch(() => []),
  ])
  const { reviews = [] } = await authFetch<{ reviews: any[] }>("/accounts/me/reviews").catch(() => ({ reviews: [] }))
  async function deleteReviewAction(id: string) { "use server"; return authFetch<any>(`/accounts/me/reviews/${id}`, { method: "DELETE" }) }

  async function completeOrderAction(orderNumber: string) {
    "use server"
    return authFetch<any>(`/orders/${orderNumber}/complete`, { method: "PATCH" })
  }
  async function deleteOrderAction(orderNumber: string) {
    "use server"
    return authFetch<any>(`/orders/${orderNumber}`, { method: "DELETE" })
  }
  async function addAddressAction(formData: FormData) {
    "use server"
    const p: any = {}; formData.forEach((v, k) => { p[k] = v }); p.is_default_shipping = p.is_default_shipping === "true"
    return authFetch<any[]>("/accounts/me/addresses", { method: "POST", body: JSON.stringify(p) })
  }
  async function updateAddressAction(addressId: string, formData: FormData) {
    "use server"
    const p: any = {}; formData.forEach((v, k) => { p[k] = v }); p.is_default_shipping = p.is_default_shipping === "true"
    return authFetch<any[]>(`/accounts/me/addresses/${addressId}`, { method: "PUT", body: JSON.stringify(p) })
  }
  async function deleteAddressAction(addressId: string) {
    "use server"
    return authFetch<any[]>(`/accounts/me/addresses/${addressId}`, { method: "DELETE" })
  }
  async function addPaymentMethodAction(label: string) {
    "use server"
    return authFetch<any[]>("/accounts/me/payment-methods", { method: "POST", body: JSON.stringify({ label, method_type: "credit_card" }) })
  }
  async function deletePaymentMethodAction(pmId: string) {
    "use server"
    return authFetch<any[]>(`/accounts/me/payment-methods/${pmId}`, { method: "DELETE" })
  }

  return (
    <CustomerPanel
      cart={cart} orders={orders} products={products} addresses={addresses} paymentMethods={paymentMethods} reviewsCount={reviews.length} customer={customer}
      completeOrderAction={completeOrderAction} deleteOrderAction={deleteOrderAction}
      addAddressAction={addAddressAction} updateAddressAction={updateAddressAction} deleteAddressAction={deleteAddressAction}
      addPaymentMethodAction={addPaymentMethodAction} deletePaymentMethodAction={deletePaymentMethodAction}
      reviewsCount={reviews.length} reviews={reviews} deleteReviewAction={deleteReviewAction}
    />
  )
}
