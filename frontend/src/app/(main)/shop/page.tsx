import { Metadata } from "next"

import { SortOptions } from "@modules/store/components/refinement-list/sort-products"
import StoreTemplate from "@modules/store/templates"

export const metadata: Metadata = {
  title: "Shop",
  description: "Explore all products.",
}

type Props = {
  searchParams: Promise<{
    sortBy?: SortOptions
    page?: string
    shop?: string
  }>
}

export default async function ShopPage(props: Props) {
  const { sortBy, page, shop } = await props.searchParams

  return (
    <StoreTemplate
      sortBy={sortBy}
      page={page}
      shop={shop}
      countryCode="cn"
    />
  )
}
