import type { BackendValue } from "../../types/backend"

export function unwrapBackendValue<T>(value: BackendValue<T>): T {
  if (
    value !== null &&
    typeof value === "object" &&
    "value" in value
  ) {
    return value.value
  }

  return value
}

export function formatMoney(amount: number, currency = "USD") {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
  }).format(amount)
}

export function slugify(value: string) {
  return value
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
}
