import LocalizedClientLink from "@modules/common/components/localized-client-link"

const Hero = () => {
  return (
    <section className="border-b border-ui-border-base bg-ui-bg-base">
      <div className="content-container grid min-h-[58vh] items-end gap-10 py-16 small:grid-cols-[1.1fr_0.9fr] small:py-24">
        <div className="max-w-3xl pb-4">
          <p className="text-small-regular uppercase text-ui-fg-muted">
            Online Shopping System
          </p>
          <h1 className="mt-4 text-3xl-regular text-ui-fg-base">
            Discover products from the live catalog.
          </h1>
          <p className="mt-4 text-base-regular text-ui-fg-subtle">
            Browse seeded products, add them to a database-backed cart, and place orders through the FastAPI service.
          </p>
          <div className="mt-8">
            <LocalizedClientLink
              href="/shop"
              className="inline-flex h-10 items-center justify-center rounded-md bg-ui-fg-base px-5 text-small-semi text-ui-bg-base hover:bg-ui-fg-subtle"
            >
              Browse store
            </LocalizedClientLink>
          </div>
        </div>
        <div className="grid gap-3 border-l border-ui-border-base pl-6 text-small-regular text-ui-fg-subtle">
          <div>
            <span className="block text-base-semi text-ui-fg-base">Backend</span>
            FastAPI application services with PostgreSQL persistence.
          </div>
          <div>
            <span className="block text-base-semi text-ui-fg-base">Data</span>
            CSV catalog import and MinIO-hosted product media.
          </div>
          <div>
            <span className="block text-base-semi text-ui-fg-base">Frontend</span>
            Next.js storefront connected directly to the backend API.
          </div>
        </div>
      </div>
    </section>
  )
}

export default Hero
