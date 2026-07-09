import ManagerPanel from "@modules/manager/templates/manager-panel"
import { Metadata } from "next"

export const metadata: Metadata = {
  title: "Manager Panel",
  description: "Shop manager dashboard",
}

export default function ManagerPage() {
  return <ManagerPanel />
}
