import { getHall } from "../../api/backend"
import { retrieveCustomer } from "@lib/data/customer"
import CatlogTemplate from "@modules/customer/templates/catlog"
import { Metadata } from "next"

export const metadata: Metadata = {
  title: "Catlog",
  description: "Find products by category.",
}

export const dynamic = "force-dynamic"

export default async function CatlogPage() {
  const [data, currentUser] = await Promise.all([getHall(), retrieveCustomer()])

  return <CatlogTemplate data={data} currentUser={currentUser} />
}
