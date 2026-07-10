import type { BackendProduct } from "../../../../types/backend"
import {
  backendCategoryName,
  backendProductName,
  backendProductPrice,
  backendProductSlug,
  formatBackendMoney,
} from "../../../../lib/backend-native"
import LocalizedClientLink from "@modules/common/components/localized-client-link"
import Thumbnail from "@modules/products/components/thumbnail"

export default function BackendProductPreview({
  product,
  isFeatured,
}: {
  product: BackendProduct
  isFeatured?: boolean
}) {
  const name = backendProductName(product)

  return (
    <LocalizedClientLink href={`/shop/${backendProductSlug(product)}`} className="group">
      <div data-testid="product-wrapper">
        <Thumbnail thumbnail={null} images={(product as any).images ?? []} size="full" isFeatured={isFeatured} />
        <div className="flex txt-compact-medium mt-4 justify-between">
          <span className="text-ui-fg-subtle" data-testid="product-title">
            {name}
          </span>
          <span className="text-ui-fg-muted" data-testid="price">
            {formatBackendMoney(backendProductPrice(product))}
          </span>
        </div>
        <p className="mt-1 text-small-regular text-ui-fg-muted">
          {backendCategoryName(product.category)}
        </p>
      </div>
    </LocalizedClientLink>
  )
}
