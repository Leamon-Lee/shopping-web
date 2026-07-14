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
const CART_ID_COOKIE = "shopping_cart_id"

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
    // Send cart_id for guest cart isolation
    const cartId = cookieStore.get(CART_ID_COOKIE)?.value
    if (cartId) {
      headers["X-Cart-Id"] = cartId
    }
  } catch {
    // cookies() throws outside of server context — skip auth
  }
  return headers
}

async function backendFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = await getAuthHeaders()
  const response = await fetch(`${BACKEND_URL}${path}`, {
    ...init,
    headers: {
      ...headers,
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
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

export async function getCartForUsername(username: string): Promise<ShoppingCart> {
  return backendFetch<ShoppingCart>("/cart", {
    headers: {
      "X-Cart-Owner": decodeURIComponent(username),
    },
  })
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

export async function deleteCartItem(
  productName: string,
  username?: string
): Promise<ShoppingCart> {
  const headers = username
    ? { "X-Cart-Owner": decodeURIComponent(username) }
    : undefined
  return backendFetch<ShoppingCart>(
    `/cart/items/${encodeURIComponent(productName)}`,
    { method: "DELETE", headers }
  )
}

// ── Checkout ─────────────────────────────────────────────────────────

export async function setCartAddresses(payload: Record<string, unknown>): Promise<ShoppingCart> {
  return backendFetch<ShoppingCart>("/cart/addresses", {
    method: "PATCH",
    body: JSON.stringify(payload),
  })
}

export async function setCartEmail(email: string): Promise<ShoppingCart> {
  return backendFetch<ShoppingCart>("/cart/email", {
    method: "PATCH",
    body: JSON.stringify({ email }),
  })
}

export async function getCartShippingOptions(): Promise<Record<string, unknown>[]> {
  return backendFetch<Record<string, unknown>[]>("/cart/shipping-options")
}

export async function setCartShippingMethod(shippingMethodId: string): Promise<ShoppingCart> {
  return backendFetch<ShoppingCart>("/cart/shipping-method", {
    method: "PATCH",
    body: JSON.stringify({ shipping_method_id: shippingMethodId }),
  })
}

export async function createCartPaymentSession(providerId?: string): Promise<ShoppingCart> {
  return backendFetch<ShoppingCart>("/cart/payment-session", {
    method: "POST",
    body: JSON.stringify({ provider_id: providerId || "pp_system_default" }),
  })
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

// ── Payment ──────────────────────────────────────────────────────────

export async function processPayment(payload: {
  order_id: string
  card_number: string
  amount: number
  currency?: string
  access_token?: string
}): Promise<Record<string, unknown>> {
  return backendFetch<Record<string, unknown>>("/payments/process", {
    method: "POST",
    body: JSON.stringify(payload),
  })
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
