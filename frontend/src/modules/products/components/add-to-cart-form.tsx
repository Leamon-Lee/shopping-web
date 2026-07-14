"use client"

import { Button } from "@medusajs/ui"
import { useRouter } from "next/navigation"
import { useState, useTransition } from "react"

type AddToCartFormProps = {
  addAction: () => Promise<void>
  disabled?: boolean
  requiresLogin?: boolean
  loginHref?: string
}

export default function AddToCartForm({
  addAction,
  disabled,
  requiresLogin,
  loginHref = "/auth/login",
}: AddToCartFormProps) {
  const router = useRouter()
  const [isPending, startTransition] = useTransition()
  const [toast, setToast] = useState<{ message: string; type: "success" | "error" } | null>(null)

  const handleSubmit = () => {
    if (requiresLogin) {
      router.push(loginHref)
      return
    }

    setToast(null)
    startTransition(async () => {
      try {
        await addAction()
        setToast({ message: "Added to cart!", type: "success" })
        window.dispatchEvent(new CustomEvent("cart-updated"))
        setTimeout(() => router.push("/cart"), 600)
      } catch {
        setToast({ message: "Failed to add to cart", type: "error" })
        setTimeout(() => setToast(null), 3000)
      }
    })
  }

  return (
    <>
      {toast && (
        <div className="fixed top-20 right-4 z-[100]">
          <div
            className={`rounded-lg px-4 py-3 text-small-regular shadow-lg ${
              toast.type === "success"
                ? "bg-green-600 text-white"
                : "bg-red-600 text-white"
            }`}
          >
            {toast.message}
          </div>
        </div>
      )}
      <Button
        onClick={handleSubmit}
        disabled={disabled || isPending}
        variant="primary"
        className="w-full h-10"
        isLoading={isPending}
        data-testid="add-product-button"
      >
        {requiresLogin ? "Sign in to add to cart" : "Add to cart"}
      </Button>
    </>
  )
}
