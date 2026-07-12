"use client"

import { Button, clx } from "@medusajs/ui"
import { useMemo, useState } from "react"
import type {
  BackendProduct,
  BackendProductOption,
  BackendProductVariant,
} from "types/backend"

type ChoiceGroup = {
  id: string
  title: string
  values: string[]
}

type ProductChoicePanelProps = {
  product: BackendProduct
  fallbackSizes: string[]
}

const DEFAULT_VARIANT_NAMES = new Set(["default", "default variant"])

export default function ProductChoicePanel({
  product,
  fallbackSizes,
}: ProductChoicePanelProps) {
  const choiceGroups = useMemo(
    () => buildChoiceGroups(product, fallbackSizes),
    [product, fallbackSizes]
  )
  const [selected, setSelected] = useState<Record<string, string>>(() =>
    Object.fromEntries(choiceGroups.map((group) => [group.id, group.values[0]]))
  )

  if (choiceGroups.length === 0) {
    return (
      <div className="rounded-rounded border border-ui-border-base bg-ui-bg-subtle p-4">
        <p className="text-small-regular text-ui-fg-subtle">
          This product currently has one default selection.
        </p>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-5">
      {choiceGroups.map((group) => (
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
      ))}
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
