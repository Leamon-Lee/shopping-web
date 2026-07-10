import { managerLinks, managerStats } from "@modules/route-reference/route-config"
import RoleRoutePage from "@modules/route-reference/templates/role-route-page"

export default async function ManagerDashboardPage(props: { params: Promise<{ username: string }> }) {
  const { username } = await props.params
  const activePath = `/manager/${username}/dashboard`
  return <RoleRoutePage eyebrow="Manager" title="Dashboard" description="Track shop health, orders, products, analytics, and income." username={username} activePath={activePath} links={managerLinks(username)} stats={managerStats} />
}
