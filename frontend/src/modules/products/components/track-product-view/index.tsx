"use client"

import { useEffect } from "react"
import { trackProductView } from "@lib/data/events"

/** Fire-and-forget product view tracking. Renders nothing.
 *
 *  Callers should pass as much product context as available
 *  so the event is useful for downstream recommendation models.
 */
export default function ProductViewTracker({
  productId,
  productName,
  productSlug,
  shopId,
  shopName,
  categoryId,
  categoryName,
  price,
}: {
  productId: string
  productName?: string
  productSlug?: string
  shopId?: string
  shopName?: string
  categoryId?: string
  categoryName?: string
  price?: number
}) {
  useEffect(() => {
    if (productId) {
      trackProductView({
        product_id: productId,
        product_name: productName,
        product_slug: productSlug,
        shop_id: shopId,
        shop_name: shopName,
        category_id: categoryId,
        category_name: categoryName,
        price,
      })
    }
  }, [productId, productName, productSlug, shopId, shopName, categoryId, categoryName, price])

  return null
}
