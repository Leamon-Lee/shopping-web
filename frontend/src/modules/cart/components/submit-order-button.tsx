"use client"

import { Button } from "@medusajs/ui"
import { useRouter } from "next/navigation"

export default function SubmitOrderButton() {
  const router = useRouter()

  return (
    <Button
      onClick={() => router.push("/checkout")}
      className="w-full h-10"
    >
      Complete order
    </Button>
  )
}
