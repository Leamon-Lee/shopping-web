import { getCart, getCartForUsername } from "api/backend"
import { cartHrefForUsername } from "@lib/cart-url"
import { retrieveCustomer } from "@lib/data/customer"
import BackendCartPage from "@modules/cart/templates/backend-cart-page"
import { headers } from "next/headers"
import { notFound, redirect } from "next/navigation"

export const dynamic = "force-dynamic"
export const revalidate = 0

const TOKEN_COOKIE = "shopping_token"

function logoutHref(redirectPath: string) {
  return `/auth/logout?redirect=${encodeURIComponent(redirectPath)}`
}

function hasCookie(cookieHeader: string | null, name: string) {
  return cookieHeader
    ?.split(";")
    .some((part) => part.trim().startsWith(`${name}=`)) ?? false
}

export default async function CountryCart(props: {
  params: Promise<{ countryCode: string }>
}) {
  const { countryCode } = await props.params
  if (countryCode === "cart") {
    notFound()
  }

  const requestHeaders = await headers()
  const hasAuthCookie = hasCookie(requestHeaders.get("cookie"), TOKEN_COOKIE)
  const customer = await retrieveCustomer()
  const currentPath = `/${countryCode}/cart`

  if (hasAuthCookie && !customer) {
    redirect(logoutHref(currentPath))
  }

  if (customer?.user_name && countryCode !== customer.user_name) {
    redirect(cartHrefForUsername(customer.user_name))
  }

  let cart =
    countryCode === "guest"
      ? await getCart().catch(() => null)
      : await getCartForUsername(countryCode).catch(() => null)

  // Fallback: if username-based cart is empty and user is a guest,
  // try the cookie-based cart (cart_id isolation)
  if (!cart || (!customer && (cart.items?.length ?? 0) === 0)) {
    const cookieCart = await getCart().catch(() => null)
    if (cookieCart && (cookieCart.items?.length ?? 0) > 0) {
      cart = cookieCart
    }
  }

  return <BackendCartPage cart={cart} ownerUsername={countryCode} />
}
