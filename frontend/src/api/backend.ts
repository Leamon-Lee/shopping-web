import { cookies } from "next/headers"
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

const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8001"

const TOKEN_COOKIE = "shopping_token"

async function getAuthHeaders(): Promise<Record<string, string>> {
  const headers: Record<string, string> = {
    "content-type": "application/json",
  }
  try {
    const cookieStore = await cookies()
    const token = cookieStore.get(TOKEN_COOKIE)?.value
    if (token) {
      headers["Authorization"] = `Bearer ${token}`
    }
  } catch {
    // cookies() throws outside of server context — skip auth
  }
  return headers
}

async function backendFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = await getAuthHeaders()
  const url = `${BACKEND_URL}${path}`
  console.log('[backendFetch] Requesting:', url)   // 打印请求 URL

  try {
    const response = await fetch(url, {
      ...init,
      headers: {
        ...headers,
        ...(init?.headers ?? {}),
      },
      // 临时注释掉 cache: "no-store"，排除缓存策略干扰
      // cache: "no-store",
    })

    if (!response.ok) {
      let detail = ""
      try {
        const body = await response.json()
        detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail)
      } catch {
        // ignore parse errors
      }
      throw new Error(detail || `Backend request failed: ${response.status} ${path}`)
    }

    return response.json() as Promise<T>
  } catch (error) {
    // 详细打印错误信息，包括 cause（底层网络错误）
    console.error('❌ backendFetch failed for URL:', url)
    console.error('Error object:', error)
    if (error.cause) {
      console.error('Error cause:', error.cause)
    }
    // 重新抛出，让上层处理
    throw error
  }
}

// ── Regions ──────────────────────────────────────────────────────────

export async function listRegions() {
  return backendFetch<Record<string, unknown>[]>("/regions")
}

export async function getRegion(regionId: string) {
  return backendFetch<Record<string, unknown>>(`/regions/${regionId}`)
}

// ── Products ─────────────────────────────────────────────────────────

export async function listProducts(shop?: string, q?: string, limit?: number, offset?: number): Promise<Product[]> {
  const params = new URLSearchParams()
  if (shop) params.set("shop", shop)
  if (q) params.set("q", q)
  if (limit !== undefined) params.set("limit", String(limit))
  if (offset !== undefined) params.set("offset", String(offset))
  const query = params.toString() ? `?${params.toString()}` : ""
  return backendFetch<Product[]>(`/shop${query}`)
}

export async function searchProducts(q: string, limit?: number): Promise<Product[]> {
  const params = new URLSearchParams({ q })
  if (limit !== undefined) params.set("limit", String(limit))
  return backendFetch<Product[]>(`/shop/search?${params.toString()}`)
}

export async function getHall(): Promise<HallPayload> {
  return backendFetch<HallPayload>("/hall")
}

export async function getHallProducts(params?: {
  q?: string
  shop?: string
  category?: string
  limit?: number
  offset?: number
}): Promise<PaginatedHallProducts> {
  const searchParams = new URLSearchParams()
  if (params?.q) searchParams.set("q", params.q)
  if (params?.shop) searchParams.set("shop", params.shop)
  if (params?.category) searchParams.set("category", params.category)
  if (params?.limit !== undefined) searchParams.set("limit", String(params.limit))
  if (params?.offset !== undefined) searchParams.set("offset", String(params.offset))
  const query = searchParams.toString() ? `?${searchParams.toString()}` : ""
  return backendFetch<PaginatedHallProducts>(`/hall/products${query}`)
}

export async function getProduct(productName: string): Promise<Product> {
  return backendFetch<Product>(`/shop/${encodeURIComponent(productName)}`)
}

export async function createProduct(payload: {
  name: string
  description: string
  price: number
  available_item_count: number
  category: { name: string; description: string }
}): Promise<Product> {
  return backendFetch<Product>("/shop", {
    method: "POST",
    body: JSON.stringify(payload),
  })
}

export async function listCategories(): Promise<Category[]> {
  return backendFetch<Category[]>("/shop/categories")
}

// ── Cart ─────────────────────────────────────────────────────────────

export async function getCart(): Promise<ShoppingCart> {
  return backendFetch<ShoppingCart>("/cart")
}

export async function addCartItem(payload: {
  product_name: string
  quantity: number
}): Promise<ShoppingCart> {
  return backendFetch<ShoppingCart>("/cart/items", {
    method: "POST",
    body: JSON.stringify(payload),
  })
}

export async function updateCartItem(
  productName: string,
  quantity: number
): Promise<ShoppingCart> {
  return backendFetch<ShoppingCart>(
    `/cart/items/${encodeURIComponent(productName)}`,
    {
      method: "PATCH",
      body: JSON.stringify({ quantity }),
    }
  )
}

export async function deleteCartItem(productName: string): Promise<ShoppingCart> {
  return backendFetch<ShoppingCart>(
    `/cart/items/${encodeURIComponent(productName)}`,
    { method: "DELETE" }
  )
}

// ── Orders ───────────────────────────────────────────────────────────

export async function placeOrder(payload: {
  order_number?: string
  items?: Array<{ product_name: string; quantity: number }>
  payment?: { amount: number; currency: string }
} = {}): Promise<Order> {
  return backendFetch<Order>("/orders", {
    method: "POST",
    body: JSON.stringify(payload),
  })
}

export async function listOrders(): Promise<Order[]> {
  return backendFetch<Order[]>("/orders")
}

export async function getOrder(orderNumber: string): Promise<Order> {
  return backendFetch<Order>(`/orders/${encodeURIComponent(orderNumber)}`)
}

// ── Auth ─────────────────────────────────────────────────────────────

export async function login(payload: {
  email: string
  password: string
}): Promise<TokenResponse> {
  return backendFetch<TokenResponse>("/accounts/login", {
    method: "POST",
    body: JSON.stringify(payload),
  })
}

export async function registerAccount(payload: Record<string, unknown>): Promise<Account> {
  return backendFetch<Account>("/accounts/register", {
    method: "POST",
    body: JSON.stringify(payload),
  })
}

export async function retrieveCustomer(): Promise<Account> {
  return backendFetch<Account>("/accounts/me")
}

export async function updateCustomer(payload: Record<string, unknown>): Promise<Account> {
  return backendFetch<Account>("/accounts/me", {
    method: "PUT",
    body: JSON.stringify(payload),
  })
}

export async function listCustomerAddresses(): Promise<Address[]> {
  return backendFetch<Address[]>("/accounts/me/addresses")
}

export async function addCustomerAddress(payload: {
  street: string
  city: string
  state?: string
  postal_code?: string
  country?: string
  is_default_shipping?: boolean
}): Promise<Address[]> {
  return backendFetch<Address[]>("/accounts/me/addresses", {
    method: "POST",
    body: JSON.stringify(payload),
  })
}

export async function updateCustomerAddress(
  addressId: string,
  payload: Record<string, unknown>
): Promise<Address[]> {
  return backendFetch<Address[]>(`/accounts/me/addresses/${addressId}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  })
}

export async function deleteCustomerAddress(addressId: string): Promise<Address[]> {
  return backendFetch<Address[]>(`/accounts/me/addresses/${addressId}`, {
    method: "DELETE",
  })
}

// ── Panel dashboards ─────────────────────────────────────────────────

export async function getAdminPanel(): Promise<Record<string, unknown>> {
  return backendFetch<Record<string, unknown>>("/admin")
}

export async function getManagerPanel(): Promise<Record<string, unknown>> {
  return backendFetch<Record<string, unknown>>("/manager")
}

export async function getCustomerPanel(): Promise<Record<string, unknown>> {
  return backendFetch<Record<string, unknown>>("/customer")
}