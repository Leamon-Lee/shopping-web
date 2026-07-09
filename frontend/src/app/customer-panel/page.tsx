import CustomerPanel from "@modules/customer/templates/customer-panel"
import { Metadata } from "next"

export const metadata: Metadata = {
  title: "Customer Panel",
  description: "Customer dashboard and shopping tools.",
}

export default function CustomerPanelPage() {
  return <CustomerPanel />
}
