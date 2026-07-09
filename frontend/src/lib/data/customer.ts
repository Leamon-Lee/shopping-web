"use server"

import {
  login as apiLogin,
  registerAccount as apiRegister,
  retrieveCustomer as apiRetrieveCustomer,
  updateCustomer as apiUpdateCustomer,
  addCustomerAddress as apiAddCustomerAddress,
  updateCustomerAddress as apiUpdateCustomerAddress,
  deleteCustomerAddress as apiDeleteCustomerAddress,
} from "../../api/backend"
import { cookies } from "next/headers"

const SESSION_COOKIE = "shopping_email"

async function getSessionEmail(): Promise<string | null> {
  const store = await cookies()
  return store.get(SESSION_COOKIE)?.value ?? null
}

async function setSessionEmail(email: string) {
  const store = await cookies()
  store.set(SESSION_COOKIE, email, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    maxAge: 60 * 60 * 24 * 7, // 7 days
  })
}

export const retrieveCustomer = async () => {
  const email = await getSessionEmail()
  if (!email) return null
  try {
    return await apiRetrieveCustomer(email)
  } catch {
    return null
  }
}

export const updateCustomer = async (_prevState: any, formData: FormData) => {
  const email = await getSessionEmail()
  if (!email) return "Not logged in."
  try {
    const entries: Record<string, any> = {}
    formData.forEach((value, key) => {
      entries[key] = value
    })
    await apiUpdateCustomer(email, entries)
    return null
  } catch (e: any) {
    return e.message || "Failed to update customer."
  }
}

export async function signup(_prevState: any, formData: FormData) {
  const payload: Record<string, any> = {}
  formData.forEach((value, key) => {
    payload[key] = value
  })

  try {
    await apiRegister({
      email: payload.email?.toString() ?? "",
      password: payload.password?.toString() ?? "",
      first_name: payload.first_name?.toString() ?? "",
      last_name: payload.last_name?.toString() ?? "",
      phone_country_code: "",
      phone_number: payload.phone?.toString() ?? "",
      street: "",
      city: "",
      state: "",
      postal_code: "",
      country: "",
    })
    await setSessionEmail(payload.email?.toString() ?? "")
    return null
  } catch (e: any) {
    return e.message || "Registration failed."
  }
}

export async function login(_prevState: any, formData: FormData) {
  const email = formData.get("email")?.toString() ?? ""
  const password = formData.get("password")?.toString() ?? ""

  try {
    await apiLogin({ email, password })
    await setSessionEmail(email)
    return null
  } catch (e: any) {
    return e.message || "Login failed."
  }
}

export async function signout() {
  const store = await cookies()
  store.delete(SESSION_COOKIE)
}

export async function transferCart() {
  // Cart transfer between guest and logged-in states — not yet implemented
}

export const addCustomerAddress = async (_prevState: any, formData: FormData) => {
  const email = await getSessionEmail()
  if (!email) return "Not logged in."

  const payload: Record<string, any> = {}
  formData.forEach((value, key) => {
    payload[key] = value
  })

  try {
    await apiAddCustomerAddress(email, {
      street: payload.street ?? payload.address_1 ?? "",
      city: payload.city ?? "",
      state: payload.state ?? payload.province ?? "",
      postal_code: payload.postal_code ?? "",
      country: payload.country_code ?? payload.country ?? "",
      is_default_shipping: false,
    } as any)
    return null
  } catch (e: any) {
    return e.message || "Failed to add address."
  }
}

export const deleteCustomerAddress = async (addressId: string) => {
  const email = await getSessionEmail()
  if (!email) return "Not logged in."
  try {
    await apiDeleteCustomerAddress(email, addressId)
  } catch (e: any) {
    return e.message || "Failed to delete address."
  }
}

export const updateCustomerAddress = async (_prevState: any, formData: FormData) => {
  const email = await getSessionEmail()
  if (!email) return "Not logged in."

  const addressId = formData.get("address_id")?.toString() ?? ""
  const payload: Record<string, any> = {}
  formData.forEach((value, key) => {
    if (key !== "address_id") {
      payload[key] = value
    }
  })

  try {
    await apiUpdateCustomerAddress(email, addressId, {
      street: payload.street ?? payload.address_1 ?? undefined,
      city: payload.city ?? undefined,
      state: payload.state ?? payload.province ?? undefined,
      postal_code: payload.postal_code ?? undefined,
      country: payload.country_code ?? payload.country ?? undefined,
    })
    return null
  } catch (e: any) {
    return e.message || "Failed to update address."
  }
}
