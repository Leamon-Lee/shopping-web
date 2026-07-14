import { Metadata } from "next"
import { notFound } from "next/navigation"
import { Badge } from "@medusajs/ui"
import LocalizedClientLink from "@modules/common/components/localized-client-link"

import { getHall, listProducts } from "../../../api/backend"
import { retrieveCustomer } from "@lib/data/customer"
import {
  backendCategoryName,
  backendProductName,
  backendProductPrice,
  formatBackendMoney,
} from "../../../lib/backend-native"
import { productHref } from "../../../lib/marketplace-routes"
import { cartHrefForUsername } from "../../../lib/cart-url"

type Props = {
  params: Promise<{ countryCode: string; shopName: string }>
}

export const dynamic = "force-dynamic"

export async function generateMetadata(props: Props): Promise<Metadata> {
  const { shopName } = await props.params
  const data = await getHall()
  const shop = data.shops.find((item) => item.slug === shopName)

  return {
    title: `${shop?.name ?? shopName} | Shop`,
    description: `Browse products from ${shop?.name ?? shopName}.`,
  }
}

export default async function UsernameShopPage(props: Props) {
  const { countryCode, shopName } = await props.params
  const [data, currentUser, products] = await Promise.all([
    getHall(),
    retrieveCustomer(),
    listProducts(shopName),
  ])
  const shop = data.shops.find((item) => item.slug === shopName)

  if (!shop) {
    notFound()
  }

  const username = encodeURIComponent(currentUser?.user_name ?? countryCode)
  const hallPath = currentUser ? `/${username}/hall` : "/hall"
  const shopsPath = `/${username}/shops`
  const catlogPath = `/${username}/catlog`
  const cartPath = cartHrefForUsername(currentUser?.user_name ?? countryCode)

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
            <LocalizedClientLink className="text-ui-fg-base" href={shopsPath}>
              Shops
            </LocalizedClientLink>
            <LocalizedClientLink className="hover:text-ui-fg-base" href={catlogPath}>
              Catlog
            </LocalizedClientLink>
          </nav>
          <div className="flex items-center gap-x-4">
            <LocalizedClientLink href={cartPath} className="hover:text-ui-fg-base">
              Cart
            </LocalizedClientLink>
            {currentUser ? (
              <LocalizedClientLink
                href={`/customer/${username}`}
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
        <div className="mb-6 flex flex-col gap-3 border-b border-ui-border-base pb-6 small:flex-row small:items-end small:justify-between">
          <div>
            <p className="txt-xsmall-plus uppercase text-ui-fg-muted">Shop</p>
            <h1 className="mt-2 text-2xl-semi">{shop.name}</h1>
            <p className="mt-2 max-w-2xl text-small-regular text-ui-fg-subtle">
              {shop.categories.slice(0, 8).join(", ") || "Marketplace shop"}
            </p>
          </div>
          <div className="flex gap-2">
            <Badge>{products.length} products</Badge>
            <Badge>{shop.categories.length} categories</Badge>
          </div>
        </div>

        <ul className="grid grid-cols-2 gap-4 small:grid-cols-3 medium:grid-cols-5">
          {products.map((product) => (
            <li key={product.id ?? backendProductName(product)}>
              <LocalizedClientLink
                href={productHref(product, currentUser, shop.slug)}
                className="group block"
              >
                <div className="aspect-square overflow-hidden rounded-rounded bg-ui-bg-subtle">
                  {getProductImageUrl(product) ? (
                    <img
                      src={getProductImageUrl(product) ?? ""}
                      alt={backendProductName(product)}
                      className="h-full w-full object-cover transition-transform duration-150 group-hover:scale-[1.03]"
                      loading="lazy"
                      decoding="async"
                    />
                  ) : null}
                </div>
                <h2 className="mt-3 line-clamp-2 text-small-regular text-ui-fg-base">
                  {backendProductName(product)}
                </h2>
                <div className="mt-1 flex items-center justify-between gap-2 text-small-regular text-ui-fg-muted">
                  <span className="line-clamp-1">
                    {backendCategoryName(product.category)}
                  </span>
                  <span className="shrink-0">
                    {formatBackendMoney(backendProductPrice(product))}
                  </span>
                </div>
              </LocalizedClientLink>
            </li>
          ))}
        </ul>
      </section>
    </main>
  )
}

function getProductImageUrl(
  product: Awaited<ReturnType<typeof listProducts>>[number]
) {
  return (
    product.thumbnail ||
    product.images?.[0]?.url ||
    product.images?.[0]?.image_url ||
    null
  )
}
