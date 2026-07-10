import CustomerPanel from "@modules/customer/templates/customer-panel"
import { getCustomerPanel } from "../../api/backend"
import { Metadata } from "next"

export const metadata: Metadata = {
  title: "Customer Panel",
  description: "Customer dashboard and shopping tools.",
}

export default async function CustomerPage() {
  await getCustomerPanel()
  return <CustomerPanel />
}
