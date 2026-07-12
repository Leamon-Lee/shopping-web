import { redirect } from "next/navigation"

export default async function UsernameCatalogAliasPage(props: {
  params: Promise<{ countryCode: string }>
}) {
  const { countryCode } = await props.params
  redirect(`/${countryCode}/catlog`)
}
