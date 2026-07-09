import { Metadata } from "next"

import { listProducts } from "../../../api/backend"
import BackendProductPreview from "@modules/products/components/backend-product-preview"
import Hero from "@modules/home/components/hero"

export const metadata: Metadata = {
  title: "Shopping Web",
  description: "A standalone ecommerce frontend powered by Next.js.",
}

export default async function Home(props: {
  params: Promise<{ countryCode: string }>
}) {
  await props.params
  const products = await listProducts()
    .then((items) => items.slice(0, 3))
    .catch(() => [])

  return (
    <>
      <Hero />
      <section className="content-container py-16">
        <div className="mb-8 flex items-end justify-between">
          <div>
            <p className="text-small-regular text-ui-fg-muted">Featured</p>
            <h2 className="text-2xl text-ui-fg-base">New arrivals</h2>
          </div>
          <a className="text-small-regular text-ui-fg-subtle hover:text-ui-fg-base" href="./store">
            View store
          </a>
        </div>
        {products.length > 0 ? (
          <ul className="grid grid-cols-1 gap-6 small:grid-cols-3">
            {products.map((product) => (
              <li key={String(product.name)}>
                <BackendProductPreview product={product} isFeatured />
              </li>
            ))}
          </ul>
        ) : (
          <div className="rounded-rounded border border-ui-border-base bg-ui-bg-subtle p-6">
            <p className="text-base-semi text-ui-fg-base">
              Products are unavailable
            </p>
            <p className="mt-2 text-small-regular text-ui-fg-subtle">
              Start the backend service to load featured products.
            </p>
          </div>
        )}
      </section>
    </>
  )
}
