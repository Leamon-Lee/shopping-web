"use client"

import { addToCart } from "@lib/data/cart"
import { trackEvent } from "../../../../api/backend-client"
import { useIntersection } from "@lib/hooks/use-in-view"
import type {
  BackendAddress,
  BackendCart,
  BackendCartLineItem,
  BackendCollection,
  BackendCustomer,
  BackendOrder,
  BackendOrderLineItem,
  BackendPaymentSession,
  BackendPrice,
  BackendProduct,
  BackendProductCategory,
  BackendProductImage,
  BackendProductListParams,
  BackendProductOption,
  BackendProductVariant,
  BackendPromotion,
  BackendRecord,
  BackendRegion,
  BackendShippingOption,
} from "types/backend"
import { Button } from "@medusajs/ui"
import Divider from "@modules/common/components/divider"
import OptionSelect from "@modules/products/components/product-actions/option-select"
import { isEqual } from "lodash"
import { useParams, usePathname, useSearchParams } from "next/navigation"
import { useEffect, useMemo, useRef, useState } from "react"
import ProductPrice from "../product-price"
import MobileActions from "./mobile-actions"
import { useRouter } from "next/navigation"

type ProductActionsProps = {
  product: BackendProduct
  region: BackendRegion
  disabled?: boolean
}

const optionsAsKeymap = (
  variantOptions: BackendProductVariant["options"]
) => {
  return variantOptions?.reduce((acc: Record<string, string>, varopt: any) => {
    acc[varopt.option_id] = varopt.value
    return acc
  }, {})
}

export default function ProductActions({
  product,
  disabled,
}: ProductActionsProps) {
  const router = useRouter()
  const pathname = usePathname()
  const searchParams = useSearchParams()

  const [options, setOptions] = useState<Record<string, string | undefined>>({})
  const [isAdding, setIsAdding] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [isSaved, setIsSaved] = useState(false)
  const [toast, setToast] = useState<{ message: string; type: "success" | "error" } | null>(null)
  const countryCode = useParams().countryCode as string

  // If there is only 1 variant, preselect the options
  useEffect(() => {
    if (product.variants?.length === 1) {
      const variantOptions = optionsAsKeymap(product.variants[0].options)
      setOptions(variantOptions ?? {})
    }
  }, [product.variants])

  const selectedVariant = useMemo(() => {
    if (!product.variants || product.variants.length === 0) {
      return
    }

    return product.variants.find((v) => {
      const variantOptions = optionsAsKeymap(v.options)
      return isEqual(variantOptions, options)
    })
  }, [product.variants, options])

  // update the options when a variant is selected
  const setOptionValue = (optionId: string, value: string) => {
    setOptions((prev) => ({
      ...prev,
      [optionId]: value,
    }))
  }

  //check if the selected options produce a valid variant
  const isValidVariant = useMemo(() => {
    return product.variants?.some((v) => {
      const variantOptions = optionsAsKeymap(v.options)
      return isEqual(variantOptions, options)
    })
  }, [product.variants, options])

  useEffect(() => {
    const params = new URLSearchParams(searchParams.toString())
    const value = isValidVariant ? selectedVariant?.id : null

    if (params.get("v_id") === value) {
      return
    }

    if (value) {
      params.set("v_id", value)
    } else {
      params.delete("v_id")
    }

    router.replace(pathname + "?" + params.toString())
  }, [selectedVariant, isValidVariant])

  // check if the selected variant is in stock
  const inStock = useMemo(() => {
    // If we don't manage inventory, we can always add to cart
    if (selectedVariant && !selectedVariant.manage_inventory) {
      return true
    }

    // If we allow back orders on the variant, we can add to cart
    if (selectedVariant?.allow_backorder) {
      return true
    }

    // If there is inventory available, we can add to cart
    if (
      selectedVariant?.manage_inventory &&
      (selectedVariant?.inventory_quantity || 0) > 0
    ) {
      return true
    }

    // Otherwise, we can't add to cart
    return false
  }, [selectedVariant])

  const actionsRef = useRef<HTMLDivElement>(null)

  const inView = useIntersection(actionsRef, "0px")

  // add the selected variant to the cart
  const handleAddToCart = async () => {
    if (!selectedVariant?.id && !product.variants?.length) return null

    setIsAdding(true)
    setToast(null)

    try {
      await addToCart({
        variantId: selectedVariant?.id || product.variants?.[0]?.id,
        productName: !selectedVariant?.id ? (product.title ?? product.name) : undefined,
        quantity: 1,
        countryCode,
      })
      window.dispatchEvent(new CustomEvent("cart-updated"))
      setToast({ message: "Added to cart!", type: "success" })
    } catch {
      setToast({ message: "Failed to add to cart. Please try again.", type: "error" })
    } finally {
      setIsAdding(false)
      setTimeout(() => setToast(null), 3000)
    }
  }

  const handleFavorite = async () => {
    if (!product.id) return

    setIsSaving(true)
    setToast(null)

    try {
      await trackEvent({
        event_type: "favorite_product",
        product_id: product.id,
        product_name: product.title ?? product.name,
        product_slug: product.slug ?? product.handle,
        shop_id: product.shop?.shop_id,
        shop_name: product.shop?.shop_name,
        category_name: product.category?.name,
        price: product.price,
        source_page: pathname,
        metadata: { source: "product_detail" },
      })
      setIsSaved(true)
      setToast({ message: "Saved for recommendations.", type: "success" })
    } catch {
      setToast({ message: "Failed to save. Please try again.", type: "error" })
    } finally {
      setIsSaving(false)
      setTimeout(() => setToast(null), 3000)
    }
  }

  return (
    <>
      {toast && (
        <div className="fixed top-20 right-4 z-[100] animate-in fade-in slide-in-from-top-2">
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
      <div className="flex flex-col gap-y-2" ref={actionsRef}>
        <div>
          {(product.variants?.length ?? 0) > 1 && (
            <div className="flex flex-col gap-y-4">
              {(product.options || []).map((option) => {
                return (
                  <div key={option.id}>
                    <OptionSelect
                      option={option}
                      current={options[option.id]}
                      updateOption={setOptionValue}
                      title={option.title ?? ""}
                      data-testid="product-options"
                      disabled={!!disabled || isAdding}
                    />
                  </div>
                )
              })}
              <Divider />
            </div>
          )}
        </div>

        <ProductPrice product={product} variant={selectedVariant} />

        <Button
          onClick={handleAddToCart}
          disabled={
            !inStock ||
            !selectedVariant ||
            !!disabled ||
            isAdding ||
            !isValidVariant
          }
          variant="primary"
          className="w-full h-10"
          isLoading={isAdding}
          data-testid="add-product-button"
        >
          {!selectedVariant && !options
            ? "Select variant"
            : !inStock || !isValidVariant
            ? "Out of stock"
            : "Add to cart"}
        </Button>
        <Button
          onClick={handleFavorite}
          disabled={!!disabled || isSaving || isSaved}
          variant="secondary"
          className="w-full h-10"
          isLoading={isSaving}
        >
          {isSaved ? "Saved" : "Save"}
        </Button>
        <MobileActions
          product={product}
          variant={selectedVariant}
          options={options}
          updateOptions={setOptionValue}
          inStock={inStock}
          handleAddToCart={handleAddToCart}
          isAdding={isAdding}
          show={!inView}
          optionsDisabled={!!disabled || isAdding}
        />
      </div>
    </>
  )
}
