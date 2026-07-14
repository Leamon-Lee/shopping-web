export const GUEST_CART_USERNAME = "guest"

export function cartHrefForUsername(username?: string | null): string {
  return `/${encodeURIComponent(username || GUEST_CART_USERNAME)}/cart`
}
