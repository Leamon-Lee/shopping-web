"use client"

import { useCallback, useEffect, useState } from "react"
import { usePathname } from "next/navigation"
import LocalizedClientLink from "@modules/common/components/localized-client-link"
import { getCart } from "../../../api/backend-client"

declare global {
  interface WindowEventMap {
    "cart-updated": CustomEvent
  }
}

export default function CartCount() {
  const [count, setCount] = useState<number | null>(null)
  const pathname = usePathname()

  const fetchCount = useCallback(() => {
    getCart()
      .then((data) => {
        setCount(data.total_quantity ?? 0)
      })
      .catch(() => {})
  }, [])

  useEffect(() => {
    fetchCount()
  }, [pathname, fetchCount])

  useEffect(() => {
    window.addEventListener("cart-updated", fetchCount)
    return () => window.removeEventListener("cart-updated", fetchCount)
  }, [fetchCount])

  return (
    <LocalizedClientLink
      className="hover:text-ui-fg-base flex gap-2"
      href="/cart"
      data-testid="nav-cart-link"
    >
      Cart{count !== null ? ` (${count})` : ""}
    </LocalizedClientLink>
  )
}
