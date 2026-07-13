"use client"

import { useTransition } from "react"

type RemoveItemButtonProps = {
  productName: string
  removeAction: (formData: FormData) => Promise<void>
}

export default function RemoveItemButton({ productName, removeAction }: RemoveItemButtonProps) {
  const [isPending, startTransition] = useTransition()

  const handleRemove = () => {
    startTransition(async () => {
      const fd = new FormData()
      fd.set("product_name", productName)
      await removeAction(fd)
      window.dispatchEvent(new CustomEvent("cart-updated"))
    })
  }

  return (
    <button
      onClick={handleRemove}
      disabled={isPending}
      className={`text-small-regular text-ui-fg-muted hover:text-ui-fg-base ${isPending ? "opacity-50" : ""}`}
    >
      Remove
    </button>
  )
}
