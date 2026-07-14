"use server"

import { cookies } from "next/headers"
import type { Account, TokenResponse } from "types/backend"

const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8001"

const TOKEN_COOKIE = "shopping_token"

export type AuthActionResult = {
  error?: string
  redirectTo?: string
}

function customerHallPath(userName: string) {
  return `/${encodeURIComponent(userName)}/hall`
}

async function backendFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const cookieStore = await cookies()
  const token = cookieStore.get(TOKEN_COOKIE)?.value

  const headers: Record<string, string> = {
    "content-type": "application/json",
    ...(init?.headers as Record<string, string> | undefined),
  }
  if (token) {
    headers["Authorization"] = `Bearer ${token}`
  }

  const response = await fetch(`${BACKEND_URL}${path}`, {
    ...init,
    headers,
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

async function setTokenCookie(token: string) {
  const store = await cookies()
  store.set(TOKEN_COOKIE, token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
    maxAge: 60 * 60 * 24 * 7, // 7 days
  })
}

async function getToken(): Promise<string | null> {
  const store = await cookies()
  return store.get(TOKEN_COOKIE)?.value ?? null
}

// ── Public auth actions ──────────────────────────────────────────────

export async function login(
  _prevState: unknown,
  formData: FormData
): Promise<AuthActionResult | null> {
  const email = formData.get("email")?.toString() ?? ""
  const password = formData.get("password")?.toString() ?? ""

  try {
    const result = await backendFetch<TokenResponse>("/accounts/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    })
    await setTokenCookie(result.access_token)
    return { redirectTo: customerHallPath(result.user.user_name) }
  } catch (e: unknown) {
    return { error: e instanceof Error ? e.message : "Login failed." }
  }
}

export async function signup(
  _prevState: unknown,
  formData: FormData
): Promise<AuthActionResult | null> {
  const payload: Record<string, string> = {}
  formData.forEach((value, key) => {
    payload[key] = value.toString()
  })

  try {
    await backendFetch<Account>("/accounts/register", {
      method: "POST",
      body: JSON.stringify({
        email: payload.email ?? "",
        password: payload.password ?? "",
        first_name: payload.first_name ?? "",
        last_name: payload.last_name ?? "",
        phone_country_code: "",
        phone_number: payload.phone ?? "",
        street: "",
        city: "",
        state: "",
        postal_code: "",
        country: "",
      }),
    })
    // Auto-login after registration
    const loginResult = await backendFetch<TokenResponse>("/accounts/login", {
      method: "POST",
      body: JSON.stringify({
        email: payload.email ?? "",
        password: payload.password ?? "",
      }),
    })
    await setTokenCookie(loginResult.access_token)
    return { redirectTo: customerHallPath(loginResult.user.user_name) }
  } catch (e: unknown) {
    return { error: e instanceof Error ? e.message : "Registration failed." }
  }
}

export async function signout() {
  const store = await cookies()
  store.delete({
    name: TOKEN_COOKIE,
    path: "/",
  })
}

// ── Authenticated actions ────────────────────────────────────────────

export async function retrieveCustomer(): Promise<Account | null> {
  const token = await getToken()
  if (!token) return null
  try {
    const account = await backendFetch<Account>("/accounts/me")
    // Spread top-level name fields for checkout component compatibility
    if (account) {
      account.first_name = account.name?.first_name || ""
      account.last_name = account.name?.last_name || ""
    }
    return account
  } catch {
    return null
  }
}

export async function updateCustomer(
  _prevState: unknown,
  formData: FormData
): Promise<string | null> {
  const entries: Record<string, string> = {}
  formData.forEach((value, key) => {
    entries[key] = value.toString()
  })
  try {
    await backendFetch<Account>("/accounts/me", {
      method: "PUT",
      body: JSON.stringify({
        first_name: entries.first_name,
        last_name: entries.last_name,
        phone_number: entries.phone_number,
        phone_country_code: entries.phone_country_code,
      }),
    })
    return null
  } catch (e: unknown) {
    return e instanceof Error ? e.message : "Failed to update customer."
  }
}

export async function addCustomerAddress(
  _prevState: unknown,
  formData: FormData
): Promise<string | null> {
  const payload: Record<string, unknown> = {}
  formData.forEach((value, key) => {
    payload[key] = value
  })
  try {
    await backendFetch("/accounts/me/addresses", {
      method: "POST",
      body: JSON.stringify({
        street: payload.street ?? payload.address_1 ?? "",
        city: payload.city ?? "",
        state: payload.state ?? payload.province ?? "",
        postal_code: payload.postal_code ?? "",
        country: payload.country_code ?? payload.country ?? "",
        is_default_shipping: false,
      }),
    })
    return null
  } catch (e: unknown) {
    return e instanceof Error ? e.message : "Failed to add address."
  }
}

export async function deleteCustomerAddress(addressId: string): Promise<string | null> {
  try {
    await backendFetch(`/accounts/me/addresses/${addressId}`, { method: "DELETE" })
    return null
  } catch (e: unknown) {
    return e instanceof Error ? e.message : "Failed to delete address."
  }
}

export async function updateCustomerAddress(
  _prevState: unknown,
  formData: FormData
): Promise<string | null> {
  const addressId = formData.get("address_id")?.toString() ?? ""
  const payload: Record<string, unknown> = {}
  formData.forEach((value, key) => {
    if (key !== "address_id") payload[key] = value
  })
  try {
    await backendFetch(`/accounts/me/addresses/${addressId}`, {
      method: "PUT",
      body: JSON.stringify({
        street: payload.street ?? payload.address_1 ?? undefined,
        city: payload.city ?? undefined,
        state: payload.state ?? payload.province ?? undefined,
        postal_code: payload.postal_code ?? undefined,
        country: payload.country_code ?? payload.country ?? undefined,
      }),
    })
    return null
  } catch (e: unknown) {
    return e instanceof Error ? e.message : "Failed to update address."
  }
}

export async function listCustomerAddresses() {
  try {
    return await backendFetch<import("types/backend").Address[]>("/accounts/me/addresses")
  } catch {
    return []
  }
}

export async function transferCart() {
  // Cart transfer between guest and logged-in states — not yet implemented
}
