"use client"

import { Badge, Button } from "@medusajs/ui"
import Input from "@modules/common/components/input"
import { SelectHTMLAttributes, useMemo, useState } from "react"

type HallProduct = {
  name: string
  shop: string
  category: string
  price: string
  rating: string
  reviews: number
  stock: string
  tag: string
  reason: string
}

const products: HallProduct[] = [
  {
    name: "Linen Organizer Bin",
    shop: "Northline Home",
    category: "Home",
    price: "CNY 129",
    rating: "4.8",
    reviews: 126,
    stock: "In stock",
    tag: "Recommended",
    reason: "Because you viewed home storage",
  },
  {
    name: "Desk Lamp Pro",
    shop: "Desk Goods",
    category: "Stationery",
    price: "CNY 368",
    rating: "4.7",
    reviews: 88,
    stock: "Low stock",
    tag: "Best seller",
    reason: "Popular in your workspace category",
  },
  {
    name: "Compact Sling Bag",
    shop: "Everyday Carry Studio",
    category: "Bags",
    price: "CNY 299",
    rating: "4.9",
    reviews: 54,
    stock: "In stock",
    tag: "New arrival",
    reason: "From your favourite shop",
  },
  {
    name: "Cable Dock",
    shop: "Desk Goods",
    category: "Electronics",
    price: "CNY 59",
    rating: "4.5",
    reviews: 203,
    stock: "In stock",
    tag: "Trending",
    reason: "Because you viewed electronics",
  },
  {
    name: "Wool Throw",
    shop: "Northline Home",
    category: "Home",
    price: "CNY 299",
    rating: "4.6",
    reviews: 72,
    stock: "Unavailable",
    tag: "Recently viewed",
    reason: "Recently viewed",
  },
  {
    name: "Aluminum Pen Tray",
    shop: "Desk Goods",
    category: "Stationery",
    price: "CNY 89",
    rating: "4.4",
    reviews: 41,
    stock: "In stock",
    tag: "Recommended",
    reason: "Matches your saved desk setup",
  },
]

const shops = [
  {
    name: "Northline Home",
    description: "Soft textiles and calm storage goods for organized living.",
    rating: "4.8",
    products: 84,
    category: "Home",
  },
  {
    name: "Desk Goods",
    description: "Focused desk accessories, lighting, and daily work tools.",
    rating: "4.7",
    products: 42,
    category: "Stationery",
  },
  {
    name: "Everyday Carry Studio",
    description: "Bags and compact carry gear for daily movement.",
    rating: "4.9",
    products: 28,
    category: "Bags",
  },
]

const categories = [
  { name: "Home", detail: "216 products, 18 shops" },
  { name: "Stationery", detail: "87 products, 9 shops" },
  { name: "Bags", detail: "43 products, 6 shops" },
  { name: "Electronics", detail: "132 products, 14 shops" },
]

const quickLinks = [
  { label: "Hall", href: "/hall" },
  { label: "Shops", href: "#shops" },
  { label: "Categories", href: "#categories" },
]

const sortOptions = [
  "Recommended",
  "Newest",
  "Best Selling",
  "Price Low to High",
  "Price High to Low",
  "Highest Rated",
  "Most Reviewed",
]

const HallTemplate = () => {
  const [query, setQuery] = useState("")
  const [category, setCategory] = useState("all")
  const [shop, setShop] = useState("all")
  const [availability, setAvailability] = useState("all")
  const [accountOpen, setAccountOpen] = useState(false)

  const filteredProducts = useMemo(() => {
    const normalized = query.trim().toLowerCase()

    return products.filter((product) => {
      const matchesQuery =
        !normalized ||
        [product.name, product.shop, product.category, product.tag]
          .join(" ")
          .toLowerCase()
          .includes(normalized)
      const matchesCategory =
        category === "all" || product.category.toLowerCase() === category
      const matchesShop = shop === "all" || product.shop === shop
      const matchesAvailability =
        availability === "all" ||
        product.stock.toLowerCase().replace(" ", "-") === availability

      return matchesQuery && matchesCategory && matchesShop && matchesAvailability
    })
  }, [availability, category, query, shop])

  const recommendedProducts = products.filter((product) =>
    ["Recommended", "Best seller", "Trending"].includes(product.tag)
  )

  return (
    <div className="min-h-screen bg-ui-bg-base text-ui-fg-base">
      <header className="sticky top-0 z-40 border-b border-ui-border-base bg-white">
        <div className="content-container flex h-16 items-center justify-between txt-xsmall-plus text-ui-fg-subtle">
          <a className="text-ui-fg-base hover:text-ui-fg-base" href="/hall">
            SHOPPING HALL
          </a>
          <nav className="hidden items-center gap-x-6 small:flex">
            {quickLinks.map((link) => (
              <a key={link.label} className="hover:text-ui-fg-base" href={link.href}>
                {link.label}
              </a>
            ))}
          </nav>
          <div className="relative flex items-center">
            <button
              type="button"
              onClick={() => setAccountOpen((open) => !open)}
              className="text-small-regular text-ui-fg-subtle hover:text-ui-fg-base"
              aria-expanded={accountOpen}
            >
              Nora Lee
            </button>
            {accountOpen && (
              <div className="absolute right-0 top-10 z-50 w-44 rounded-rounded border border-ui-border-base bg-white p-2 shadow-elevation-card-rest">
                <a
                  className="block rounded-md px-3 py-2 text-small-regular text-ui-fg-subtle hover:bg-ui-bg-subtle hover:text-ui-fg-base"
                  href="/us/cart"
                >
                  Cart
                </a>
                <a
                  className="block rounded-md px-3 py-2 text-small-regular text-ui-fg-subtle hover:bg-ui-bg-subtle hover:text-ui-fg-base"
                  href="/customer-panel"
                >
                  My Orders
                </a>
                <a
                  className="block rounded-md px-3 py-2 text-small-regular text-ui-fg-subtle hover:bg-ui-bg-subtle hover:text-ui-fg-base"
                  href="/customer-panel"
                >
                  Wishlist
                </a>
              </div>
            )}
          </div>
        </div>
      </header>

      <main className="content-container flex flex-col gap-y-12 py-12">
        <section className="grid grid-cols-1 gap-8 border-b border-ui-border-base pb-12 medium:grid-cols-[1fr_320px]">
          <div>
            <p className="txt-xsmall-plus uppercase text-ui-fg-muted">
              Customer shopping hall
            </p>
            <h1 className="mt-2 text-3xl-semi text-ui-fg-base">
              Discover products from every shop
            </h1>
            <p className="mt-3 max-w-2xl text-base-regular text-ui-fg-subtle">
              Search products, shops, categories, brands, and keywords. The hall
              keeps recommendations visible while customers browse across stores.
            </p>
            <div className="mt-6 max-w-2xl">
              <Input
                label="Search product, shop, category, brand, or keyword"
                name="hall-search"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
              />
            </div>
            <div className="mt-4 flex flex-wrap gap-2">
              {categories.map((item) => (
                <button
                  key={item.name}
                  onClick={() => setCategory(item.name.toLowerCase())}
                  className="rounded-md border border-ui-border-base px-3 py-2 text-small-regular text-ui-fg-subtle hover:bg-ui-bg-subtle hover:text-ui-fg-base"
                >
                  {item.name}
                </button>
              ))}
            </div>
          </div>
          <div className="rounded-rounded border border-ui-border-base bg-white p-5">
            <h2 className="text-base-semi">Customer shortcuts</h2>
            <div className="mt-4 grid grid-cols-2 gap-2 text-small-regular">
              <Button variant="secondary" className="h-10 justify-start">
                Cart (3)
              </Button>
              <Button variant="secondary" className="h-10 justify-start">
                Wishlist (12)
              </Button>
              <Button variant="secondary" className="h-10 justify-start">
                Track orders
              </Button>
              <Button variant="secondary" className="h-10 justify-start">
                Preferences
              </Button>
            </div>
            <p className="mt-4 text-small-regular text-ui-fg-muted">
              Signed in as Nora Lee. Recommendations use wishlist, orders,
              browsing history, and selected preferences.
            </p>
          </div>
        </section>

        <section className="grid grid-cols-1 gap-8 small:grid-cols-[260px_1fr]">
          <aside className="small:sticky small:top-24 small:self-start">
            <div className="rounded-rounded border border-ui-border-base bg-white p-5">
              <h2 className="text-base-semi">Filters</h2>
              <div className="mt-4 flex flex-col gap-4">
                <HallSelect
                  name="category-filter"
                  value={category}
                  onChange={(event) => setCategory(event.target.value)}
                >
                  <option value="all">All categories</option>
                  <option value="home">Home</option>
                  <option value="stationery">Stationery</option>
                  <option value="bags">Bags</option>
                  <option value="electronics">Electronics</option>
                </HallSelect>
                <HallSelect
                  name="shop-filter"
                  value={shop}
                  onChange={(event) => setShop(event.target.value)}
                >
                  <option value="all">All shops</option>
                  {shops.map((item) => (
                    <option key={item.name} value={item.name}>
                      {item.name}
                    </option>
                  ))}
                </HallSelect>
                <HallSelect
                  name="availability-filter"
                  value={availability}
                  onChange={(event) => setAvailability(event.target.value)}
                >
                  <option value="all">Any availability</option>
                  <option value="in-stock">In stock</option>
                  <option value="low-stock">Low stock</option>
                  <option value="unavailable">Unavailable</option>
                </HallSelect>
                <HallSelect name="sort-filter" defaultValue="Recommended">
                  {sortOptions.map((option) => (
                    <option key={option} value={option}>
                      {option}
                    </option>
                  ))}
                </HallSelect>
                <FilterGroup
                  title="More filters"
                  items={[
                    "Discount",
                    "New arrival",
                    "Best seller",
                    "Recommended",
                    "Product variants",
                    "4 stars and up",
                  ]}
                />
              </div>
            </div>
          </aside>

          <div className="flex flex-col gap-y-12">
            <ProductSection
              title="Recommended for you"
              description="Personalised recommendations based on wishlist, viewed categories, favourite shops, and order history."
              items={recommendedProducts}
            />

            <section>
              <div className="mb-5 flex flex-col justify-between gap-3 small:flex-row small:items-end">
                <div>
                  <p className="txt-xsmall-plus uppercase text-ui-fg-muted">
                    Product discovery
                  </p>
                  <h2 className="mt-2 text-xl-semi">All matching products</h2>
                </div>
                <Badge color="orange">{filteredProducts.length} products</Badge>
              </div>
              {filteredProducts.length ? (
                <ProductGrid items={filteredProducts} />
              ) : (
                <EmptyState
                  title="No products found"
                  description="Try another search term, category, shop, price range, or availability filter."
                />
              )}
            </section>
          </div>
        </section>

        <section id="shops" className="flex flex-col gap-y-5">
          <div>
            <p className="txt-xsmall-plus uppercase text-ui-fg-muted">
              Featured shops
            </p>
            <h2 className="mt-2 text-xl-semi">Browse by shop</h2>
          </div>
          <div className="grid grid-cols-1 gap-4 small:grid-cols-3">
            {shops.map((shopItem) => (
              <ShopCard key={shopItem.name} shop={shopItem} />
            ))}
          </div>
        </section>

        <section id="categories" className="flex flex-col gap-y-5">
          <div>
            <p className="txt-xsmall-plus uppercase text-ui-fg-muted">
              Categories
            </p>
            <h2 className="mt-2 text-xl-semi">Browse platform categories</h2>
          </div>
          <div className="grid grid-cols-1 gap-4 small:grid-cols-4">
            {categories.map((item) => (
              <button
                key={item.name}
                onClick={() => setCategory(item.name.toLowerCase())}
                className="rounded-rounded border border-ui-border-base bg-white p-5 text-left hover:shadow-borders-interactive-with-active"
              >
                <p className="text-base-semi">{item.name}</p>
                <p className="mt-2 text-small-regular text-ui-fg-subtle">
                  {item.detail}
                </p>
              </button>
            ))}
          </div>
        </section>

        <ProductSection
          title="New from Fresh Home Market"
          description="A shop-grouped section reserved for new products from selected shops."
          items={products.filter((product) => product.category === "Home")}
        />
      </main>
    </div>
  )
}

const ProductSection = ({
  title,
  description,
  items,
}: {
  title: string
  description: string
  items: HallProduct[]
}) => {
  return (
    <section>
      <div className="mb-5">
        <h2 className="text-xl-semi">{title}</h2>
        <p className="mt-2 max-w-2xl text-small-regular text-ui-fg-subtle">
          {description}
        </p>
      </div>
      {items.length ? (
        <ProductGrid items={items} />
      ) : (
        <EmptyState
          title="No recommended products yet"
          description="Recommendation sections will fill in as the customer browses, saves products, and places orders."
        />
      )}
    </section>
  )
}

const ProductGrid = ({ items }: { items: HallProduct[] }) => {
  return (
    <div className="grid grid-cols-1 gap-x-6 gap-y-8 xsmall:grid-cols-2 medium:grid-cols-3 large:grid-cols-4">
      {items.map((product) => (
        <ProductCard key={`${product.shop}-${product.name}`} product={product} />
      ))}
    </div>
  )
}

const ProductCard = ({ product }: { product: HallProduct }) => {
  return (
    <div className="group">
      <a
        href={`/hall?product=${encodeURIComponent(product.name)}`}
        aria-label={`View ${product.name}`}
        className="relative block aspect-[11/14] w-full overflow-hidden bg-ui-bg-subtle p-4 shadow-elevation-card-rest transition-shadow duration-150 ease-in-out group-hover:shadow-elevation-card-hover"
      >
        <div className="flex h-full items-center justify-center border border-dashed border-ui-border-base text-small-regular text-ui-fg-muted">
          Product image
        </div>
      </a>
      <div className="mt-4 flex justify-between gap-3 txt-compact-medium">
        <div className="min-w-0 flex-1">
          <p className="text-ui-fg-base">{product.name}</p>
          <div className="mt-1 flex items-end justify-between gap-3">
            <p className="min-w-0 text-small-regular text-ui-fg-subtle">
              {product.shop}
            </p>
            <div className="flex shrink-0 items-end justify-center gap-2 text-small-regular">
              <span className={getStockTextColor(product.stock)}>
                {product.stock}
              </span>
              <span className={getTagTextColor(product.tag)}>{product.tag}</span>
            </div>
          </div>
        </div>
        <p className="text-ui-fg-muted">{product.price}</p>
      </div>
      <div className="mt-3 flex items-center justify-between gap-3 text-small-regular">
        <span className="text-ui-fg-muted">{product.category}</span>
        <span className={getRatingTextColor(product.rating)}>
          {product.rating} rating
        </span>
        <span className="text-ui-fg-muted">{product.reviews} reviews</span>
      </div>
      <p className="hidden">
        {product.category} · {product.rating} rating · {product.reviews} reviews
      </p>
      <p className="mt-1 text-small-regular text-ui-fg-subtle">
        {product.reason}
      </p>
      <div className="mt-4 flex flex-col gap-2">
        <Button className="h-10 w-full">Add to Cart</Button>
      </div>
    </div>
  )
}

const getStockTextColor = (stock: string) => {
  if (stock === "In stock") {
    return "text-emerald-700"
  }
  if (stock === "Low stock") {
    return "text-violet-700"
  }
  return "text-rose-600"
}

const getTagTextColor = (tag: string) => {
  if (tag === "Best seller" || tag === "Trending") {
    return "text-orange-700"
  }
  if (tag === "New arrival") {
    return "text-violet-700"
  }
  return "text-orange-700"
}

const getRatingTextColor = (rating: string) => {
  const value = Number(rating)
  if (value >= 4.7) {
    return "text-emerald-700"
  }
  if (value >= 4.3) {
    return "text-orange-700"
  }
  if (value >= 3) {
    return "text-violet-700"
  }
  return "text-rose-600"
}

const ShopCard = ({ shop }: { shop: (typeof shops)[number] }) => {
  return (
    <div className="rounded-rounded border border-ui-border-base bg-white p-5">
      <div className="flex items-start gap-4">
        <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-rounded border border-ui-border-base bg-ui-bg-subtle text-base-semi">
          {shop.name
            .split(" ")
            .map((part) => part[0])
            .join("")
            .slice(0, 2)}
        </div>
        <div>
          <h3 className="text-base-semi">{shop.name}</h3>
          <p className="mt-1 text-small-regular text-ui-fg-subtle">
            {shop.description}
          </p>
        </div>
      </div>
      <div className="mt-4 flex flex-wrap gap-2">
        <Badge color="green">{shop.rating} rating</Badge>
        <Badge color="orange">{shop.category}</Badge>
        <Badge color="green">{shop.products} products</Badge>
      </div>
      <Button variant="secondary" className="mt-4 h-10 w-full">
        Visit shop
      </Button>
    </div>
  )
}

const HallSelect = ({
  children,
  className = "",
  ...props
}: SelectHTMLAttributes<HTMLSelectElement>) => {
  return (
    <div className="relative">
      <select
        {...props}
        className={`h-9 w-full appearance-none bg-transparent px-0 pr-7 text-small-regular text-ui-fg-base outline-none hover:text-ui-fg-subtle ${className}`}
      >
        {children}
      </select>
      <span className="pointer-events-none absolute inset-y-0 right-0 flex items-center text-ui-fg-muted">
        v
      </span>
    </div>
  )
}

const FilterGroup = ({ title, items }: { title: string; items: string[] }) => {
  return (
    <div>
      <p className="text-small-semi text-ui-fg-base">{title}</p>
      <div className="mt-3 flex flex-col gap-2">
        {items.map((item) => (
          <label
            key={item}
            className="flex items-center gap-2 text-small-regular text-ui-fg-subtle"
          >
            <input type="checkbox" className="h-4 w-4" />
            {item}
          </label>
        ))}
      </div>
    </div>
  )
}

const EmptyState = ({
  title,
  description,
}: {
  title: string
  description: string
}) => {
  return (
    <div className="rounded-rounded border border-ui-border-base bg-ui-bg-subtle p-6">
      <h3 className="text-base-semi">{title}</h3>
      <p className="mt-2 text-small-regular text-ui-fg-subtle">
        {description}
      </p>
    </div>
  )
}

export default HallTemplate
