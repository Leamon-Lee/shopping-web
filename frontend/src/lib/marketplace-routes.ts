import type {
  Account,
  BackendProduct,
  BackendShopSummary,
} from "../types/backend"
import {
  backendProductName,
  backendProductSlug,
  backendSlug,
} from "./backend-native"

export function userNamePath(currentUser?: Account | null) {
  return currentUser ? encodeURIComponent(currentUser.user_name) : null
}

export function productShopSlug(product: BackendProduct) {
  return backendSlug(product.shop?.shop_name ?? "shop")
}

export function shopHref(shop: BackendShopSummary, currentUser?: Account | null) {
  const username = userNamePath(currentUser)

  return username
    ? `/${username}/${shop.slug}`
    : `/shop?shop=${encodeURIComponent(shop.slug)}`
}

export function productHref(
  product: BackendProduct,
  currentUser?: Account | null,
  fallbackShopSlug?: string
) {
  const username = userNamePath(currentUser)
  const productSlug = product.slug || backendProductSlug(product)
  const shopSlug = product.shop?.shop_name
    ? productShopSlug(product)
    : fallbackShopSlug ?? productShopSlug(product)

  return username
    ? `/${username}/${shopSlug}/${productSlug}`
    : `/shop/${productSlug}`
}

export function productMatchesRoute(product: BackendProduct, routeValue: string) {
  const value = decodeURIComponent(routeValue)
  return (
    product.id === value ||
    product.slug === value ||
    backendProductSlug(product) === value ||
    backendProductName(product) === value
  )
}
