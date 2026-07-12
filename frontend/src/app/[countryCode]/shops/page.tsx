import { getHall } from "../../../api/backend"
import { retrieveCustomer } from "@lib/data/customer"
import ShopsTemplate from "@modules/customer/templates/shops"
import { Metadata } from "next"

export const metadata: Metadata = {
  title: "Shops",
  description: "Browse all marketplace shops.",
}

export const dynamic = "force-dynamic"

export default async function UsernameShopsPage(props: {
  params: Promise<{ countryCode: string }>
}) {
  const { countryCode } = await props.params
  const [data, currentUser] = await Promise.all([getHall(), retrieveCustomer()])

  return (
    <ShopsTemplate
      data={data}
      currentUser={currentUser}
      activeShopPath={`/${countryCode}/shops`}
    />
  )
}
