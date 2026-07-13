"use server"

import { listProducts as listBackendProducts } from "../../api/backend"
import { backendProductPrice } from "@lib/backend-native"
import { SortOptions } from "@modules/store/components/refinement-list/sort-products"

type ProductQueryParams = Record<string, any> & {
  limit?: number
  id?: string[] | string
  handle?: string
  order?: string
}

export const listProducts = async ({
  pageParam = 1,
  queryParams,
}: {
  pageParam?: number
  queryParams?: ProductQueryParams
  countryCode?: string
  regionId?: string
}): Promise<{
  response: { products: any[]; count: number }
  nextPage: number | null
  queryParams?: ProductQueryParams
}> => {
  const limit = queryParams?.limit || 12
  const offset = Math.max(pageParam - 1, 0) * limit
  let products = await listBackendProducts()

  const productIds = Array.isArray(queryParams?.id)
    ? queryParams?.id
    : queryParams?.id
    ? [queryParams.id]
    : []

  if (productIds.length) {
    const ids = new Set(productIds)
    products = products.filter(
      (product) =>
        ids.has(String(product.id)) ||
        ids.has(String(product.name)) ||
        ids.has(String(product.slug ?? "")) ||
        ids.has(String(product.handle ?? ""))
    )
  }

  const count = products.length
  const paginated = products.slice(offset, offset + limit)

  return {
    response: { products: paginated, count },
    nextPage: count > offset + limit ? pageParam + 1 : null,
    queryParams,
  }
}

export const listProductsWithSort = async ({
  page = 1,
  queryParams,
  sortBy = "created_at",
}: {
  page?: number
  queryParams?: ProductQueryParams
  sortBy?: SortOptions
  countryCode: string
}): Promise<{
  response: { products: any[]; count: number }
  nextPage: number | null
  queryParams?: ProductQueryParams
}> => {
  const limit = queryParams?.limit || 12
  const products = await listBackendProducts()
  const sortedProducts =
    sortBy === "price_asc"
      ? [...products].sort((a, b) => backendProductPrice(a) - backendProductPrice(b))
      : sortBy === "price_desc"
      ? [...products].sort((a, b) => backendProductPrice(b) - backendProductPrice(a))
      : products
  const offset = Math.max(page - 1, 0) * limit

  return {
    response: {
      products: sortedProducts.slice(offset, offset + limit),
      count: sortedProducts.length,
    },
    nextPage: sortedProducts.length > offset + limit ? page + 1 : null,
    queryParams,
  }
}
