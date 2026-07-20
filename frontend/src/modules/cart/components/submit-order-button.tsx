"use client"

import { Button } from "@medusajs/ui"
import { useRouter } from "next/navigation"

const DEFAULT_REGION = process.env.NEXT_PUBLIC_DEFAULT_REGION || "cn"

export default function SubmitOrderButton() {
  const router = useRouter()

  return (
    <Button
      onClick={() => router.push(`/${DEFAULT_REGION}/checkout`)}
      className="w-full h-10"
    >
      Complete order
    </Button>
  )
}
