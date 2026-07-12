import CustomerPanel from "@modules/customer/templates/customer-panel"
import { getCustomerPanel } from "../../../api/backend"
import { Metadata } from "next"

export const metadata: Metadata = {
  title: "Customer Panel",
  description: "Customer dashboard and shopping tools.",
}

export const dynamic = "force-dynamic"

export default async function CustomerPage(props: {
  params: Promise<{ username: string }>
}) {
  await props.params
  await getCustomerPanel()

  return <CustomerPanel />
}
