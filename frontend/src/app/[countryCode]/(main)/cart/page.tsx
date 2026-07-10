import { redirect } from "next/navigation"

export default async function CountryCart(props: {
  params: Promise<{ countryCode: string }>
}) {
  await props.params
  redirect("/cart")
}
