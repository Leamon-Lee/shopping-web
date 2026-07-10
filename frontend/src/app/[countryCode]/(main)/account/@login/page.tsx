import { redirect } from "next/navigation"

export default async function CountryLogin(props: {
  params: Promise<{ countryCode: string }>
}) {
  await props.params
  redirect("/auth/login")
}
