import { getHall } from "../../api/backend"
import { retrieveCustomer } from "@lib/data/customer"
import ShopsTemplate from "@modules/customer/templates/shops"
import { Metadata } from "next"
import { redirect } from "next/navigation"

export const metadata: Metadata = {
  title: "Shops",
  description: "Browse all marketplace shops.",
}

export const dynamic = "force-dynamic"

export default async function ShopsPage() {
  const [data, currentUser] = await Promise.all([getHall(), retrieveCustomer()])

  if (currentUser) {
    redirect(`/${encodeURIComponent(currentUser.user_name)}/shops`)
  }

  return <ShopsTemplate data={data} currentUser={currentUser} />
}
