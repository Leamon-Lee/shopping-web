import { Metadata } from "next"
import { notFound, redirect } from "next/navigation"
import { cookies } from "next/headers"
import { getCart } from "../../../api/backend"
import { retrieveCustomer } from "@lib/data/customer"
import OrderConfirmation from "@modules/checkout/templates/order-confirmation"

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

export default async function CheckoutPage() {
  const cart = await getCart()
  if (!cart || !cart.items?.length) return notFound()

  // Filter cart items by selected items from cookie
  const store = await cookies()
  const selectedRaw = store.get("checkout_items")?.value
  if (selectedRaw) {
    const selectedNames = selectedRaw.split("|").map((s) => s.toLowerCase())
    cart.items = (cart.items || []).filter((item: any) =>
      selectedNames.includes((item.product_title || item.product?.name || "").toLowerCase())
    )
    if (!cart.items.length) return notFound()
  }

  // Recalculate totals based on filtered items
  cart.subtotal = (cart.items || []).reduce(
    (sum: number, item: any) => sum + (item.unit_price || item.price || 0) * (item.quantity || 1), 0
  )
  cart.total = cart.subtotal

  const customer = await retrieveCustomer()
  if (!customer) redirect("/auth/login?redirect=/checkout")

  const [addresses, paymentMethods] = await Promise.all([
    authFetch<any[]>("/accounts/me/addresses").catch(() => []),
    authFetch<any[]>("/accounts/me/payment-methods").catch(() => []),
  ])

  async function addAddressAction(formData: FormData) {
    "use server"
    const payload: Record<string, any> = {}; formData.forEach((v, k) => { payload[k] = v })
    payload.is_default_shipping = payload.is_default_shipping === "true"
    return authFetch<any[]>("/accounts/me/addresses", { method: "POST", body: JSON.stringify(payload) })
  }
  async function updateAddressAction(addressId: string, formData: FormData) {
    "use server"
    const payload: Record<string, any> = {}; formData.forEach((v, k) => { payload[k] = v })
    payload.is_default_shipping = payload.is_default_shipping === "true"
    return authFetch<any[]>(`/accounts/me/addresses/${addressId}`, { method: "PUT", body: JSON.stringify(payload) })
  }
  async function addPaymentMethodAction(label: string) {
    "use server"
    return authFetch<any[]>("/accounts/me/payment-methods", { method: "POST", body: JSON.stringify({ label, method_type: "credit_card" }) })
  }
  async function placeOrderAction(items: Array<{ product_name: string; quantity: number }>, subtotal: number) {
    "use server"
    return authFetch<any>("/orders", { method: "POST", body: JSON.stringify({ items, payment: { amount: subtotal, currency: "CNY" } }) })
  }

  return (
    <div className="py-12">
      <div className="content-container">
        <h1 className="text-[2rem] leading-[2.75rem] mb-8">Order Confirmation</h1>
        <OrderConfirmation
          cart={cart} customer={customer} addresses={addresses} paymentMethods={paymentMethods}
          addAddressAction={addAddressAction} updateAddressAction={updateAddressAction}
          addPaymentMethodAction={addPaymentMethodAction} placeOrderAction={placeOrderAction}
        />
      </div>
    </div>
  )
}
