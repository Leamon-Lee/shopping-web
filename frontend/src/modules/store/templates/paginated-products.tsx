import { listProducts } from "../../../api/backend"
import {
  backendProductName,
  backendProductPrice,
} from "../../../lib/backend-native"
import BackendProductPreview from "@modules/products/components/backend-product-preview"
import { Pagination } from "@modules/store/components/pagination"
import { SortOptions } from "@modules/store/components/refinement-list/sort-products"

const PRODUCT_LIMIT = 12

export default async function PaginatedProducts({
  sortBy,
  page,
  shop,
}: {
  sortBy?: SortOptions
  page: number
  shop?: string
  countryCode: string
  categoryId?: string
  collectionId?: string
  productsIds?: string[]
}) {
  const products = await listProducts(shop)
  const sortedProducts =
    sortBy === "price_asc"
      ? [...products].sort((a, b) => backendProductPrice(a) - backendProductPrice(b))
      : sortBy === "price_desc"
      ? [...products].sort((a, b) => backendProductPrice(b) - backendProductPrice(a))
      : [...products].sort((a, b) =>
          backendProductName(a).localeCompare(backendProductName(b))
        )

  const start = Math.max(page - 1, 0) * PRODUCT_LIMIT
  const paginatedProducts = sortedProducts.slice(start, start + PRODUCT_LIMIT)
  const totalPages = Math.ceil(sortedProducts.length / PRODUCT_LIMIT)

  return (
    <>
      <ul
        className="grid grid-cols-2 w-full small:grid-cols-3 medium:grid-cols-4 gap-x-6 gap-y-8"
        data-testid="products-list"
      >
        {paginatedProducts.map((product) => (
          <li key={backendProductName(product)}>
            <BackendProductPreview product={product} />
          </li>
        ))}
      </ul>
      {totalPages > 1 && (
        <Pagination
          data-testid="product-pagination"
          page={page}
          totalPages={totalPages}
        />
      )}
    </>
  )
}
