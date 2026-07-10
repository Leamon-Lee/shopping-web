import { getHall } from "../../api/backend"
import HallTemplate from "@modules/customer/templates/hall"
import { Metadata } from "next"

export const metadata: Metadata = {
  title: "Shopping Hall",
  description: "Discover products from different shops.",
}

export default async function HallPage() {
  try {
    const data = await getHall()
    return <HallTemplate data={data} />
  } catch (error) {
    return (
      <main className="content-container py-16">
        <h1 className="text-2xl-semi">Shopping Hall</h1>
        <p className="mt-3 text-base-regular text-ui-fg-subtle">
          Start the backend service and database seed to load shop and product
          data.
        </p>
      </main>
    )
  }
}
