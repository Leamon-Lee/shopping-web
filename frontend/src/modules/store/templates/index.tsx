import { backendProductFixtures } from "../../../api/backend-fixtures"
import { mapBackendProductToFrontendProduct } from "../../../adapters/backend/product"
import RefinementList from "@modules/store/components/refinement-list"
import { SortOptions } from "@modules/store/components/refinement-list/sort-products"
import LocalizedClientLink from "@modules/common/components/localized-client-link"

const StoreTemplate = ({
  sortBy,
  page,
  countryCode,
}: {
  sortBy?: SortOptions
  page?: string
  countryCode: string
}) => {
  const pageNumber = page ? parseInt(page) : 1
  const sort = sortBy || "created_at"
  const products = backendProductFixtures.map(mapBackendProductToFrontendProduct)
  const sortedProducts =
    sort === "price_asc"
      ? [...products].sort((a, b) => a.price - b.price)
      : sort === "price_desc"
      ? [...products].sort((a, b) => b.price - a.price)
      : products

  return (
    <div
      className="flex flex-col small:flex-row small:items-start py-6 content-container"
      data-testid="category-container"
    >
      <RefinementList sortBy={sort} />
      <div className="w-full">
        <div className="mb-8 text-2xl-semi">
          <h1 data-testid="store-page-title">All products</h1>
        </div>
        <ul
          className="grid grid-cols-2 w-full small:grid-cols-3 medium:grid-cols-4 gap-x-6 gap-y-8"
          data-testid="products-list"
        >
          {sortedProducts.map((product) => (
            <li key={product.id}>
              <LocalizedClientLink href={`/products/${product.id}`} className="group">
                <div data-testid="product-wrapper">
                  <div className="relative w-full overflow-hidden p-4 bg-ui-bg-subtle shadow-elevation-card-rest rounded-large group-hover:shadow-elevation-card-hover transition-shadow ease-in-out duration-150 aspect-[9/16]">
                    <div className="absolute inset-0 flex items-center justify-center text-ui-fg-muted text-small-regular">
                      {product.category.name}
                    </div>
                  </div>
                  <div className="flex txt-compact-medium mt-4 justify-between">
                    <span className="text-ui-fg-subtle">{product.name}</span>
                    <span className="text-ui-fg-base">{product.displayPrice}</span>
                  </div>
                  <p className="mt-1 text-small-regular text-ui-fg-muted">
                    {product.availableItemCount} available
                  </p>
                </div>
              </LocalizedClientLink>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}

export default StoreTemplate
