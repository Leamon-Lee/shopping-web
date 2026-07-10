import { redirect } from "next/navigation"

export default async function CountryHome(props: {
  params: Promise<{ countryCode: string }>
}) {
  await props.params
  redirect("/")
}
