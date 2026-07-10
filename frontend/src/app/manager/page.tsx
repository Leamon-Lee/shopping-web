import ManagerPanel from "@modules/manager/templates/manager-panel"
import { getManagerPanel } from "../../api/backend"
import { Metadata } from "next"

export const metadata: Metadata = {
  title: "Manager Panel",
  description: "Shop manager dashboard",
}

export default async function ManagerPage() {
  await getManagerPanel()
  return <ManagerPanel />
}
