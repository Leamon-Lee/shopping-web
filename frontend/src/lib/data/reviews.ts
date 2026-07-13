"use server"

import { cookies } from "next/headers"

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8001"
const TOKEN_COOKIE = "shopping_token"

async function authFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const store = await cookies()
  const token = store.get(TOKEN_COOKIE)?.value
  const headers: Record<string, string> = { "content-type": "application/json", ...(init?.headers as any) }
  if (token) headers["Authorization"] = `Bearer ${token}`
  const res = await fetch(`${BACKEND_URL}${path}`, { ...init, headers, cache: "no-store" })
  if (!res.ok) { const body = await res.json().catch(() => ({})); throw new Error(body.detail || `Failed: ${res.status}`) }
  return res.json()
}

export async function createReview(productIdentity: string, rating: number, content: string) {
  return authFetch(`/shop/${encodeURIComponent(productIdentity)}/reviews`, {
    method: "POST",
    body: JSON.stringify({ rating, content }),
  })
}

export async function deleteReview(reviewId: string) {
  return authFetch(`/accounts/me/reviews/${reviewId}`, { method: "DELETE" })
}

export async function fetchProductReviews(productIdentity: string) {
  return authFetch(`/shop/${encodeURIComponent(productIdentity)}/reviews`)
}
