"use client"

import { useEffect, useRef, useState } from "react"
import LocalizedClientLink from "@modules/common/components/localized-client-link"
import { productHref } from "@lib/marketplace-routes"
import { trackRecommendationClick, trackRecommendationImpression } from "@lib/data/events"
import { saveCartIdCookie } from "../../../../api/backend-client"
import type { Account, BackendProduct } from "types/backend"
import {
  backendProductName,
  backendProductPrice,
  formatBackendMoney,
} from "@lib/backend-native"

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8001"

type RecItem = {
  product: BackendProduct
  reason: string
  score: number | null
}

type Props = {
  /** URL path for the recommendation endpoint, e.g. "/recommendations/home" */
  endpoint: string
  title?: string
  currentUser?: Account | null
  className?: string
  compact?: boolean
  /** Optional cart ID — passed as X-Cart-Id header so /recommendations/cart can exclude items */
  cartId?: string | null
}

/**
 * Generic recommendation section.
 *
 * Fetches from any /recommendations/* endpoint, renders a responsive
 * product grid with images, prices, and recommendation reasons.
 * Silently falls back (renders nothing) on error or empty results.
 * Tracks impressions via IntersectionObserver and clicks on tap.
 */
export default function RecommendedProducts({
  endpoint,
  title = "Recommended for you",
  currentUser,
  className = "",
  compact = false,
  cartId,
}: Props) {
  const [items, setItems] = useState<RecItem[]>([])
  const [loading, setLoading] = useState(true)
  const sectionRef = useRef<HTMLElement | null>(null)
  const impressionFired = useRef(false)

  // Fetch
  useEffect(() => {
    let cancelled = false
    setLoading(true)

    // Build headers — pass cart_id for cart-aware recommendations
    const headers: Record<string, string> = {}
    const cid = cartId || (typeof document !== "undefined"
      ? (document.cookie.match(/(?:^|;\s*)shopping_cart_id=([^;]*)/) || [])[1]
      : null)
    if (cid) headers["X-Cart-Id"] = cid

    fetch(`${BACKEND_URL}${endpoint}`, { cache: "no-store", headers })
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (cancelled || !data?.items?.length) {
          if (!cancelled) setLoading(false)
          return
        }
        setItems(data.items.map((i: any) => ({
          product: i.product as BackendProduct,
          reason: i.reason || "Recommended",
          score: i.score,
        })))
        setLoading(false)
      })
      .catch(() => {
        if (!cancelled) setLoading(false)
      })

    return () => { cancelled = true }
  }, [endpoint, cartId])

  // Impression tracking (fire once when 50% visible)
  useEffect(() => {
    if (!sectionRef.current || items.length === 0 || impressionFired.current) return

    const el = sectionRef.current
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && !impressionFired.current) {
          impressionFired.current = true
          const productIds = items.map(
            (i) => i.product.id ?? backendProductName(i.product)
          ).filter(Boolean)
          trackRecommendationImpression(endpoint, productIds)
          observer.unobserve(el)
        }
      },
      { threshold: 0.5 }
    )
    observer.observe(el)
    return () => observer.disconnect()
  }, [items, endpoint])

  // Loading skeleton
  if (loading) {
    const cols = compact ? 3 : 6
    return (
      <section className={className} ref={sectionRef}>
        <h2 className="text-xl-semi mb-4">{title}</h2>
        <div className={`grid grid-cols-2 gap-3 small:grid-cols-3 ${compact ? "" : "medium:grid-cols-6"}`}>
          {Array.from({ length: cols }).map((_, i) => (
            <div key={i} className="animate-pulse rounded-rounded border border-ui-border-base bg-ui-bg-subtle aspect-[3/4]" />
          ))}
        </div>
      </section>
    )
  }

  // Silent fallback — don't render anything on error or empty
  if (items.length === 0) return null

  const handleClick = (productId: string) => {
    trackRecommendationClick(endpoint, productId)
  }

  return (
    <section className={className} ref={sectionRef}>
      <h2 className="text-xl-semi mb-4">{title}</h2>
      <div className={`grid grid-cols-2 gap-3 small:grid-cols-3 ${compact ? "" : "medium:grid-cols-6"}`}>
        {items.slice(0, compact ? 4 : 6).map((rec) => {
          const product = rec.product
          const pid = product.id ?? backendProductName(product)
          return (
            <LocalizedClientLink
              key={pid}
              href={productHref(product, currentUser)}
              className="group block"
              onClick={() => handleClick(pid)}
            >
              <article className="overflow-hidden rounded-rounded border border-ui-border-base bg-white shadow-elevation-card-rest transition-shadow duration-150 group-hover:shadow-elevation-card-hover h-full flex flex-col">
                <div className="aspect-[3/4] w-full overflow-hidden bg-ui-bg-subtle">
                  {getProductImage(product) ? (
                    <img
                      src={getProductImage(product)!}
                      alt={backendProductName(product)}
                      className="h-full w-full object-cover"
                      loading="lazy"
                      decoding="async"
                    />
                  ) : (
                    <div className="h-full w-full bg-ui-bg-subtle" />
                  )}
                </div>
                <div className="flex flex-col flex-1 p-3">
                  <h3 className="line-clamp-2 text-small-regular text-ui-fg-base">
                    {backendProductName(product)}
                  </h3>
                  <p className="mt-1 text-small-regular text-ui-fg-muted">
                    {formatBackendMoney(backendProductPrice(product))}
                  </p>
                  <p className="mt-auto pt-2 text-xsmall-regular text-ui-fg-subtle italic">
                    {rec.reason}
                  </p>
                </div>
              </article>
            </LocalizedClientLink>
          )
        })}
      </div>
    </section>
  )
}

function getProductImage(product: BackendProduct): string | null {
  return product.thumbnail || product.images?.[0]?.url || product.images?.[0]?.image_url || null
}
