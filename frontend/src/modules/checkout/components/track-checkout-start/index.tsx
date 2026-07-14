"use client"

import { useEffect } from "react"
import { trackCheckoutStart } from "@lib/data/events"

export default function CheckoutTracker({ cartItemCount }: { cartItemCount?: number }) {
  useEffect(() => {
    trackCheckoutStart(cartItemCount)
  }, [cartItemCount])

  return null
}
