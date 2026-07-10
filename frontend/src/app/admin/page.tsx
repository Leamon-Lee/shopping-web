import AdminPanel from "@modules/admin/templates/admin-panel"
import { getAdminPanel } from "../../api/backend"

export const metadata = {
  title: "Admin Panel",
  description: "Platform administration dashboard",
}

export default async function AdminPage() {
  await getAdminPanel()
  return <AdminPanel />
}
