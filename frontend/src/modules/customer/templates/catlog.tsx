import { Badge } from "@medusajs/ui"
import LocalizedClientLink from "@modules/common/components/localized-client-link"
import type {
  Account,
  BackendHallPayload,
  BackendProduct,
} from "../../../types/backend"
import {
  backendCategoryName,
  backendProductName,
  backendProductPrice,
  formatBackendMoney,
} from "../../../lib/backend-native"
import { productHref } from "../../../lib/marketplace-routes"
import { signout } from "@lib/data/customer"

const CATEGORY_PREVIEW_COUNT = 5

type CategoryGroup = {
  name: string
  slug: string
  products: BackendProduct[]
  shops: string[]
}

const CatlogTemplate = ({
  data,
  currentUser,
  activeCatlogPath,
}: {
  data: BackendHallPayload
  currentUser?: Account | null
  activeCatlogPath?: string
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
  const groups = buildCategoryGroups(data)
  const featuredGroups = groups.slice(0, 6)

  return (
    <main className="min-h-screen bg-ui-bg-base text-ui-fg-base">
      <header className="sticky inset-x-0 top-0 z-50 border-b border-ui-border-base bg-gray-200">
        <div className="content-container flex h-16 items-center justify-between text-small-regular text-ui-fg-subtle">
          <LocalizedClientLink href={hallPath} className="text-ui-fg-base">
            SHOPPING HALL
          </LocalizedClientLink>
          <nav className="hidden items-center gap-x-6 small:flex">
            <LocalizedClientLink className="hover:text-ui-fg-base" href={hallPath}>
              Hall
            </LocalizedClientLink>
            <LocalizedClientLink className="hover:text-ui-fg-base" href={shopsPath}>
              Shops
            </LocalizedClientLink>
            <LocalizedClientLink className="text-ui-fg-base" href={activeCatlogPath ?? catlogPath}>
              Catlog
            </LocalizedClientLink>
          </nav>
          <div className="flex items-center gap-x-4">
            <LocalizedClientLink href="/cart" className="hover:text-ui-fg-base">
              Cart
            </LocalizedClientLink>
            {currentUser ? (
              <>
                <LocalizedClientLink
                  href={customerBasePath ?? "/customer"}
                  className="hover:text-ui-fg-base"
                >
                  Account
                </LocalizedClientLink>
                <button
                  type="button"
                  className="hover:text-ui-fg-base"
                  onClick={() => signout()}
                >
                  Log out
                </button>
              </>
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
        <div className="border-b border-ui-border-base pb-6">
          <div className="flex flex-col gap-4 small:flex-row small:items-end small:justify-between">
            <div>
              <p className="txt-xsmall-plus uppercase text-ui-fg-muted">Catlog</p>
              <h1 className="mt-2 text-2xl-semi">Shop by category</h1>
              <p className="mt-2 max-w-2xl text-small-regular text-ui-fg-subtle">
                Browse departments, compare category previews, and jump into a
                filtered product feed.
              </p>
            </div>
            <div className="flex gap-2">
              <Badge>{groups.length} categories</Badge>
              <Badge>{data.product_count} products</Badge>
            </div>
          </div>

          <div className="mt-5 flex gap-2 overflow-x-auto pb-1">
            {groups.map((group) => (
              <LocalizedClientLink
                key={group.slug}
                href={`/hall?category=${encodeURIComponent(group.slug)}`}
                className="flex h-9 shrink-0 items-center rounded-rounded border border-ui-border-base bg-white px-3 text-small-regular text-ui-fg-subtle hover:bg-ui-bg-subtle hover:text-ui-fg-base"
              >
                {group.name}
              </LocalizedClientLink>
            ))}
          </div>
        </div>

        <section className="py-7">
          <div className="mb-4 flex items-end justify-between">
            <div>
              <h2 className="text-xl-semi">Featured departments</h2>
              <p className="mt-1 text-small-regular text-ui-fg-subtle">
                Product-rich categories surfaced first for faster browsing.
              </p>
            </div>
          </div>
          <ul className="grid grid-cols-1 gap-4 medium:grid-cols-2">
            {featuredGroups.map((group) => (
              <li key={group.slug}>
                <CategoryFeature group={group} currentUser={currentUser} />
              </li>
            ))}
          </ul>
        </section>

        <section className="border-t border-ui-border-base py-7">
          <div className="mb-4">
            <h2 className="text-xl-semi">All categories</h2>
          </div>
          <ul className="grid grid-cols-1 gap-3 small:grid-cols-2 medium:grid-cols-3">
            {groups.map((group) => (
              <li key={group.slug}>
                <LocalizedClientLink
                  href={`/hall?category=${encodeURIComponent(group.slug)}`}
                  className="flex h-full items-center justify-between gap-4 rounded-rounded border border-ui-border-base bg-white p-4 hover:shadow-elevation-card-hover"
                >
                  <div className="min-w-0">
                    <h3 className="line-clamp-1 text-base-semi">{group.name}</h3>
                    <p className="mt-1 text-small-regular text-ui-fg-subtle">
                      {group.products.length} products from {group.shops.length} shops
                    </p>
                  </div>
                  <Badge>{group.products.length}</Badge>
                </LocalizedClientLink>
              </li>
            ))}
          </ul>
        </section>
      </section>
    </main>
  )
}

const CategoryFeature = ({
  group,
  currentUser,
}: {
  group: CategoryGroup
  currentUser?: Account | null
}) => {
  const previewProducts = group.products.slice(0, CATEGORY_PREVIEW_COUNT)

  return (
    <article className="h-full rounded-rounded border border-ui-border-base bg-white p-5">
      <div className="flex items-start justify-between gap-4">
        <LocalizedClientLink href={`/hall?category=${encodeURIComponent(group.slug)}`}>
          <h3 className="text-base-semi">{group.name}</h3>
          <p className="mt-1 text-small-regular text-ui-fg-subtle">
            {group.products.length} products from {group.shops.length} shops
          </p>
        </LocalizedClientLink>
        <Badge>{group.products.length}</Badge>
      </div>

      <ul className="mt-4 grid grid-cols-2 gap-3 small:grid-cols-5">
        {previewProducts.map((product) => (
          <li key={product.id ?? backendProductName(product)}>
            <CategoryProductPreview product={product} currentUser={currentUser} />
          </li>
        ))}
      </ul>
    </article>
  )
}

const CategoryProductPreview = ({
  product,
  currentUser,
}: {
  product: BackendProduct
  currentUser?: Account | null
}) => {
  const imageUrl = getProductImageUrl(product)
  const name = backendProductName(product)

  return (
    <LocalizedClientLink href={productHref(product, currentUser)} className="group block min-w-0">
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
      <h4 className="mt-2 line-clamp-2 text-small-regular text-ui-fg-base">
        {name}
      </h4>
      <p className="mt-1 text-small-regular text-ui-fg-muted">
        {formatBackendMoney(backendProductPrice(product))}
      </p>
    </LocalizedClientLink>
  )
}

function buildCategoryGroups(data: BackendHallPayload): CategoryGroup[] {
  const groups = new Map<string, CategoryGroup>()

  data.categories.forEach((category) => {
    groups.set(category.name, {
      name: category.name,
      slug: category.slug,
      products: [],
      shops: [],
    })
  })

  data.sections.forEach((section) => {
    section.products.forEach((product) => {
      const name = backendCategoryName(product.category)
      const slug = data.categories.find((category) => category.name === name)?.slug ?? name
      const group =
        groups.get(name) ??
        {
          name,
          slug,
          products: [],
          shops: [],
        }

      group.products.push(product)
      if (!group.shops.includes(section.shop.name)) {
        group.shops.push(section.shop.name)
      }
      groups.set(name, group)
    })
  })

  return Array.from(groups.values()).sort((a, b) => {
    if (b.products.length !== a.products.length) {
      return b.products.length - a.products.length
    }
    return a.name.localeCompare(b.name)
  })
}

function getProductImageUrl(product: BackendProduct): string | null {
  return (
    product.thumbnail ||
    product.images?.[0]?.url ||
    product.images?.[0]?.image_url ||
    null
  )
}

export default CatlogTemplate
