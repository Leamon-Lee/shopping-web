import { redirect, notFound } from "next/navigation"

import { getHall, listProducts } from "../../../../api/backend"
import { backendProductSlug } from "../../../../lib/backend-native"
import {
  productMatchesRoute,
  productShopSlug,
} from "../../../../lib/marketplace-routes"

type Props = {
  params: Promise<{
    countryCode: string
    productName: string
  }>
}

export const dynamic = "force-dynamic"

export default async function UsernameShopProductAliasPage(props: Props) {
  const { countryCode, productName } = await props.params
  const [products, hall] = await Promise.all([listProducts(), getHall()])
  const product = products.find((item) => productMatchesRoute(item, productName))

  if (!product) {
    notFound()
  }

  const username = encodeURIComponent(decodeURIComponent(countryCode))
  const productSlug = product.slug || backendProductSlug(product)
  const shopSlug =
    hall.shops
      .sort((a, b) => b.slug.length - a.slug.length)
      .find((shop) => productSlug === shop.slug || productSlug.startsWith(`${shop.slug}-`))
      ?.slug ?? productShopSlug(product)

  redirect(`/${username}/${shopSlug}/${productSlug}`)
}
