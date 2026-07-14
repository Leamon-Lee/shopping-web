"use client"

import { Button, clx } from "@medusajs/ui"
import Input from "@modules/common/components/input"
import LocalizedClientLink from "@modules/common/components/localized-client-link"
import { useIntersection } from "@lib/hooks/use-in-view"
import { useSearchParams } from "next/navigation"
import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import type { WheelEvent } from "react"
import {
  getHallProducts,
  getUserRecommendations,
  trackEvent,
} from "../../../api/backend-client"
import type {
  Account,
  BackendHallPayload,
  BackendProduct,
} from "../../../types/backend"
import {
  backendCategoryName,
  backendProductName,
  backendProductPrice,
  formatBackendMoney,
} from "../../../lib/backend-native"
import { productHref } from "../../../lib/marketplace-routes"
import { signout } from "@lib/data/customer"

const BATCH_SIZE = 30
const SEARCH_DEBOUNCE_MS = 300
const IMAGE_PRELOAD_COUNT = 18

function uniqueProducts(products: BackendProduct[]) {
  const seen = new Set<string>()

  return products.filter((product) => {
    const key = product.id ?? backendProductName(product)
    if (seen.has(key)) return false

    seen.add(key)
    return true
  })
}

function distributeIntoColumns(products: BackendProduct[], columnCount: number) {
  const columns: Array<Array<{ product: BackendProduct; index: number }>> =
    Array.from({ length: columnCount }, () => [])

  products.forEach((product, index) => {
    columns[index % columnCount].push({ product, index })
  })

  return columns
}

function useResponsiveColumnCount() {
  const [columnCount, setColumnCount] = useState(5)

  useEffect(() => {
    const updateColumnCount = () => {
      if (window.innerWidth >= 1280) {
        setColumnCount(5)
      } else if (window.innerWidth >= 1024) {
        setColumnCount(4)
      } else {
        setColumnCount(2)
      }
    }

    updateColumnCount()
    window.addEventListener("resize", updateColumnCount)

    return () => window.removeEventListener("resize", updateColumnCount)
  }, [])

  return columnCount
}

const HallTemplate = ({
  data,
  initialProducts: serverInitialProducts,
  initialHasMore,
  currentUser,
  likedProducts = [],
  recommendationUserKey: serverRecommendationUserKey,
}: {
  data: BackendHallPayload
  initialProducts?: BackendProduct[]
  initialHasMore?: boolean
  currentUser?: Account | null
  likedProducts?: BackendProduct[]
  recommendationUserKey?: string | null
}) => {
  const searchParams = useSearchParams()
  const shops = Array.isArray(data?.shops) ? data.shops : []
  const categories = Array.isArray(data?.categories) ? data.categories : []
  const initialShopSlug = searchParams.get("shop") ?? "all"
  const initialCategorySlug = searchParams.get("category") ?? "all"
  const accountPath = currentUser
    ? currentUser.role === "manager" ? "/manager"
    : currentUser.role === "admin" ? "/admin"
    : `/customer/${encodeURIComponent(currentUser.user_name)}`
    : null
  const customerBasePath = currentUser && currentUser.role !== "manager" && currentUser.role !== "admin"
    ? `/customer/${encodeURIComponent(currentUser.user_name)}`
    : null
  const hallPath = customerBasePath ? `${customerBasePath}/hall` : "/hall"
  const hallInitialProducts = useMemo(
    () => {
      if (Array.isArray(serverInitialProducts) && serverInitialProducts.length) {
        return serverInitialProducts
      }

      return (Array.isArray(data?.sections) ? data.sections : []).flatMap(
        (section) => section.products
      )
    },
    [data, serverInitialProducts]
  )
  const shouldBlendInitialRecommendations =
    initialShopSlug === "all" && initialCategorySlug === "all"
  const initialProducts = useMemo(
    () =>
      shouldBlendInitialRecommendations
        ? uniqueProducts([...likedProducts, ...hallInitialProducts])
        : hallInitialProducts,
    [hallInitialProducts, likedProducts, shouldBlendInitialRecommendations]
  )
  const productCount = data?.product_count ?? 0

  const [query, setQuery] = useState("")
  const [debouncedQuery, setDebouncedQuery] = useState("")
  const [shopSlug, setShopSlug] = useState(initialShopSlug)
  const [categorySlug, setCategorySlug] = useState(initialCategorySlug)
  const [products, setProducts] = useState<BackendProduct[]>(initialProducts)
  const [likedFeedProducts, setLikedFeedProducts] = useState<BackendProduct[]>(
    likedProducts
  )
  const [offset, setOffset] = useState(hallInitialProducts.length)
  const [hasMore, setHasMore] = useState(
    initialHasMore ?? hallInitialProducts.length < productCount
  )
  const [loading, setLoading] = useState(false)
  const [initialLoad, setInitialLoad] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const sentinelRef = useRef<HTMLDivElement | null>(null)
  const loadingRef = useRef(false)
  const isVisible = useIntersection(sentinelRef, "900px")
  const recommendationUserKey =
    serverRecommendationUserKey || currentUser?.email || currentUser?.user_name

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedQuery(query.trim())
    }, SEARCH_DEBOUNCE_MS)

    return () => clearTimeout(timer)
  }, [query])

  const refreshLikedProducts = useCallback(async () => {
    if (!recommendationUserKey) return

    try {
      const [recommendations] = await Promise.allSettled([
        getUserRecommendations(recommendationUserKey),
      ])

      if (recommendations.status === "fulfilled") {
        const refreshed = uniqueProducts(
          (recommendations.value.items ?? []).map((item) => item.product)
        )
        if (refreshed.length) {
          setLikedFeedProducts(refreshed)
          if (!debouncedQuery && shopSlug === "all" && categorySlug === "all") {
            setProducts((current) => uniqueProducts([...refreshed, ...current]))
          }
        }
      }
    } catch {
      // Recommendation refresh is best-effort; the main hall feed should stay usable.
    }
  }, [categorySlug, debouncedQuery, recommendationUserKey, shopSlug])

  useEffect(() => {
    setLikedFeedProducts(likedProducts)
  }, [likedProducts])

  useEffect(() => {
    void refreshLikedProducts()

    const handlePageShow = () => {
      void refreshLikedProducts()
    }
    const handleFocus = () => {
      void refreshLikedProducts()
    }

    window.addEventListener("pageshow", handlePageShow)
    window.addEventListener("focus", handleFocus)

    return () => {
      window.removeEventListener("pageshow", handlePageShow)
      window.removeEventListener("focus", handleFocus)
    }
  }, [refreshLikedProducts])

  const fetchPage = useCallback(
    async (nextOffset: number) => {
      if (loadingRef.current) return

      loadingRef.current = true
      setLoading(true)
      setError(null)

      try {
        const result = await getHallProducts({
          q: debouncedQuery || undefined,
          shop: shopSlug !== "all" ? shopSlug : undefined,
          category: categorySlug !== "all" ? categorySlug : undefined,
          limit: BATCH_SIZE,
          offset: nextOffset,
        })

        setProducts((current) =>
          nextOffset === 0
            ? uniqueProducts(result.products)
            : uniqueProducts([...current, ...result.products])
        )
        setOffset(nextOffset + result.products.length)
        setHasMore(result.has_more)
      } catch (err) {
        if (nextOffset === 0) {
          setProducts(initialProducts)
          setOffset(hallInitialProducts.length)
          setHasMore(false)
          setError(
            initialProducts.length > 0
              ? null
              : err instanceof Error
              ? err.message
              : "Failed to load products"
          )
        } else {
          setError(err instanceof Error ? err.message : "Failed to load more")
        }
      } finally {
        loadingRef.current = false
        setLoading(false)
        setInitialLoad(false)
      }
    },
    [categorySlug, debouncedQuery, hallInitialProducts.length, initialProducts, shopSlug]
  )

  useEffect(() => {
    if (!debouncedQuery && shopSlug === "all" && categorySlug === "all") {
      setProducts(initialProducts)
      setOffset(hallInitialProducts.length)
      setHasMore(initialHasMore ?? hallInitialProducts.length < productCount)
      setInitialLoad(false)
      setError(null)
      return
    }

    setInitialLoad(false)
    setProducts(initialProducts)
    setOffset(0)
    setHasMore(true)
    void fetchPage(0)
  }, [
    categorySlug,
    debouncedQuery,
    fetchPage,
    hallInitialProducts.length,
    initialHasMore,
    initialProducts,
    productCount,
    shopSlug,
  ])

  useEffect(() => {
    if (isVisible && hasMore && !loading && !initialLoad) {
      void fetchPage(offset)
    }
  }, [fetchPage, hasMore, initialLoad, isVisible, loading, offset])

  useEffect(() => {
    const loadNearBottom = () => {
      if (!hasMore || initialLoad || loadingRef.current) return

      const distanceToBottom =
        document.documentElement.scrollHeight -
        (window.scrollY + window.innerHeight)

      if (distanceToBottom < 1200) {
        void fetchPage(offset)
      }
    }

    window.addEventListener("scroll", loadNearBottom, { passive: true })
    window.addEventListener("resize", loadNearBottom)
    loadNearBottom()

    return () => {
      window.removeEventListener("scroll", loadNearBottom)
      window.removeEventListener("resize", loadNearBottom)
    }
  }, [fetchPage, hasMore, initialLoad, offset])

  useEffect(() => {
    products.slice(0, IMAGE_PRELOAD_COUNT).forEach((product) => {
      const imageUrl = getProductImageUrl(product)
      if (!imageUrl) return

      const image = new window.Image()
      image.decoding = "async"
      image.src = imageUrl
    })
  }, [products])

  const activeShopName = useMemo(
    () => shops.find((shop) => shop.slug === shopSlug)?.name,
    [shopSlug, shops]
  )
  const activeCategoryName = useMemo(
    () => categories.find((category) => category.slug === categorySlug)?.name,
    [categorySlug, categories]
  )

  const clearFilters = () => {
    setQuery("")
    setDebouncedQuery("")
    setShopSlug("all")
    setCategorySlug("all")
  }

  const activeFilterCount =
    Number(Boolean(debouncedQuery)) +
    Number(shopSlug !== "all") +
    Number(categorySlug !== "all")

  return (
    <div className="min-h-screen bg-ui-bg-base text-ui-fg-base">
      <header className="sticky inset-x-0 top-0 z-50 border-b border-ui-border-base bg-gray-200">
        <div className="content-container flex h-16 items-center justify-between text-small-regular text-ui-fg-subtle">
          <LocalizedClientLink href={hallPath} className="text-ui-fg-base">
            SHOPPING HALL
          </LocalizedClientLink>
          <div className="flex items-center gap-x-4">
            {(!currentUser || (currentUser.role !== "manager" && currentUser.role !== "admin")) && (
              <LocalizedClientLink href="/cart" className="hover:text-ui-fg-base">
                Cart
              </LocalizedClientLink>
            )}
            {currentUser ? (
              <>
                <LocalizedClientLink
                  href={accountPath ?? "/customer"}
                  className="hover:text-ui-fg-base"
                >
                  Account
                </LocalizedClientLink>
                <button
                  type="button"
                  className="hover:text-ui-fg-base"
                  onClick={() => signout()}
                >
                  Log out
                </button>
              </>
            ) : (
              <LocalizedClientLink
                href="/auth/login"
                className="hover:text-ui-fg-base"
              >
                Sign in
              </LocalizedClientLink>
            )}
          </div>
        </div>
      </header>

      <main className="content-container py-8">
        <section className="border-b border-ui-border-base pb-8">
          <div className="flex flex-col gap-5 small:flex-row small:items-end small:justify-between">
            <div className="max-w-3xl">
              <p className="txt-xsmall-plus uppercase text-ui-fg-muted">
                Product discovery
              </p>
              <h1 className="mt-2 text-3xl-semi text-ui-fg-base">
                Recommended products from every shop
              </h1>
              <p className="mt-3 text-base-regular text-ui-fg-subtle">
                Scroll the hall to keep loading products. The feed mixes shops
                and categories so the homepage feels like a product showcase
                instead of a shop directory.
              </p>
            </div>
          </div>

          <div className="mt-6 grid grid-cols-1 gap-3 small:grid-cols-[1fr_auto]">
            <Input
              label="Search products"
              name="hall-search"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
            />
            <Button
              variant="secondary"
              className="h-10 self-end"
              onClick={clearFilters}
              disabled={activeFilterCount === 0}
            >
              Clear
            </Button>
          </div>

          <div id="filters" className="mt-5 flex flex-col gap-4">
            <FilterStrip
              label="Shops"
              allLabel="All shops"
              value={shopSlug}
              items={shops.map((shop) => ({
                label: shop.name,
                value: shop.slug,
                meta: shop.product_count,
              }))}
              onChange={setShopSlug}
            />
            <FilterStrip
              label="Categories"
              allLabel="All categories"
              value={categorySlug}
              items={categories.map((category) => ({
                label: category.name,
                value: category.slug,
              }))}
              onChange={setCategorySlug}
            />
          </div>
        </section>

        <section id="products" className="py-8">
          {likedFeedProducts.length > 0 && (
            <LikedProductsRail
              products={likedFeedProducts}
              currentUser={currentUser}
            />
          )}

          <div className="mb-6 flex flex-col gap-2 small:flex-row small:items-end small:justify-between">
            <div>
              <h2 className="text-xl-semi">Today&apos;s product feed</h2>
              <p className="mt-2 text-small-regular text-ui-fg-subtle">
                {feedSummary(activeShopName, activeCategoryName)}
              </p>
            </div>
          </div>

          {products.length > 0 ? (
            <MasonryProductFeed products={products} currentUser={currentUser} />
          ) : !loading && !initialLoad ? (
            <EmptyFeed onClear={clearFilters} />
          ) : null}

          <div ref={sentinelRef} className="pt-8">
            {loading && (
              <div>
                <p className="text-center text-small-regular text-ui-fg-subtle">
                  Loading products...
                </p>
                <MasonrySkeleton />
              </div>
            )}

            {error && (
              <div className="mx-auto mt-6 max-w-md rounded-rounded border border-ui-border-base bg-ui-bg-subtle p-5 text-center">
                <p className="text-small-regular text-ui-fg-subtle">{error}</p>
                <Button
                  variant="secondary"
                  className="mt-3 h-10"
                  onClick={() => void fetchPage(offset)}
                >
                  Retry
                </Button>
              </div>
            )}

            {!loading && !hasMore && products.length > 0 && (
              <p className="mt-6 text-center text-small-regular text-ui-fg-muted">
                You&apos;ve reached the end of this feed.
              </p>
            )}
          </div>
        </section>
      </main>
    </div>
  )
}

const LikedProductsRail = ({
  products,
  currentUser,
}: {
  products: BackendProduct[]
  currentUser?: Account | null
}) => {
  const visibleProducts = uniqueProducts(products).slice(0, 10)
  const scrollerRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    const scroller = scrollerRef.current
    if (!scroller || visibleProducts.length < 2) return

    const interval = window.setInterval(() => {
      if (!scroller) return
      const atEnd =
        scroller.scrollLeft + scroller.clientWidth >= scroller.scrollWidth - 4
      if (atEnd) {
        scroller.scrollTo({ left: 0, behavior: "smooth" })
      } else {
        scroller.scrollBy({ left: 1, behavior: "auto" })
      }
    }, 35)

    return () => window.clearInterval(interval)
  }, [visibleProducts.length])

  if (!visibleProducts.length) return null

  return (
    <section className="mb-8 border-b border-ui-border-base pb-8">
      <div className="mb-4">
        <div>
          <h2 className="text-xl-semi">Products you may like</h2>
          <p className="mt-2 text-small-regular text-ui-fg-subtle">
            Picked from your reviews, ratings, and shopping activity.
          </p>
        </div>
      </div>
      <div
        ref={scrollerRef}
        className="no-scrollbar flex gap-4 overflow-x-auto pb-1"
      >
        {visibleProducts.map((product, index) => (
          <div
            key={product.id ?? `${backendProductName(product)}-${index}`}
            className="w-[360px] shrink-0"
          >
            <LikedProductCard
              product={product}
              priority={index < 4}
              currentUser={currentUser}
            />
          </div>
        ))}
      </div>
    </section>
  )
}

const LikedProductCard = ({
  product,
  priority,
  currentUser,
}: {
  product: BackendProduct
  priority: boolean
  currentUser?: Account | null
}) => {
  const imageUrl = getProductImageUrl(product)
  const name = backendProductName(product)
  const category = backendCategoryName(product.category)

  return (
    <LocalizedClientLink
      href={productHref(product, currentUser)}
      className="group block"
      onClick={() => trackProductClick(product, "liked_products")}
    >
      <article className="flex h-32 overflow-hidden rounded-rounded border border-ui-border-base bg-white shadow-elevation-card-rest transition-shadow duration-150 group-hover:shadow-elevation-card-hover">
        <div className="h-32 w-32 shrink-0 overflow-hidden bg-ui-bg-subtle">
          {imageUrl ? (
            <img
              src={imageUrl}
              alt={name}
              className="h-full w-full object-cover"
              loading={priority ? "eager" : "lazy"}
              decoding="async"
              fetchPriority={priority ? "high" : "auto"}
            />
          ) : (
            <div className="h-full w-full bg-ui-bg-subtle" />
          )}
        </div>
        <div className="flex min-w-0 flex-1 flex-col justify-between p-3">
          <div>
            <h3 className="line-clamp-2 text-small-regular text-ui-fg-base">
              {name}
            </h3>
            <p className="mt-2 line-clamp-1 text-small-regular text-ui-fg-muted">
              {category}
            </p>
          </div>
          <div className="flex items-center justify-between gap-3 text-small-regular">
            <span className="font-medium text-ui-fg-base">
              {formatBackendMoney(backendProductPrice(product))}
            </span>
            {product.shop?.shop_name && (
              <span className="line-clamp-1 text-right text-ui-fg-muted">
                {product.shop.shop_name}
              </span>
            )}
          </div>
        </div>
      </article>
    </LocalizedClientLink>
  )
}

const FilterStrip = ({
  label,
  allLabel,
  value,
  items,
  onChange,
}: {
  label: string
  allLabel: string
  value: string
  items: Array<{ label: string; value: string; meta?: number }>
  onChange: (value: string) => void
}) => {
  const scrollerRef = useRef<HTMLDivElement | null>(null)

  const handleWheel = (event: WheelEvent<HTMLDivElement>) => {
    const scroller = scrollerRef.current
    if (!scroller) return
    if (Math.abs(event.deltaY) <= Math.abs(event.deltaX)) return

    event.preventDefault()
    scroller.scrollLeft += event.deltaY
  }

  return (
    <div>
      <p className="mb-2 txt-xsmall-plus uppercase text-ui-fg-muted">{label}</p>
      <div
        ref={scrollerRef}
        className="no-scrollbar flex gap-2 overflow-x-auto pb-1"
        onWheel={handleWheel}
      >
        <button
          type="button"
          onClick={() => onChange("all")}
          className={filterButtonClass(value === "all")}
        >
          {allLabel}
        </button>
        {items.map((item) => (
          <button
            key={item.value}
            type="button"
            onClick={() => onChange(item.value)}
            className={filterButtonClass(value === item.value)}
          >
            <span>{item.label}</span>
            {item.meta !== undefined && (
              <span className="text-ui-fg-muted">{item.meta}</span>
            )}
          </button>
        ))}
      </div>
    </div>
  )
}

const filterButtonClass = (active: boolean) =>
  clx(
    "flex h-9 shrink-0 items-center gap-2 rounded-rounded border px-3 text-small-regular transition-colors",
    active
      ? "border-ui-fg-base bg-ui-fg-base text-ui-bg-base"
      : "border-ui-border-base bg-white text-ui-fg-subtle hover:bg-ui-bg-subtle hover:text-ui-fg-base"
  )

const MasonryProductFeed = ({
  products,
  currentUser,
}: {
  products: BackendProduct[]
  currentUser?: Account | null
}) => {
  const columnCount = useResponsiveColumnCount()
  const columns = useMemo(
    () => distributeIntoColumns(products, columnCount),
    [columnCount, products]
  )

  return (
    <div className="grid grid-cols-2 gap-4 small:grid-cols-4 medium:grid-cols-5">
      {columns.map((column, columnIndex) => (
        <ul key={columnIndex} className="flex min-w-0 flex-col gap-5">
          {column.map(({ product, index }) => (
            <li key={`${product.id ?? backendProductName(product)}-${index}`}>
              <HallProductCard
                product={product}
                priority={index < 8}
                currentUser={currentUser}
              />
            </li>
          ))}
        </ul>
      ))}
    </div>
  )
}

const HallProductCard = ({
  product,
  priority,
  currentUser,
  eventSource = "hall_feed",
}: {
  product: BackendProduct
  priority: boolean
  currentUser?: Account | null
  eventSource?: string
}) => {
  const imageUrl = getProductImageUrl(product)
  const name = backendProductName(product)
  const category = backendCategoryName(product.category)
  const [imageRatio, setImageRatio] = useState(4 / 5)

  return (
    <LocalizedClientLink
      href={productHref(product, currentUser)}
      className="group block"
      onClick={() => trackProductClick(product, eventSource)}
    >
      <article className="overflow-hidden rounded-rounded border border-ui-border-base bg-white shadow-elevation-card-rest transition-shadow duration-150 group-hover:shadow-elevation-card-hover">
        <div
          className="relative w-full overflow-hidden bg-ui-bg-subtle"
          style={{ aspectRatio: imageRatio }}
        >
          {imageUrl ? (
            <img
              src={imageUrl}
              alt={name}
              className="absolute inset-0 h-full w-full bg-ui-bg-subtle object-cover"
              loading={priority ? "eager" : "lazy"}
              decoding="async"
              fetchPriority={priority ? "high" : "auto"}
              onLoad={(event) => {
                const image = event.currentTarget
                if (image.naturalWidth > 0 && image.naturalHeight > 0) {
                  setImageRatio(image.naturalWidth / image.naturalHeight)
                }
              }}
            />
          ) : (
            <div className="absolute inset-0 bg-ui-bg-subtle" />
          )}
        </div>
        <div className="p-3">
          <div className="flex items-start justify-between gap-3">
            <h3 className="line-clamp-2 text-small-regular text-ui-fg-base">
              {name}
            </h3>
            <span className="shrink-0 text-small-regular text-ui-fg-muted">
              {formatBackendMoney(backendProductPrice(product))}
            </span>
          </div>
          <div className="mt-2 flex items-center justify-between gap-3 text-small-regular text-ui-fg-muted">
            <span className="line-clamp-1">{category}</span>
            {product.shop?.shop_name && (
              <span className="line-clamp-1 text-right">
                {product.shop.shop_name}
              </span>
            )}
          </div>
        </div>
      </article>
    </LocalizedClientLink>
  )
}

function trackProductClick(product: BackendProduct, source: string) {
  const payload = {
    event_type: source === "liked_products" ? "recommendation_click" : "product_view",
    product_id: product.id,
    product_name: backendProductName(product),
    product_slug: product.slug,
    shop_id: product.shop?.shop_id,
    shop_name: product.shop?.shop_name,
    category_name: backendCategoryName(product.category),
    price: backendProductPrice(product),
    source_page: "/hall",
    metadata: { source },
  }

  if (typeof navigator !== "undefined" && "sendBeacon" in navigator) {
    const body = new Blob([JSON.stringify(payload)], {
      type: "application/json",
    })
    if (navigator.sendBeacon("/api/backend/events", body)) {
      return
    }
  }

  void trackEvent(payload).catch(() => {})
}

const MasonrySkeleton = () => {
  return (
    <div className="mt-5 grid grid-cols-2 gap-4 small:grid-cols-4 medium:grid-cols-5">
      {Array.from({ length: 5 }).map((_, columnIndex) => (
        <ul key={columnIndex} className="flex min-w-0 flex-col gap-5">
          {Array.from({ length: columnIndex < 2 ? 2 : 1 }).map((__, index) => {
            const itemIndex = columnIndex * 2 + index

            return (
              <li key={itemIndex}>
                <div className="overflow-hidden rounded-rounded border border-ui-border-base bg-white">
                  <div
                    className={clx(
                      "w-full animate-pulse bg-ui-bg-subtle",
                      itemIndex % 3 === 0
                        ? "aspect-[3/4]"
                        : itemIndex % 3 === 1
                        ? "aspect-square"
                        : "aspect-[4/5]"
                    )}
                  />
                  <div className="p-3">
                    <div className="h-4 w-3/4 animate-pulse rounded bg-ui-bg-subtle" />
                    <div className="mt-2 h-3 w-1/2 animate-pulse rounded bg-ui-bg-subtle" />
                  </div>
                </div>
              </li>
            )
          })}
        </ul>
      ))}
    </div>
  )
}

const EmptyFeed = ({ onClear }: { onClear: () => void }) => {
  return (
    <div className="rounded-rounded border border-ui-border-base bg-ui-bg-subtle p-6">
      <h3 className="text-base-semi">No products found</h3>
      <p className="mt-2 text-small-regular text-ui-fg-subtle">
        Try another search term or remove the current filters.
      </p>
      <Button variant="secondary" className="mt-4 h-10" onClick={onClear}>
        Clear filters
      </Button>
    </div>
  )
}

function getProductImageUrl(product: BackendProduct): string | null {
  return (
    product.thumbnail ||
    product.images?.[0]?.url ||
    product.images?.[0]?.image_url ||
    null
  )
}

function feedSummary(
  shopName?: string,
  categoryName?: string
) {
  const filters = [shopName, categoryName].filter(Boolean)
  if (filters.length) {
    return `Filtered by ${filters.join(" / ")}. Keep scrolling to load more.`
  }

  return "Keep scrolling to load more products."
}

export default HallTemplate
