import { redirect } from "next/navigation"

export default async function CountryProduct(props: {
  params: Promise<{ countryCode: string; handle: string }>
}) {
  const { handle } = await props.params
  redirect(`/shop/${handle}`)
}
