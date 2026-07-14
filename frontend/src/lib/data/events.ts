"use client"

/**
 * Fire-and-forget event tracking for recommendation system.
 *
 * Sends events to POST /events on the backend.
 * Every call is wrapped in try/catch — tracking failures
 * must NEVER break the user shopping flow.
 *
 * Anonymous users are tracked via an anonymous_id stored in
 * localStorage, plus a session_id in sessionStorage.
 *
 * No passwords, tokens, or card numbers are ever sent.
 */

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8001"

// ── Identity helpers ──────────────────────────────────────────

let _sessionId: string | null = null
function getSessionId(): string {
  if (!_sessionId) {
    if (typeof window !== "undefined") {
      _sessionId = sessionStorage.getItem("rec_session_id")
      if (!_sessionId) {
        _sessionId = crypto.randomUUID()
        sessionStorage.setItem("rec_session_id", _sessionId)
      }
    } else {
      _sessionId = "ssr"
    }
  }
  return _sessionId
}

let _anonymousId: string | null = null
function getAnonymousId(): string {
  if (!_anonymousId) {
    if (typeof window !== "undefined") {
      _anonymousId = localStorage.getItem("rec_anonymous_id")
      if (!_anonymousId) {
        _anonymousId = crypto.randomUUID()
        localStorage.setItem("rec_anonymous_id", _anonymousId)
      }
    } else {
      _anonymousId = "ssr"
    }
  }
  return _anonymousId
}

function getSourcePage(): string {
  if (typeof window !== "undefined") {
    return window.location.pathname + window.location.search
  }
  return ""
}

// ── Core tracking function ────────────────────────────────────

export type EventPayload = {
  event_type: string
  product_id?: string | null
  product_name?: string | null
  product_slug?: string | null
  shop_id?: string | null
  shop_name?: string | null
  category_id?: string | null
  category_name?: string | null
  query?: string | null
  quantity?: number | null
  price?: number | null
  source_page?: string | null
  metadata?: Record<string, unknown> | null
}

export async function trackEvent(payload: EventPayload): Promise<void> {
  try {
    const headers: Record<string, string> = {
      "content-type": "application/json",
      "X-Session-Id": getSessionId(),
      "X-Anonymous-Id": getAnonymousId(),
    }
    // Also send cart_id for session continuity
    try {
      const cartMatch = document.cookie.match(/(?:^|;\s*)shopping_cart_id=([^;]*)/)
      if (cartMatch) headers["X-Cart-Id"] = cartMatch[1]
    } catch { /* cookie read may fail in some contexts */ }

    await fetch(`${BACKEND_URL}/events`, {
      method: "POST",
      headers,
      body: JSON.stringify({
        ...payload,
        source_page: payload.source_page || getSourcePage(),
      }),
      keepalive: true,
    })
  } catch {
    // Silently ignore — tracking must never break the UX
  }
}

// ── Named event helpers ───────────────────────────────────────

/** Product detail page opened or product card scrolled into view. */
export function trackProductView(payload: {
  product_id: string
  product_name?: string
  product_slug?: string
  shop_id?: string
  shop_name?: string
  category_id?: string
  category_name?: string
  price?: number
}) {
  trackEvent({ event_type: "product_view", ...payload })
}

/** User typed a search query. */
export function trackSearch(query: string, resultCount?: number) {
  trackEvent({
    event_type: "search",
    query,
    metadata: resultCount != null ? { result_count: resultCount } : undefined,
  })
}

/** Product added to cart (call AFTER the API succeeds). */
export function trackAddToCart(payload: {
  product_id: string
  product_name?: string
  product_slug?: string
  shop_id?: string
  shop_name?: string
  price?: number
  quantity?: number
}) {
  trackEvent({ event_type: "add_to_cart", ...payload })
}

/** Product removed from cart. */
export function trackRemoveFromCart(payload: {
  product_id: string
  product_name?: string
}) {
  trackEvent({ event_type: "remove_from_cart", ...payload })
}

/** User entered the checkout flow. */
export function trackCheckoutStart(cartItemCount?: number) {
  trackEvent({
    event_type: "checkout_start",
    metadata: cartItemCount != null ? { cart_item_count: cartItemCount } : undefined,
  })
}

/** Order created (call AFTER the order API succeeds). */
export function trackOrderCreated(orderNumber: string, itemCount?: number) {
  trackEvent({
    event_type: "order_created",
    metadata: { order_number: orderNumber, item_count: itemCount },
  })
}

/** Order payment completed. */
export function trackOrderPaid(orderNumber: string) {
  trackEvent({
    event_type: "order_paid",
    metadata: { order_number: orderNumber },
  })
}

/** Recommendation card appeared in the viewport. */
export function trackRecommendationImpression(recommendationId: string, productIds: string[]) {
  trackEvent({
    event_type: "recommendation_impression",
    metadata: { recommendation_id: recommendationId, product_ids: productIds },
  })
}

/** User clicked a recommendation card. */
export function trackRecommendationClick(recommendationId: string, productId: string) {
  trackEvent({
    event_type: "recommendation_click",
    product_id: productId,
    metadata: { recommendation_id: recommendationId },
  })
}

/** User added a recommended product to cart. */
export function trackRecommendationAddToCart(recommendationId: string, productId: string) {
  trackEvent({
    event_type: "recommendation_add_to_cart",
    product_id: productId,
    metadata: { recommendation_id: recommendationId },
  })
}
