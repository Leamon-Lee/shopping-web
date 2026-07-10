import { redirect } from "next/navigation"

export default async function CountryStore(props: {
  params: Promise<{ countryCode: string }>
}) {
  await props.params
  redirect("/shop")
}
