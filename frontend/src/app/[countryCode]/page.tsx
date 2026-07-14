import { notFound, redirect } from "next/navigation"

export default async function CountryHome(props: {
  params: Promise<{ countryCode: string }>
}) {
  const { countryCode } = await props.params
  if (countryCode === "cart") {
    notFound()
  }
  redirect("/")
}
