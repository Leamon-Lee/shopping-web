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

export function shopHref(shop: BackendShopSummary, _currentUser?: Account | null) {
  return `/shop?shop=${encodeURIComponent(shop.slug)}`
}

export function productHref(
  product: BackendProduct,
  _currentUser?: Account | null,
  _fallbackShopSlug?: string
) {
  const productSlug = product.slug || backendProductSlug(product)
  return `/shop/${productSlug}`
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
