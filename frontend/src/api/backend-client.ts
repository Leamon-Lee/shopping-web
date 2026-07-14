/**
 * Client-safe API layer — for use in "use client" components.
 * Reads auth token and cart_id from cookies via document.cookie.
 */

import type {
  Account,
  Address,
  HallPayload,
  Order,
  PaginatedHallProducts,
  Product,
  Category,
  ShoppingCart,
  TokenResponse,
} from "types/backend"

const BACKEND_PROXY_URL = "/api/backend"
const DIRECT_BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8001"

function getClientToken(): string | null {
  if (typeof document === "undefined") return null
  const match = document.cookie.match(/(?:^|;\s*)shopping_token=([^;]*)/)
  return match ? match[1] : null
}

function getClientCartId(): string | null {
  if (typeof document === "undefined") return null
  const match = document.cookie.match(/(?:^|;\s*)shopping_cart_id=([^;]*)/)
  return match ? match[1] : null
}

export function saveCartIdCookie(cartId: string) {
  if (typeof document === "undefined") return
  document.cookie = `shopping_cart_id=${cartId};path=/;max-age=${60 * 60 * 24 * 7};SameSite=Lax`
}

async function clientFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getClientToken()
  const cartId = getClientCartId()
  const headers: Record<string, string> = {
    "content-type": "application/json",
    ...(init?.headers as Record<string, string> | undefined),
  }
  if (token) {
    headers["Authorization"] = `Bearer ${token}`
  }
  if (cartId) {
    headers["X-Cart-Id"] = cartId
  }

  const urls = [`${BACKEND_PROXY_URL}${path}`, `${DIRECT_BACKEND_URL}${path}`]
  let lastError: Error | null = null

  for (const url of urls) {
    try {
      const response = await fetch(url, {
        ...init,
        headers,
        cache: "no-store",
      })

      if (!response.ok) {
        let detail = ""
        try {
          const body = await response.json()
          detail =
            typeof body.detail === "string"
              ? body.detail
              : JSON.stringify(body.detail)
        } catch {
          // ignore parse errors
        }
        throw new Error(
          detail || `Backend request failed: ${response.status} ${path}`
        )
      }

      return response.json() as Promise<T>
    } catch (error) {
      lastError = error instanceof Error ? error : new Error(String(error))
    }
  }

  throw lastError ?? new Error(`Backend request failed: ${path}`)
}

// ── Public read endpoints ────────────────────────────────────────────

export async function listProducts(shop?: string, q?: string, limit?: number, offset?: number): Promise<Product[]> {
  const params = new URLSearchParams()
  if (shop) params.set("shop", shop)
  if (q) params.set("q", q)
  if (limit !== undefined) params.set("limit", String(limit))
  if (offset !== undefined) params.set("offset", String(offset))
  const query = params.toString() ? `?${params.toString()}` : ""
  return clientFetch<Product[]>(`/shop${query}`)
}

export async function searchProducts(q: string, limit?: number): Promise<Product[]> {
  const params = new URLSearchParams({ q })
  if (limit !== undefined) params.set("limit", String(limit))
  return clientFetch<Product[]>(`/shop/search?${params.toString()}`)
}

export async function getHall(): Promise<HallPayload> {
  return clientFetch<HallPayload>("/hall")
}

export async function getHallProducts(params?: {
  q?: string
  shop?: string
  category?: string
  limit?: number
  offset?: number
}): Promise<PaginatedHallProducts> {
  const sp = new URLSearchParams()
  if (params?.q) sp.set("q", params.q)
  if (params?.shop) sp.set("shop", params.shop)
  if (params?.category) sp.set("category", params.category)
  sp.set("limit", String(params?.limit ?? 24))
  sp.set("offset", String(params?.offset ?? 0))
  const qs = sp.toString()
  return clientFetch<PaginatedHallProducts>(`/hall/products${qs ? `?${qs}` : ""}`)
}

export async function getProduct(productName: string): Promise<Product> {
  return clientFetch<Product>(`/shop/${encodeURIComponent(productName)}`)
}

export async function listCategories(): Promise<Category[]> {
  return clientFetch<Category[]>("/shop/categories")
}

// ── Cart (works for both guest and authenticated) ────────────────────

export async function getCart(): Promise<ShoppingCart> {
  return clientFetch<ShoppingCart>("/cart")
}

export async function addCartItem(payload: { product_name: string; quantity: number }): Promise<ShoppingCart> {
  return clientFetch<ShoppingCart>("/cart/items", {
    method: "POST",
    body: JSON.stringify(payload),
  })
}

export async function updateCartItem(productName: string, quantity: number): Promise<ShoppingCart> {
  return clientFetch<ShoppingCart>(`/cart/items/${encodeURIComponent(productName)}`, {
    method: "PATCH",
    body: JSON.stringify({ quantity }),
  })
}

export async function deleteCartItem(productName: string): Promise<ShoppingCart> {
  return clientFetch<ShoppingCart>(`/cart/items/${encodeURIComponent(productName)}`, { method: "DELETE" })
}

// ── Checkout ─────────────────────────────────────────────────────────

export async function setCartAddresses(payload: Record<string, unknown>): Promise<ShoppingCart> {
  return clientFetch<ShoppingCart>("/cart/addresses", {
    method: "PATCH",
    body: JSON.stringify(payload),
  })
}

export async function getCartShippingOptions(): Promise<Record<string, unknown>[]> {
  return clientFetch<Record<string, unknown>[]>("/cart/shipping-options")
}

export async function setCartShippingMethod(shippingMethodId: string): Promise<ShoppingCart> {
  return clientFetch<ShoppingCart>("/cart/shipping-method", {
    method: "PATCH",
    body: JSON.stringify({ shipping_method_id: shippingMethodId }),
  })
}

export async function createCartPaymentSession(providerId?: string): Promise<ShoppingCart> {
  return clientFetch<ShoppingCart>("/cart/payment-session", {
    method: "POST",
    body: JSON.stringify({ provider_id: providerId || "pp_system_default" }),
  })
}

// ── Orders (requires auth) ──────────────────────────────────────────

export async function placeOrder(payload: Record<string, unknown> = {}): Promise<Order> {
  return clientFetch<Order>("/orders", { method: "POST", body: JSON.stringify(payload) })
}

export async function listOrders(): Promise<Order[]> {
  return clientFetch<Order[]>("/orders")
}

export async function getOrder(orderNumber: string): Promise<Order> {
  return clientFetch<Order>(`/orders/${encodeURIComponent(orderNumber)}`)
}

// ── Payment ──────────────────────────────────────────────────────────

export async function processPayment(payload: {
  order_id: string
  card_number: string
  amount: number
  currency?: string
  access_token?: string
}): Promise<Record<string, unknown>> {
  return clientFetch<Record<string, unknown>>("/payments/process", {
    method: "POST",
    body: JSON.stringify(payload),
  })
}

// ── Panel dashboards (requires auth) ────────────────────────────────

export async function getAdminPanel(): Promise<Record<string, unknown>> {
  return clientFetch<Record<string, unknown>>("/admin")
}

export async function getAdminUsers(): Promise<{ users: Record<string, unknown>[]; total: number }> {
  return clientFetch("/admin/users")
}

export async function getAdminProducts(): Promise<{ products: Record<string, unknown>[]; total: number }> {
  return clientFetch("/admin/products")
}

export async function getAdminOrders(): Promise<{ orders: Record<string, unknown>[]; total: number }> {
  return clientFetch("/admin/orders")
}

export async function getManagerPanel(): Promise<Record<string, unknown>> {
  return clientFetch<Record<string, unknown>>("/manager")
}

export async function getManagerProducts(): Promise<{ products: Record<string, unknown>[]; total: number }> {
  return clientFetch("/manager/products")
}

export async function getManagerOrders(): Promise<{ orders: Record<string, unknown>[]; total: number }> {
  return clientFetch("/manager/orders")
}

export async function getCustomerPanel(): Promise<Record<string, unknown>> {
  return clientFetch<Record<string, unknown>>("/customer")
}

// ── Auth ────────────────────────────────────────────────────────────

export async function loginRequest(payload: { email: string; password: string }): Promise<TokenResponse> {
  return clientFetch<TokenResponse>("/accounts/login", {
    method: "POST",
    body: JSON.stringify(payload),
  })
}

export async function getCurrentUser(): Promise<Account | null> {
  try {
    return await clientFetch<Account>("/accounts/me")
  } catch {
    return null
  }
}

// ── Manager operations ─────────────────────────────────────────────

export async function getManagerShops(): Promise<{ shops: Record<string, unknown>[] }> {
  return clientFetch("/manager/shops")
}

export async function createManagerShop(payload: { name: string; description?: string; category?: string }): Promise<Record<string, unknown>> {
  return clientFetch("/manager/shops", { method: "POST", body: JSON.stringify(payload) })
}

export async function createManagerProduct(payload: { shop_id: string; name: string; price: number; description?: string; available_item_count?: number }): Promise<Record<string, unknown>> {
  return clientFetch("/manager/products", { method: "POST", body: JSON.stringify(payload) })
}

export async function updateManagerProduct(productId: string, payload: { name?: string; price?: number; available_item_count?: number; status?: string }): Promise<Record<string, unknown>> {
  return clientFetch(`/manager/products/${productId}`, { method: "PATCH", body: JSON.stringify(payload) })
}

export async function updateManagerInventory(variantId: string, inventory_count: number): Promise<Record<string, unknown>> {
  return clientFetch(`/manager/inventory/${variantId}`, { method: "PATCH", body: JSON.stringify({ inventory_count }) })
}

export async function createManagerShipment(orderNumber: string, payload: { carrier?: string; tracking_number?: string; tracking_url?: string }): Promise<Record<string, unknown>> {
  return clientFetch(`/manager/orders/${orderNumber}/shipments`, { method: "POST", body: JSON.stringify(payload) })
}

export async function updateManagerOrderStatus(orderNumber: string, status: string): Promise<Record<string, unknown>> {
  return clientFetch(`/manager/orders/${orderNumber}/status`, { method: "PATCH", body: JSON.stringify({ status }) })
}

export async function getManagerIncome(): Promise<Record<string, unknown>> {
  return clientFetch("/manager/income")
}

export async function getManagerReports(): Promise<Record<string, unknown>> {
  return clientFetch("/manager/reports")
}

export async function getManagerShipments(): Promise<{ shipments: Record<string, unknown>[] }> {
  return clientFetch("/manager/shipments")
}

// ── Admin operations ───────────────────────────────────────────────

export async function getAdminShops(statusFilter?: string): Promise<{ shops: Record<string, unknown>[] }> {
  const qs = statusFilter ? `?status_filter=${statusFilter}` : ""
  return clientFetch(`/admin/shops${qs}`)
}

export async function approveShop(shopId: string, status: string): Promise<Record<string, unknown>> {
  return clientFetch(`/admin/shops/${shopId}/approval`, { method: "PATCH", body: JSON.stringify({ status }) })
}

export async function updateUserStatus(userId: string, status: string): Promise<Record<string, unknown>> {
  return clientFetch(`/admin/users/${userId}/status`, { method: "PATCH", body: JSON.stringify({ status }) })
}

export async function updateUserRole(userId: string, role: string): Promise<Record<string, unknown>> {
  return clientFetch(`/admin/users/${userId}/role`, { method: "PATCH", body: JSON.stringify({ role }) })
}

export async function updateProductStatus(productId: string, status: string): Promise<Record<string, unknown>> {
  return clientFetch(`/admin/products/${productId}/status`, { method: "PATCH", body: JSON.stringify({ status }) })
}

export async function getAdminCategories(): Promise<{ categories: Record<string, unknown>[] }> {
  return clientFetch("/admin/categories")
}

export async function createAdminCategory(payload: { name: string; description: string }): Promise<Record<string, unknown>> {
  return clientFetch("/admin/categories", { method: "POST", body: JSON.stringify(payload) })
}

export async function updateAdminCategory(categoryId: string, payload: { name: string; description: string }): Promise<Record<string, unknown>> {
  return clientFetch(`/admin/categories/${categoryId}`, { method: "PATCH", body: JSON.stringify(payload) })
}

export async function deleteAdminCategory(categoryId: string): Promise<Record<string, unknown>> {
  return clientFetch(`/admin/categories/${categoryId}`, { method: "DELETE" })
}

// ── Recommendations ────────────────────────────────────────────────

type RecItem = {
  product: Record<string, unknown>
  score: number | null
  reason: string
  algorithm: string
}

type RecResponse = {
  scene: string
  count: number
  items: RecItem[]
}

export async function getHomeRecommendations(): Promise<RecResponse> {
  return clientFetch<RecResponse>("/recommendations/home")
}

export async function getCartRecommendations(): Promise<RecResponse> {
  return clientFetch<RecResponse>("/recommendations/cart")
}

export async function getSimilarProducts(productId: string): Promise<RecResponse> {
  return clientFetch<RecResponse>(`/recommendations/products/${encodeURIComponent(productId)}/similar`)
}

export async function getUserRecommendations(username: string): Promise<RecResponse> {
  return clientFetch<RecResponse>(`/recommendations/users/${encodeURIComponent(username)}`)
}
