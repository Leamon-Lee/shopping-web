import type {
  BackendAccount,
  BackendAddress,
  BackendOrder,
  BackendOrderPayload,
  BackendProduct,
  BackendProductCategory,
  BackendProductFormPayload,
  BackendRegion,
  BackendShoppingCart,
} from "../types/backend"

const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL ||
  "http://localhost:8001"

async function backendFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${BACKEND_URL}${path}`, {
    ...init,
    headers: {
      "content-type": "application/json",
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

export async function listRegions(): Promise<BackendRegion[]> {
  return backendFetch<BackendRegion[]>("/regions")
}

export async function getRegion(regionId: string): Promise<BackendRegion> {
  return backendFetch<BackendRegion>(`/regions/${regionId}`)
}

export async function listProducts(): Promise<BackendProduct[]> {
  return backendFetch<BackendProduct[]>("/products")
}

export async function getProduct(productName: string): Promise<BackendProduct> {
  return backendFetch<BackendProduct>(
    `/products/${encodeURIComponent(productName)}`
  )
}

export async function createProduct(
  payload: BackendProductFormPayload
): Promise<BackendProduct> {
  return backendFetch<BackendProduct>("/products", {
    method: "POST",
    body: JSON.stringify(payload),
  })
}

export async function listCategories(): Promise<BackendProductCategory[]> {
  return backendFetch<BackendProductCategory[]>("/products/categories")
}

export async function getCart(): Promise<BackendShoppingCart> {
  return backendFetch<BackendShoppingCart>("/cart")
}

export async function addCartItem(payload: {
  product_name: string
  quantity: number
}): Promise<BackendShoppingCart> {
  return backendFetch<BackendShoppingCart>("/cart/items", {
    method: "POST",
    body: JSON.stringify(payload),
  })
}

export async function updateCartItem(
  productName: string,
  quantity: number
): Promise<BackendShoppingCart> {
  return backendFetch<BackendShoppingCart>(
    `/cart/items/${encodeURIComponent(productName)}`,
    {
      method: "PATCH",
      body: JSON.stringify({ quantity }),
    }
  )
}

export async function deleteCartItem(
  productName: string
): Promise<BackendShoppingCart> {
  return backendFetch<BackendShoppingCart>(
    `/cart/items/${encodeURIComponent(productName)}`,
    { method: "DELETE" }
  )
}

export async function placeOrder(
  payload: BackendOrderPayload = {}
): Promise<BackendOrder> {
  return backendFetch<BackendOrder>("/orders", {
    method: "POST",
    body: JSON.stringify(payload),
  })
}

export async function listOrders(): Promise<BackendOrder[]> {
  return backendFetch<BackendOrder[]>("/orders")
}

export async function getOrder(orderNumber: string): Promise<BackendOrder> {
  return backendFetch<BackendOrder>(`/orders/${encodeURIComponent(orderNumber)}`)
}

export async function login(payload: {
  email: string
  password: string
}): Promise<BackendAccount> {
  return backendFetch<BackendAccount>("/accounts/login", {
    method: "POST",
    body: JSON.stringify(payload),
  })
}

export async function registerAccount(payload: Record<string, any>): Promise<BackendAccount> {
  return backendFetch<BackendAccount>("/accounts/register", {
    method: "POST",
    body: JSON.stringify(payload),
  })
}

export async function retrieveCustomer(
  email: string
): Promise<BackendAccount> {
  return backendFetch<BackendAccount>(
    `/accounts/me?email=${encodeURIComponent(email)}`
  )
}

export async function updateCustomer(
  email: string,
  payload: Record<string, any>
): Promise<BackendAccount> {
  const params = new URLSearchParams({ email, ...payload })
  return backendFetch<BackendAccount>(`/accounts/me?${params.toString()}`, {
    method: "PUT",
  })
}

export async function listCustomerAddresses(
  email: string
): Promise<BackendAddress[]> {
  return backendFetch<BackendAddress[]>(
    `/accounts/me/addresses?email=${encodeURIComponent(email)}`
  )
}

export async function addCustomerAddress(
  email: string,
  payload: BackendAddress
): Promise<BackendAddress[]> {
  return backendFetch<BackendAddress[]>(
    `/accounts/me/addresses?email=${encodeURIComponent(email)}`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    }
  )
}

export async function updateCustomerAddress(
  email: string,
  addressId: string,
  payload: Partial<BackendAddress>
): Promise<BackendAddress[]> {
  return backendFetch<BackendAddress[]>(
    `/accounts/me/addresses/${addressId}?email=${encodeURIComponent(email)}`,
    {
      method: "PUT",
      body: JSON.stringify(payload),
    }
  )
}

export async function deleteCustomerAddress(
  email: string,
  addressId: string
): Promise<BackendAddress[]> {
  return backendFetch<BackendAddress[]>(
    `/accounts/me/addresses/${addressId}?email=${encodeURIComponent(email)}`,
    { method: "DELETE" }
  )
}
