import CustomerPanel from "@modules/customer/templates/customer-panel"
import { getCart, getUserPreferenceProfile, listOrders, listProducts } from "../../api/backend"
import { retrieveCustomer } from "@lib/data/customer"
import { cookies } from "next/headers"
import { Metadata } from "next"

export const dynamic = "force-dynamic"

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8001"
const TOKEN_COOKIE = "shopping_token"

async function authFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const store = await cookies()
  const token = store.get(TOKEN_COOKIE)?.value
  const headers: Record<string, string> = { "content-type": "application/json", ...(init?.headers as any) }
  if (token) headers["Authorization"] = `Bearer ${token}`
  const res = await fetch(`${BACKEND_URL}${path}`, { ...init, headers, cache: "no-store" })
  if (!res.ok) { const body = await res.json().catch(() => ({})); throw new Error(body.detail || `Request failed: ${res.status}`) }
  return res.json()
}

export default async function CustomerPage() {
  const customer = await retrieveCustomer()
  const userKey = customer?.email || customer?.user_name || ""
  const [cart, orders, products, addresses, paymentMethods, reviewsData, preferenceProfile] = await Promise.all([
    getCart().catch(() => null), listOrders().catch(() => []), listProducts().catch(() => []),
    authFetch<any[]>("/accounts/me/addresses").catch(() => []),
    authFetch<any[]>("/accounts/me/payment-methods").catch(() => []),
    authFetch<{ reviews: any[] }>("/accounts/me/reviews").catch(() => ({ reviews: [] })),
    userKey ? getUserPreferenceProfile(userKey).catch(() => null) : Promise.resolve(null),
  ])
  const reviewCount = reviewsData?.reviews?.length || 0
  const reviews = reviewsData?.reviews || []
  async function deleteReviewAction(id: string) { "use server"; return authFetch<any>(`/accounts/me/reviews/${id}`, { method: "DELETE" }) }

  async function completeOrderAction(o: string) { "use server"; return authFetch<any>(`/orders/${o}/complete`, { method: "PATCH" }) }
  async function deleteOrderAction(o: string) { "use server"; return authFetch<any>(`/orders/${o}`, { method: "DELETE" }) }
  async function addAddressAction(fd: FormData) { "use server"; const p: any = {}; fd.forEach((v,k) => { p[k]=v }); p.is_default_shipping=p.is_default_shipping==="true"; return authFetch<any[]>("/accounts/me/addresses", { method: "POST", body: JSON.stringify(p) }) }
  async function updateAddressAction(id: string, fd: FormData) { "use server"; const p: any = {}; fd.forEach((v,k) => { p[k]=v }); p.is_default_shipping=p.is_default_shipping==="true"; return authFetch<any[]>(`/accounts/me/addresses/${id}`, { method: "PUT", body: JSON.stringify(p) }) }
  async function deleteAddressAction(id: string) { "use server"; return authFetch<any[]>(`/accounts/me/addresses/${id}`, { method: "DELETE" }) }
  async function addPaymentMethodAction(label: string) { "use server"; return authFetch<any[]>("/accounts/me/payment-methods", { method: "POST", body: JSON.stringify({ label, method_type: "credit_card" }) }) }
  async function deletePaymentMethodAction(id: string) { "use server"; return authFetch<any[]>(`/accounts/me/payment-methods/${id}`, { method: "DELETE" }) }

  return <CustomerPanel
    cart={cart} orders={orders} products={products} addresses={addresses} paymentMethods={paymentMethods} reviewsCount={reviewCount} customer={customer}
    completeOrderAction={completeOrderAction} deleteOrderAction={deleteOrderAction}
    addAddressAction={addAddressAction} updateAddressAction={updateAddressAction} deleteAddressAction={deleteAddressAction}
    addPaymentMethodAction={addPaymentMethodAction} deletePaymentMethodAction={deletePaymentMethodAction}
    preferenceProfile={preferenceProfile}
    reviews={reviews} deleteReviewAction={deleteReviewAction} />
}
