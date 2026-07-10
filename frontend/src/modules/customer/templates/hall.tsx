"use client"

import { Badge, Button } from "@medusajs/ui"
import Input from "@modules/common/components/input"
import LocalizedClientLink from "@modules/common/components/localized-client-link"
import BackendProductPreview from "@modules/products/components/backend-product-preview"
import { useMemo, useState } from "react"
import type {
  BackendHallPayload,
  BackendHallSection,
  BackendProduct,
  BackendShopSummary,
} from "../../../types/backend"
import {
  backendCategoryName,
  backendProductName,
} from "../../../lib/backend-native"

const HallTemplate = ({ data }: { data: BackendHallPayload }) => {
  const [query, setQuery] = useState("")
  const [shopSlug, setShopSlug] = useState("all")
  const [categorySlug, setCategorySlug] = useState("all")

  const shopBySlug = useMemo(
    () => new Map(data.shops.map((shop) => [shop.slug, shop])),
    [data.shops]
  )

  const filteredProducts = useMemo(() => {
    const normalized = query.trim().toLowerCase()
    const selectedShop = shopBySlug.get(shopSlug)
    const selectedCategory = data.categories.find(
      (category) => category.slug === categorySlug
    )

    return data.products.filter((product) => {
      const productName = backendProductName(product)
      const categoryName = backendCategoryName(product.category)
      const shopName = product.shop?.shop_name ?? ""
      const searchText = [productName, categoryName, shopName]
        .join(" ")
        .toLowerCase()

      return (
        (!normalized || searchText.includes(normalized)) &&
        (!selectedShop || shopName === selectedShop.name) &&
        (!selectedCategory || categoryName === selectedCategory.name)
      )
    })
  }, [categorySlug, data.categories, data.products, query, shopBySlug, shopSlug])

  const filteredSections = useMemo(
    () =>
      data.sections
        .map((section) => ({
          ...section,
          products: section.products.filter((product) =>
            filteredProducts.some((item) => item.id === product.id)
          ),
        }))
        .filter((section) => section.products.length > 0),
    [data.sections, filteredProducts]
  )

  const featuredProducts = filteredProducts.slice(0, 8)

  return (
    <div className="min-h-screen bg-ui-bg-base text-ui-fg-base">
      <header className="sticky top-0 inset-x-0 z-50 group">
        <div className="relative h-16 mx-auto border-b duration-200 bg-white border-ui-border-base">
          <div className="content-container txt-xsmall-plus text-ui-fg-subtle flex items-center justify-between w-full h-full text-small-regular">
            <LocalizedClientLink href="/hall" className="text-ui-fg-base">
              SHOPPING HALL
            </LocalizedClientLink>
            <nav className="hidden items-center gap-x-6 small:flex">
              <a className="hover:text-ui-fg-base" href="#shops">
                Shops
              </a>
              <a className="hover:text-ui-fg-base" href="#categories">
                Categories
              </a>
              <a className="hover:text-ui-fg-base" href="#products">
                Products
              </a>
            </nav>
            <div className="flex items-center gap-x-4">
              <LocalizedClientLink
                href="/cart"
                className="hover:text-ui-fg-base"
              >
                Cart
              </LocalizedClientLink>
              <LocalizedClientLink
                href="/sign-in/customer"
                className="hover:text-ui-fg-base"
              >
                Sign in
              </LocalizedClientLink>
            </div>
          </div>
        </div>
      </header>

      <main className="content-container py-12">
        <section className="grid grid-cols-1 gap-8 border-b border-ui-border-base pb-12 small:grid-cols-[1fr_320px]">
          <div>
            <p className="txt-xsmall-plus uppercase text-ui-fg-muted">
              Marketplace
            </p>
            <h1 className="mt-2 text-3xl-semi text-ui-fg-base">
              Browse every shop in one hall
            </h1>
            <p className="mt-3 max-w-2xl text-base-regular text-ui-fg-subtle">
              Search across Nike, Muji, Uniqlo, Xiaomi, Dell, Haier, and other
              imported shops. Product data, shop index, images, inventory, and
              categories are loaded from the backend database.
            </p>
            <div className="mt-6 max-w-2xl">
              <Input
                label="Search product, shop, or category"
                name="hall-search"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
              />
            </div>
          </div>

          <div className="rounded-rounded border border-ui-border-base bg-white p-5">
            <h2 className="text-base-semi">Hall index</h2>
            <div className="mt-4 grid grid-cols-2 gap-2 text-small-regular">
              <Button variant="secondary" className="h-10 justify-start">
                {data.shops.length} shops
              </Button>
              <Button variant="secondary" className="h-10 justify-start">
                {data.products.length} products
              </Button>
              <Button variant="secondary" className="h-10 justify-start">
                {data.categories.length} categories
              </Button>
              <Button variant="secondary" className="h-10 justify-start">
                Backend live
              </Button>
            </div>
            <p className="mt-4 text-small-regular text-ui-fg-muted">
              The hall is the marketplace entry point. The shop route is used
              for focused product browsing after a shop is selected.
            </p>
          </div>
        </section>

        <section id="shops" className="py-12 border-b border-ui-border-base">
          <div className="mb-5 flex flex-col gap-3 small:flex-row small:items-end small:justify-between">
            <div>
              <p className="txt-xsmall-plus uppercase text-ui-fg-muted">
                Shops
              </p>
              <h2 className="mt-2 text-xl-semi">Browse by shop</h2>
            </div>
            <Badge>{data.shops.length} active shops</Badge>
          </div>
          <div className="grid grid-cols-1 gap-4 small:grid-cols-3 medium:grid-cols-4">
            {data.shops.map((shop) => (
              <ShopCard
                key={shop.id}
                shop={shop}
                active={shopSlug === shop.slug}
                onSelect={() => setShopSlug(shop.slug)}
              />
            ))}
          </div>
        </section>

        <section
          id="categories"
          className="py-12 border-b border-ui-border-base"
        >
          <div className="mb-5">
            <p className="txt-xsmall-plus uppercase text-ui-fg-muted">
              Categories
            </p>
            <h2 className="mt-2 text-xl-semi">Product index</h2>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button
              variant={categorySlug === "all" ? "primary" : "secondary"}
              className="h-10"
              onClick={() => setCategorySlug("all")}
            >
              All categories
            </Button>
            {data.categories.map((category) => (
              <Button
                key={category.slug}
                variant={
                  categorySlug === category.slug ? "primary" : "secondary"
                }
                className="h-10"
                onClick={() => setCategorySlug(category.slug)}
              >
                {category.name}
              </Button>
            ))}
          </div>
        </section>

        <section className="grid grid-cols-1 gap-8 py-12 small:grid-cols-[260px_1fr]">
          <aside className="small:sticky small:top-24 small:self-start">
            <div className="rounded-rounded border border-ui-border-base bg-white p-5">
              <h2 className="text-base-semi">Refine</h2>
              <div className="mt-4 flex flex-col gap-4">
                <label className="flex flex-col gap-2 text-small-regular text-ui-fg-subtle">
                  Shop
                  <select
                    value={shopSlug}
                    onChange={(event) => setShopSlug(event.target.value)}
                    className="h-10 rounded-rounded border border-ui-border-base bg-ui-bg-field px-3 text-ui-fg-base outline-none hover:bg-ui-bg-field-hover"
                  >
                    <option value="all">All shops</option>
                    {data.shops.map((shop) => (
                      <option key={shop.id} value={shop.slug}>
                        {shop.name}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="flex flex-col gap-2 text-small-regular text-ui-fg-subtle">
                  Category
                  <select
                    value={categorySlug}
                    onChange={(event) => setCategorySlug(event.target.value)}
                    className="h-10 rounded-rounded border border-ui-border-base bg-ui-bg-field px-3 text-ui-fg-base outline-none hover:bg-ui-bg-field-hover"
                  >
                    <option value="all">All categories</option>
                    {data.categories.map((category) => (
                      <option key={category.slug} value={category.slug}>
                        {category.name}
                      </option>
                    ))}
                  </select>
                </label>
                <Button
                  variant="secondary"
                  className="h-10"
                  onClick={() => {
                    setQuery("")
                    setShopSlug("all")
                    setCategorySlug("all")
                  }}
                >
                  Clear filters
                </Button>
              </div>
            </div>
          </aside>

          <div className="flex flex-col gap-y-12">
            <ProductSection
              id="products"
              title="Featured products"
              description="A cross-shop view of imported inventory from the database."
              products={featuredProducts}
            />

            {filteredSections.map((section) => (
              <ShopProductSection key={section.slug} section={section} />
            ))}

            <ProductSection
              title="All matching products"
              description={`${filteredProducts.length} products match the current hall filters.`}
              products={filteredProducts}
            />
          </div>
        </section>
      </main>
    </div>
  )
}

const ShopCard = ({
  shop,
  active,
  onSelect,
}: {
  shop: BackendShopSummary
  active: boolean
  onSelect: () => void
}) => {
  return (
    <div className="rounded-rounded border border-ui-border-base bg-white p-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h3 className="text-base-semi">{shop.name}</h3>
          <p className="mt-1 text-small-regular text-ui-fg-subtle">
            {shop.product_count} products
          </p>
        </div>
        <Badge>{shop.categories.length} categories</Badge>
      </div>
      <p className="mt-4 min-h-[40px] text-small-regular text-ui-fg-muted">
        {shop.categories.slice(0, 3).join(", ") || "Imported catalog"}
      </p>
      <div className="mt-4 flex gap-2">
        <Button
          variant={active ? "primary" : "secondary"}
          className="h-10 flex-1"
          onClick={onSelect}
        >
          Filter
        </Button>
        <LocalizedClientLink
          href={`/shop?shop=${shop.slug}`}
          className="flex h-10 flex-1 items-center justify-center rounded-rounded border border-ui-border-base text-small-regular hover:shadow-borders-interactive-with-active"
        >
          Open
        </LocalizedClientLink>
      </div>
    </div>
  )
}

const ShopProductSection = ({ section }: { section: BackendHallSection }) => {
  return (
    <ProductSection
      id={`shop-${section.slug}`}
      title={`${section.title} products`}
      description={`${section.shop.product_count} products from ${section.title}.`}
      products={section.products}
    />
  )
}

const ProductSection = ({
  id,
  title,
  description,
  products,
}: {
  id?: string
  title: string
  description: string
  products: BackendProduct[]
}) => {
  return (
    <section id={id}>
      <div className="mb-5 flex flex-col gap-3 small:flex-row small:items-end small:justify-between">
        <div>
          <h2 className="text-xl-semi">{title}</h2>
          <p className="mt-2 max-w-2xl text-small-regular text-ui-fg-subtle">
            {description}
          </p>
        </div>
        <Badge>{products.length} products</Badge>
      </div>
      {products.length > 0 ? (
        <ul className="grid grid-cols-2 w-full small:grid-cols-3 medium:grid-cols-4 gap-x-6 gap-y-8">
          {products.map((product) => (
            <li key={product.id ?? backendProductName(product)}>
              <BackendProductPreview product={product} />
              {product.shop?.shop_name && (
                <p className="mt-2 text-small-regular text-ui-fg-muted">
                  {product.shop.shop_name}
                </p>
              )}
            </li>
          ))}
        </ul>
      ) : (
        <div className="rounded-rounded border border-ui-border-base bg-ui-bg-subtle p-6">
          <h3 className="text-base-semi">No products found</h3>
          <p className="mt-2 text-small-regular text-ui-fg-subtle">
            Try another shop, category, or search term.
          </p>
        </div>
      )}
    </section>
  )
}

export default HallTemplate
