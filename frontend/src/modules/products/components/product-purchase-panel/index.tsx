"use client"

import { Button, clx } from "@medusajs/ui"
import LocalizedClientLink from "@modules/common/components/localized-client-link"
import { useActionState, useEffect, useMemo, useState } from "react"
import { saveCartIdCookie } from "../../../../api/backend-client"
import { trackAddToCart } from "@lib/data/events"
import {
  backendCategoryName,
  backendProductName,
  backendProductPrice,
} from "@lib/backend-native"
import type {
  BackendProduct,
  BackendProductOption,
} from "types/backend"

export type AddToCartState = {
  status: "idle" | "success" | "error"
  message?: string
  totalQuantity?: number
  cartId?: string
}

type ChoiceGroup = {
  id: string
  title: string
  values: string[]
}

type ProductPurchasePanelProps = {
  product: BackendProduct
  fallbackSizes: string[]
  maxQuantity: number
  cartHref: string
  addAction: (
    prevState: AddToCartState,
    formData: FormData
  ) => Promise<AddToCartState>
}

const DEFAULT_VARIANT_NAMES = new Set(["default", "default variant"])

export default function ProductPurchasePanel({
  product,
  fallbackSizes,
  maxQuantity,
  cartHref,
  addAction,
}: ProductPurchasePanelProps) {
  const choiceGroups = useMemo(
    () => buildChoiceGroups(product, fallbackSizes),
    [product, fallbackSizes]
  )
  const [selected, setSelected] = useState<Record<string, string>>(() =>
    Object.fromEntries(choiceGroups.map((group) => [group.id, group.values[0]]))
  )
  const [quantity, setQuantity] = useState(1)
  const [state, formAction, isPending] = useActionState(addAction, {
    status: "idle",
  } satisfies AddToCartState)

  // Persist cart_id when cart is first created + track add_to_cart
  useEffect(() => {
    if (state.status === "success" && state.cartId) {
      saveCartIdCookie(state.cartId)
      trackAddToCart({
        product_id: product.id ?? backendProductName(product),
        product_name: backendProductName(product),
        product_slug: product.slug ?? undefined,
        shop_id: product.shop?.shop_id as string | undefined,
        shop_name: product.shop?.shop_name as string | undefined,
        price: backendProductPrice(product),
        quantity,
      })
    }
  }, [state.status, state.cartId, product, quantity])

  const boundedMaxQuantity = Math.max(0, Math.min(maxQuantity || 0, 10))
  const unavailable = boundedMaxQuantity < 1

  const decreaseQuantity = () => {
    setQuantity((current) => Math.max(1, current - 1))
  }

  const increaseQuantity = () => {
    setQuantity((current) => Math.min(boundedMaxQuantity, current + 1))
  }

  return (
    <div className="flex flex-col gap-5">
      {choiceGroups.length > 0 ? (
        choiceGroups.map((group) => (
          <div key={group.id}>
            <div className="mb-2 flex items-center justify-between gap-3">
              <p className="txt-xsmall-plus uppercase text-ui-fg-muted">
                {group.title}
              </p>
              <p className="text-small-regular text-ui-fg-subtle">
                {selected[group.id]}
              </p>
            </div>
            <div className="grid grid-cols-3 gap-2">
              {group.values.map((value) => {
                const active = selected[group.id] === value

                return (
                  <Button
                    key={value}
                    type="button"
                    variant="secondary"
                    className={clx(
                      "h-10 justify-center border",
                      active
                        ? "border-ui-fg-base bg-ui-fg-base text-ui-bg-base hover:bg-ui-fg-base"
                        : "border-ui-border-base bg-white text-ui-fg-base"
                    )}
                    onClick={() =>
                      setSelected((current) => ({
                        ...current,
                        [group.id]: value,
                      }))
                    }
                  >
                    {value}
                  </Button>
                )
              })}
            </div>
          </div>
        ))
      ) : (
        <div className="rounded-rounded border border-ui-border-base bg-ui-bg-subtle p-4">
          <p className="text-small-regular text-ui-fg-subtle">
            This product currently has one default selection.
          </p>
        </div>
      )}

      <form action={formAction} className="flex flex-col gap-4">
        <input type="hidden" name="quantity" value={quantity} />
        {Object.entries(selected).map(([key, value]) => (
          <input key={key} type="hidden" name={`option_${key}`} value={value} />
        ))}

        <div>
          <div className="mb-2 flex items-center justify-between">
            <p className="txt-xsmall-plus uppercase text-ui-fg-muted">
              Quantity
            </p>
            <p className="text-small-regular text-ui-fg-subtle">
              {boundedMaxQuantity} available
            </p>
          </div>
          <div className="grid grid-cols-[40px_1fr_40px] overflow-hidden rounded-rounded border border-ui-border-base">
            <button
              type="button"
              className="h-10 border-r border-ui-border-base text-base-semi disabled:text-ui-fg-disabled"
              onClick={decreaseQuantity}
              disabled={quantity <= 1 || unavailable || isPending}
            >
              -
            </button>
            <div className="flex h-10 items-center justify-center text-small-regular">
              {quantity}
            </div>
            <button
              type="button"
              className="h-10 border-l border-ui-border-base text-base-semi disabled:text-ui-fg-disabled"
              onClick={increaseQuantity}
              disabled={quantity >= boundedMaxQuantity || unavailable || isPending}
            >
              +
            </button>
          </div>
        </div>

        <Button
          type="submit"
          variant="primary"
          className="h-10 w-full"
          disabled={unavailable || isPending}
          data-testid="add-product-button"
        >
          {unavailable
            ? "Out of stock"
            : isPending
            ? "Adding..."
            : `Add ${quantity} to cart`}
        </Button>
      </form>

      {state.status !== "idle" && (
        <div
          className={clx(
            "rounded-rounded border p-4 text-small-regular",
            state.status === "success"
              ? "border-ui-tag-green-border bg-ui-tag-green-bg text-ui-tag-green-text"
              : "border-ui-tag-red-border bg-ui-tag-red-bg text-ui-tag-red-text"
          )}
        >
          <p>{state.message}</p>
          {state.status === "success" && (
            <div className="mt-3 flex gap-3">
              <LocalizedClientLink href={cartHref} className="underline">
                View cart
              </LocalizedClientLink>
              <span>{state.totalQuantity ?? 0} items in cart</span>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function buildChoiceGroups(product: BackendProduct, fallbackSizes: string[]) {
  const groups = product.options
    ?.map(normalizeOption)
    .filter((group): group is ChoiceGroup => Boolean(group?.values.length))

  if (groups?.length) {
    return groups
  }

  const variantNames = (product.variants ?? [])
    .map((variant) => variant.name || variant.title)
    .filter(Boolean)
    .filter((name) => !DEFAULT_VARIANT_NAMES.has(name.trim().toLowerCase()))

  if (variantNames.length > 1) {
    return [
      {
        id: "variant",
        title: "Variant",
        values: uniqueValues(variantNames),
      },
    ]
  }

  if (fallbackSizes.length > 0) {
    return [
      {
        id: "size",
        title: "Size",
        values: fallbackSizes,
      },
    ]
  }

  return []
}

function normalizeOption(option: BackendProductOption): ChoiceGroup | null {
  const id = readString(option, ["id", "title", "name"])
  const title = readString(option, ["title", "name", "id"]) || "Option"
  const values = Array.isArray(option.values)
    ? option.values
        .map((value) =>
          typeof value === "string"
            ? value
            : readString(value as Record<string, unknown>, [
                "value",
                "label",
                "title",
                "name",
              ])
        )
        .filter(Boolean)
    : []

  if (!id || values.length === 0) return null

  return {
    id,
    title,
    values: uniqueValues(values),
  }
}

function readString(source: Record<string, unknown>, keys: string[]) {
  for (const key of keys) {
    const value = source[key]
    if (typeof value === "string" && value.trim()) {
      return value.trim()
    }
  }
  return ""
}

function uniqueValues(values: string[]) {
  return Array.from(new Set(values.map((value) => value.trim()).filter(Boolean)))
}
