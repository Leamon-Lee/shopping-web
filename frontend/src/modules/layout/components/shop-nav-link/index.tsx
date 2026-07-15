"use client"

import { usePathname } from "next/navigation"

export default function ShopNavLink() {
  const pathname = usePathname()
  const isCartPage = pathname === "/cart" || pathname.startsWith("/cart/")

  if (isCartPage) return null

  return (
    <a className="hover:text-ui-fg-base" href="/shop">
      Shop
    </a>
  )
}
