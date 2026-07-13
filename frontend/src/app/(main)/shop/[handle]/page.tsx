import { Metadata } from "next"
import { notFound } from "next/navigation"

import { addCartItem, listProducts } from "../../../../api/backend"
import {
  backendCategoryName,
  backendProductAvailableCount,
  backendProductName,
  backendProductPrice,
  backendProductSlug,
  formatBackendMoney,
  unwrapBackendValue,
} from "../../../../lib/backend-native"
import Thumbnail from "@modules/products/components/thumbnail"
import AddToCartForm from "@modules/products/components/add-to-cart-form"
import ReviewSection from "@modules/products/components/review-section"

type Props = {
  params: Promise<{ handle: string }>
}

async function getProductBySlug(handle: string) {
  const products = await listProducts()
  return products.find((product) => backendProductSlug(product) === handle)
}

export async function generateMetadata(props: Props): Promise<Metadata> {
  const { handle } = await props.params
  const product = await getProductBySlug(handle)

  if (!product) {
    notFound()
  }

  const name = backendProductName(product)
  return {
    title: `${name} | Shopping Web`,
    description: unwrapBackendValue(product.description),
  }
}

export default async function ProductPage(props: Props) {
  const { handle } = await props.params
  const product = await getProductBySlug(handle)

  if (!product) {
    notFound()
  }

  async function addProductToCart() {
    "use server"
    const identity = product?.variants?.[0]?.id || backendProductName(product!)
    await addCartItem({
      product_name: identity,
      quantity: 1,
    })
  }

  return (
    <>
    <div
      className="content-container flex flex-col small:flex-row small:items-start small:gap-x-8 large:gap-x-12 py-6 relative"
      data-testid="product-container"
    >
      <div className="flex flex-col small:sticky small:top-48 small:py-0 small:max-w-[300px] w-full py-8 gap-y-6">
        <div>
          <p className="txt-medium text-ui-fg-muted">
            {backendCategoryName(product.category)}
          </p>
          <h1 className="txt-xlarge-plus text-ui-fg-base mt-2">
            {backendProductName(product)}
          </h1>
          <p className="txt-medium text-ui-fg-subtle mt-4">
            {unwrapBackendValue(product.description)}
          </p>
        </div>
      </div>
      <div className="block w-full relative">
        <div className="grid grid-cols-1 gap-4">
          <Thumbnail thumbnail={null} images={(product as any).images ?? []} size="full" />
        </div>
      </div>
      <div className="flex flex-col small:sticky small:top-48 small:py-0 small:max-w-[300px] w-full py-8 gap-y-6">
        <div className="txt-xlarge-plus text-ui-fg-base">
          {formatBackendMoney(backendProductPrice(product))}
        </div>
        <p className="txt-small text-ui-fg-muted">
          {backendProductAvailableCount(product)} available
        </p>
        <AddToCartForm
          addAction={addProductToCart}
          disabled={backendProductAvailableCount(product) < 1}
        />
      </div>
    </div>
    <div className="content-container py-6">
      <ReviewSection productIdentity={product.id || product.slug || backendProductSlug(product)} />
    </div>
    </>
  )
}
