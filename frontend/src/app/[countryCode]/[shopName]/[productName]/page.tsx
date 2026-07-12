import { Metadata } from "next"
import { notFound } from "next/navigation"
import { Badge, Button } from "@medusajs/ui"
import LocalizedClientLink from "@modules/common/components/localized-client-link"
import ProductChoicePanel from "@modules/products/components/product-choice-panel"
import ProductImageCarousel from "@modules/products/components/product-image-carousel"

import { addCartItem, listProducts } from "../../../../api/backend"
import { retrieveCustomer } from "@lib/data/customer"
import {
  backendCategoryName,
  backendProductAvailableCount,
  backendProductName,
  backendProductPrice,
  formatBackendMoney,
  unwrapBackendValue,
} from "../../../../lib/backend-native"
import { productMatchesRoute } from "../../../../lib/marketplace-routes"

type Props = {
  params: Promise<{
    countryCode: string
    shopName: string
    productName: string
  }>
}

export const dynamic = "force-dynamic"

async function findRouteProduct(shopName: string, productName: string) {
  const products = await listProducts(shopName).catch(() => listProducts())
  return products.find((product) => productMatchesRoute(product, productName))
}

export async function generateMetadata(props: Props): Promise<Metadata> {
  const { shopName, productName } = await props.params
  const product = await findRouteProduct(shopName, productName)

  if (!product) {
    return {
      title: "Product | Shopping Web",
    }
  }

  return {
    title: `${backendProductName(product)} | Shopping Web`,
    description: unwrapBackendValue(product.description),
  }
}

export default async function UsernameProductPage(props: Props) {
  const { countryCode, shopName, productName } = await props.params
  const [currentUser, product] = await Promise.all([
    retrieveCustomer(),
    findRouteProduct(shopName, productName),
  ])

  if (!product) {
    notFound()
  }

  const username = encodeURIComponent(currentUser?.user_name ?? countryCode)
  const hallPath = currentUser ? `/customer/${username}/hall` : "/hall"
  const shopsPath = `/${username}/shops`
  const catlogPath = `/${username}/catlog`
  const shopPath = `/${username}/${shopName}`

  async function addProductToCart() {
    "use server"
    await addCartItem({
      product_name: backendProductName(product!),
      quantity: 1,
    })
  }

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
            <LocalizedClientLink className="hover:text-ui-fg-base" href={shopsPath}>
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

      <div className="content-container py-4">
        <LocalizedClientLink
          href={shopPath}
          className="text-small-regular text-ui-fg-subtle hover:text-ui-fg-base"
        >
          Back to {product.shop?.shop_name ?? "shop"}
        </LocalizedClientLink>
      </div>

      <section
        className="content-container flex flex-col gap-8 py-4 small:flex-row small:items-start large:gap-x-12"
        data-testid="product-container"
      >
        <div className="flex w-full flex-col gap-y-5 small:sticky small:top-24 small:max-w-[300px]">
          <div>
            <p className="txt-medium text-ui-fg-muted">
              {backendCategoryName(product.category)}
            </p>
            <h1 className="mt-2 txt-xlarge-plus text-ui-fg-base">
              {backendProductName(product)}
            </h1>
            <p className="mt-4 txt-medium text-ui-fg-subtle">
              {unwrapBackendValue(product.description)}
            </p>
          </div>
          {product.shop?.shop_name && <Badge>{product.shop.shop_name}</Badge>}
        </div>

        <div className="block w-full">
          <ProductImageCarousel
            images={product.images ?? []}
            fallbackAlt={backendProductName(product)}
          />
        </div>

        <div className="flex w-full flex-col gap-y-6 small:sticky small:top-24 small:max-w-[300px]">
          <div className="txt-xlarge-plus text-ui-fg-base">
            {formatBackendMoney(backendProductPrice(product))}
          </div>
          <p className="txt-small text-ui-fg-muted">
            {backendProductAvailableCount(product)} available
          </p>
          <ProductChoicePanel
            product={product}
            fallbackSizes={extractSizeChoices(unwrapBackendValue(product.description))}
          />
          <form action={addProductToCart}>
            <Button
              type="submit"
              variant="primary"
              className="h-10 w-full"
              disabled={backendProductAvailableCount(product) < 1}
              data-testid="add-product-button"
            >
              Add to cart
            </Button>
          </form>
        </div>
      </section>
    </main>
  )
}

function extractSizeChoices(description: string) {
  const sizes = description.match(/\b(?:XXS|XS|S|M|L|XL|XXL)\b/g) ?? []
  const ordered = ["XXS", "XS", "S", "M", "L", "XL", "XXL"]
  const present = new Set(sizes)

  return ordered.filter((size) => present.has(size))
}
