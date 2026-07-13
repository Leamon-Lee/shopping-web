"use client"

import { useEffect } from "react"

function hasAuthCookie(): boolean {
  if (typeof document === "undefined") return false
  return document.cookie.indexOf("shopping_token=") !== -1
}

export default function BfCacheGuard() {
  useEffect(() => {
    const handlePageShow = (event: PageTransitionEvent) => {
      if (event.persisted && !hasAuthCookie()) {
        window.location.reload()
      }
    }

    window.addEventListener("pageshow", handlePageShow)
    return () => window.removeEventListener("pageshow", handlePageShow)
  }, [])

  return null
}
