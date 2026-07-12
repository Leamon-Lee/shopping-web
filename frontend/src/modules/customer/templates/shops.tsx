import { Badge } from "@medusajs/ui"
import LocalizedClientLink from "@modules/common/components/localized-client-link"
import type {
  Account,
  BackendHallPayload,
  BackendProduct,
  BackendShopSummary,
} from "../../../types/backend"
import {
  backendCategoryName,
  backendProductName,
  backendProductPrice,
  formatBackendMoney,
} from "../../../lib/backend-native"
import { productHref, shopHref } from "../../../lib/marketplace-routes"

const SHOP_PREVIEW_COUNT = 6

const ShopsTemplate = ({
  data,
  currentUser,
  activeShopPath,
}: {
  data: BackendHallPayload
  currentUser?: Account | null
  activeShopPath?: string
}) => {
  const customerBasePath = currentUser
    ? `/customer/${encodeURIComponent(currentUser.user_name)}`
    : null
  const hallPath = customerBasePath ? `${customerBasePath}/hall` : "/hall"
  const shopsPath = currentUser
    ? `/${encodeURIComponent(currentUser.user_name)}/shops`
    : "/shops"
  const catlogPath = currentUser
    ? `/${encodeURIComponent(currentUser.user_name)}/catlog`
    : "/catlog"
  const shopProducts = new Map(
    data.sections.map((section) => [section.shop.slug, section.products])
  )

  return (
    <main className="min-h-screen bg-ui-bg-base text-ui-fg-base">
      <header className="sticky inset-x-0 top-0 z-50 border-b border-ui-border-base bg-white">
        <div className="content-container flex h-16 items-center justify-between text-small-regular text-ui-fg-subtle">
          <LocalizedClientLink href={hallPath} className="text-ui-fg-base">
            SHOPPING HALL
          </LocalizedClientLink>
          <nav className="hidden items-center gap-x-6 small:flex">
            <LocalizedClientLink className="hover:text-ui-fg-base" href={hallPath}>
              Hall
            </LocalizedClientLink>
            <LocalizedClientLink className="text-ui-fg-base" href={activeShopPath ?? shopsPath}>
              Shops
            </LocalizedClientLink>
            <LocalizedClientLink className="hover:text-ui-fg-base" href={catlogPath}>
              Catlog
            </LocalizedClientLink>
          </nav>
          <div className="flex items-center gap-x-4">
            <LocalizedClientLink href="/cart" className="hover:text-ui-fg-base">
              Cart
            </LocalizedClientLink>
            {currentUser ? (
              <LocalizedClientLink
                href={customerBasePath ?? "/customer"}
                className="hover:text-ui-fg-base"
              >
                Account
              </LocalizedClientLink>
            ) : (
              <LocalizedClientLink
                href="/auth/login"
                className="hover:text-ui-fg-base"
              >
                Sign in
              </LocalizedClientLink>
            )}
          </div>
        </div>
      </header>

      <section className="content-container py-8">
        <div className="mb-6 flex flex-col gap-3 small:flex-row small:items-end small:justify-between">
          <div>
            <p className="txt-xsmall-plus uppercase text-ui-fg-muted">Shops</p>
            <h1 className="mt-2 text-2xl-semi">Browse marketplace shops</h1>
            <p className="mt-2 max-w-2xl text-small-regular text-ui-fg-subtle">
              Pick a shop to open its product feed. Each shop preview shows a
              small slice of its catalog.
            </p>
          </div>
          <Badge>{data.shops.length} shops</Badge>
        </div>

        <ul className="flex flex-col gap-5">
          {data.shops.map((shop) => (
            <li key={shop.id}>
              <ShopRow
                shop={shop}
                products={shopProducts.get(shop.slug) ?? []}
                currentUser={currentUser}
              />
            </li>
          ))}
        </ul>
      </section>
    </main>
  )
}

const ShopRow = ({
  shop,
  products,
  currentUser,
}: {
  shop: BackendShopSummary
  products: BackendProduct[]
  currentUser?: Account | null
}) => {
  const previewProducts = products.slice(0, SHOP_PREVIEW_COUNT)

  return (
    <article className="w-full rounded-rounded border border-ui-border-base bg-white p-5">
      <div className="flex flex-col gap-4 medium:flex-row medium:items-start medium:justify-between">
        <LocalizedClientLink
          href={shopHref(shop, currentUser)}
          className="min-w-0 medium:w-64"
        >
          <div className="flex items-start justify-between gap-4 medium:block">
            <div>
              <h2 className="text-base-semi">{shop.name}</h2>
              <p className="mt-1 text-small-regular text-ui-fg-subtle">
                {shop.product_count} products
              </p>
            </div>
            <Badge>{shop.categories.length} categories</Badge>
          </div>
          <p className="mt-4 line-clamp-2 text-small-regular text-ui-fg-muted">
            {shop.categories.slice(0, 5).join(", ") || "Marketplace shop"}
          </p>
        </LocalizedClientLink>

        <ul className="grid flex-1 grid-cols-2 gap-3 small:grid-cols-3 medium:grid-cols-6">
          {previewProducts.map((product) => (
            <li key={product.id ?? backendProductName(product)}>
              <ShopProductPreview product={product} currentUser={currentUser} />
            </li>
          ))}
        </ul>
      </div>
    </article>
  )
}

const ShopProductPreview = ({
  product,
  currentUser,
}: {
  product: BackendProduct
  currentUser?: Account | null
}) => {
  const imageUrl = getProductImageUrl(product)
  const name = backendProductName(product)

  return (
    <LocalizedClientLink
      href={productHref(product, currentUser)}
      className="group block min-w-0"
    >
      <div className="aspect-square overflow-hidden rounded-rounded bg-ui-bg-subtle">
        {imageUrl ? (
          <img
            src={imageUrl}
            alt={name}
            className="h-full w-full object-cover transition-transform duration-150 group-hover:scale-[1.03]"
            loading="lazy"
            decoding="async"
          />
        ) : null}
      </div>
      <h3 className="mt-2 line-clamp-2 text-small-regular text-ui-fg-base">
        {name}
      </h3>
      <div className="mt-1 flex items-center justify-between gap-2 text-small-regular text-ui-fg-muted">
        <span className="line-clamp-1">{backendCategoryName(product.category)}</span>
        <span className="shrink-0">
          {formatBackendMoney(backendProductPrice(product))}
        </span>
      </div>
    </LocalizedClientLink>
  )
}

function getProductImageUrl(product: BackendProduct): string | null {
  return (
    product.thumbnail ||
    product.images?.[0]?.url ||
    product.images?.[0]?.image_url ||
    null
  )
}

export default ShopsTemplate
