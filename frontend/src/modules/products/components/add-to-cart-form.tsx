"use client"

import { Button } from "@medusajs/ui"
import { useRouter } from "next/navigation"
import { useState, useTransition } from "react"
import { trackEvent } from "../../../api/backend-client"

type AddToCartFormProps = {
  addAction: () => Promise<void>
  disabled?: boolean
  requiresLogin?: boolean
  loginHref?: string
  favoritePayload?: Record<string, unknown>
}

export default function AddToCartForm({
  addAction,
  disabled,
  requiresLogin,
  loginHref = "/auth/login",
  favoritePayload,
}: AddToCartFormProps) {
  const router = useRouter()
  const [isPending, startTransition] = useTransition()
  const [isSaving, setIsSaving] = useState(false)
  const [isSaved, setIsSaved] = useState(false)
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

  const handleFavorite = () => {
    if (requiresLogin) {
      router.push(loginHref)
      return
    }
    if (!favoritePayload) return

    setIsSaving(true)
    setToast(null)
    void trackEvent({
      ...favoritePayload,
      event_type: "favorite_product",
      metadata: {
        ...((favoritePayload.metadata as Record<string, unknown> | undefined) ?? {}),
        source: "product_detail",
      },
    })
      .then(() => {
        setIsSaved(true)
        setToast({ message: "Saved for recommendations.", type: "success" })
      })
      .catch(() => {
        setToast({ message: "Failed to save", type: "error" })
      })
      .finally(() => {
        setIsSaving(false)
        setTimeout(() => setToast(null), 3000)
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
      <Button
        onClick={handleFavorite}
        disabled={disabled || isSaving || isSaved}
        variant="secondary"
        className="w-full h-10 mt-2"
        isLoading={isSaving}
      >
        {requiresLogin ? "Sign in to save" : isSaved ? "Saved" : "Save"}
      </Button>
    </>
  )
}
