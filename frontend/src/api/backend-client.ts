/**
 * Client-safe API layer — for use in "use client" components.
 * Reads auth token from cookies via document.cookie.
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

async function clientFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getClientToken()
  const headers: Record<string, string> = {
    "content-type": "application/json",
    ...(init?.headers as Record<string, string> | undefined),
  }
  if (token) {
    headers["Authorization"] = `Bearer ${token}`
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
