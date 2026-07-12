"use client"

import { Button, clx } from "@medusajs/ui"
import { useMemo, useState } from "react"

type ProductImage = {
  url: string | null
  image_url: string
  rank: number
}

type ProductImageCarouselProps = {
  images: ProductImage[]
  fallbackAlt: string
}

export default function ProductImageCarousel({
  images,
  fallbackAlt,
}: ProductImageCarouselProps) {
  const orderedImages = useMemo(
    () => [...images].sort((a, b) => a.rank - b.rank),
    [images]
  )
  const [activeIndex, setActiveIndex] = useState(0)
  const activeImage = orderedImages[activeIndex]
  const hasMultipleImages = orderedImages.length > 1

  if (orderedImages.length === 0) {
    return <div className="h-80 w-full rounded-rounded bg-ui-bg-subtle" />
  }

  const showPrevious = () => {
    setActiveIndex((current) =>
      current === 0 ? orderedImages.length - 1 : current - 1
    )
  }

  const showNext = () => {
    setActiveIndex((current) =>
      current === orderedImages.length - 1 ? 0 : current + 1
    )
  }

  const activeSrc = activeImage.url || activeImage.image_url

  return (
    <div className="w-full">
      <div className="relative w-full overflow-hidden rounded-rounded bg-ui-bg-subtle">
        <img
          key={activeSrc}
          src={activeSrc}
          alt={`${fallbackAlt} image ${activeIndex + 1}`}
          className="block w-full max-w-full object-contain"
          loading="eager"
          decoding="async"
        />

        {hasMultipleImages && (
          <>
            <Button
              type="button"
              variant="secondary"
              className="absolute left-3 top-1/2 h-10 w-10 -translate-y-1/2 justify-center rounded-full bg-white/90 p-0 shadow-elevation-card-rest"
              onClick={showPrevious}
              aria-label="Previous product image"
            >
              <span aria-hidden="true" className="text-base-semi">
                {"<"}
              </span>
            </Button>
            <Button
              type="button"
              variant="secondary"
              className="absolute right-3 top-1/2 h-10 w-10 -translate-y-1/2 justify-center rounded-full bg-white/90 p-0 shadow-elevation-card-rest"
              onClick={showNext}
              aria-label="Next product image"
            >
              <span aria-hidden="true" className="text-base-semi">
                {">"}
              </span>
            </Button>
            <div className="absolute bottom-3 right-3 rounded-rounded bg-white/90 px-2 py-1 text-small-regular text-ui-fg-subtle">
              {activeIndex + 1} / {orderedImages.length}
            </div>
          </>
        )}
      </div>

      {hasMultipleImages && (
        <div className="mt-3 flex gap-2 overflow-x-auto pb-1">
          {orderedImages.map((image, index) => {
            const src = image.url || image.image_url
            const active = index === activeIndex

            return (
              <button
                key={`${src}-${index}`}
                type="button"
                className={clx(
                  "h-16 w-16 shrink-0 overflow-hidden rounded-rounded border bg-ui-bg-subtle",
                  active
                    ? "border-ui-fg-base"
                    : "border-ui-border-base hover:border-ui-fg-muted"
                )}
                onClick={() => setActiveIndex(index)}
                aria-label={`Show product image ${index + 1}`}
              >
                <img
                  src={src}
                  alt=""
                  className="h-full w-full object-cover"
                  loading="lazy"
                  decoding="async"
                />
              </button>
            )
          })}
        </div>
      )}
    </div>
  )
}
