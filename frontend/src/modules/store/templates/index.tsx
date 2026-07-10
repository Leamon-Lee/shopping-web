import PaginatedProducts from "./paginated-products"
import RefinementList from "@modules/store/components/refinement-list"
import { SortOptions } from "@modules/store/components/refinement-list/sort-products"

const StoreTemplate = ({
  sortBy,
  page,
  shop,
  countryCode,
}: {
  sortBy?: SortOptions
  page?: string
  shop?: string
  countryCode: string
}) => {
  const pageNumber = page ? parseInt(page) : 1
  const sort = sortBy || "created_at"
  const shopTitle = shop
    ? shop
        .split("-")
        .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
        .join(" ")
    : "All products"

  return (
    <div
      className="flex flex-col small:flex-row small:items-start py-6 content-container"
      data-testid="category-container"
    >
      <RefinementList sortBy={sort} />
      <div className="w-full">
        <div className="mb-8 text-2xl-semi">
          <h1 data-testid="store-page-title">{shopTitle}</h1>
        </div>
        <PaginatedProducts
          sortBy={sort}
          page={pageNumber}
          shop={shop}
          countryCode={countryCode}
        />
      </div>
    </div>
  )
}

export default StoreTemplate
