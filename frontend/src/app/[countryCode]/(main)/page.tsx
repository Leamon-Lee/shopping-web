import { Metadata } from "next"

import { backendProductFixtures } from "../../../api/backend-fixtures"
import { mapBackendProductToFrontendProduct } from "../../../adapters/backend/product"
import Hero from "@modules/home/components/hero"

export const metadata: Metadata = {
  title: "Shopping Web",
  description: "A standalone ecommerce frontend powered by Next.js.",
}

export default async function Home(props: {
  params: Promise<{ countryCode: string }>
}) {
  await props.params
  const products = backendProductFixtures.map(mapBackendProductToFrontendProduct)

  return (
    <>
      <Hero />
      <section className="content-container py-16">
        <div className="mb-8 flex items-end justify-between">
          <div>
            <p className="text-small-regular text-ui-fg-muted">Featured</p>
            <h2 className="text-2xl text-ui-fg-base">New arrivals</h2>
          </div>
          <a className="text-small-regular text-ui-fg-subtle hover:text-ui-fg-base" href="/us/store">
            View store
          </a>
        </div>
        <ul className="grid grid-cols-1 gap-6 small:grid-cols-3">
          {products.map((product) => (
            <li
              className="border border-ui-border-base bg-ui-bg-base p-6"
              key={product.name}
            >
              <div className="mb-6 aspect-[4/3] bg-ui-bg-subtle" />
              <p className="text-small-regular text-ui-fg-muted">
                {product.category.name}
              </p>
              <div className="mt-2 flex items-center justify-between">
                <h3 className="text-base-regular text-ui-fg-base">
                  {product.name}
                </h3>
                <span className="text-base-regular text-ui-fg-subtle">
                  {product.displayPrice}
                </span>
              </div>
              <p className="mt-4 text-small-regular text-ui-fg-muted">
                {product.availableItemCount} available
              </p>
            </li>
          ))}
        </ul>
      </section>
    </>
  )
}
