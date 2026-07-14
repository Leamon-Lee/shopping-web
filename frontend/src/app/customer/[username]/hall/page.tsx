import {
  getHall,
  getHallProducts,
  getUserRecommendations,
} from "../../../../api/backend"
import HallTemplate from "@modules/customer/templates/hall"
import { Metadata } from "next"
import { retrieveCustomer } from "@lib/data/customer"

const INITIAL_PRODUCT_LIMIT = 30

export const dynamic = "force-dynamic"

export const metadata: Metadata = {
  title: "Shopping Hall",
  description: "Discover products from different shops.",
}

export default async function CustomerHallPage(props: {
  params: Promise<{ username: string }>
}) {
  const { username } = await props.params
  const userKey = decodeURIComponent(username)

  try {
    const [data, initialFeed, currentUser, recommended] = await Promise.all([
      getHall(),
      getHallProducts({ limit: INITIAL_PRODUCT_LIMIT, offset: 0 }),
      retrieveCustomer(),
      getUserRecommendations(userKey).catch(() => null),
    ])

    return (
      <HallTemplate
        data={data}
        initialProducts={initialFeed.products}
        initialHasMore={initialFeed.has_more}
        currentUser={currentUser}
        likedProducts={recommended?.items?.map((item) => item.product) ?? []}
        recommendationUserKey={userKey}
      />
    )
  } catch {
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
