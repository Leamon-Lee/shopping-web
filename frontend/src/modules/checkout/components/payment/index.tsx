"use client"

import { isStripeLike, paymentInfoMap } from "@lib/constants"
import { initiatePaymentSession } from "@lib/data/cart"
import { CheckCircleSolid, CreditCard } from "@medusajs/icons"
import { Button, Container, Heading, Text, clx } from "@medusajs/ui"
import PaymentContainer from "@modules/checkout/components/payment-container"
import Divider from "@modules/common/components/divider"
import { usePathname, useRouter, useSearchParams } from "next/navigation"
import { useCallback, useEffect, useState } from "react"

const Payment = ({
  cart,
  availablePaymentMethods,
}: {
  cart: any
  availablePaymentMethods: any[]
}) => {
  const activeSession = cart.payment_collection?.payment_sessions?.find(
    (paymentSession: any) => paymentSession.status === "pending"
  )

  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selectedPaymentMethod, setSelectedPaymentMethod] = useState(
    activeSession?.provider_id ?? "pp_system_default"
  )

  const searchParams = useSearchParams()
  const router = useRouter()
  const pathname = usePathname()

  const isOpen = searchParams.get("step") === "payment"

  // Auto-create demo payment session when entering payment step
  useEffect(() => {
    if (isOpen && !activeSession) {
      setIsLoading(true)
      initiatePaymentSession(cart, {
        provider_id: "pp_system_default",
      })
        .then(() => {
          setSelectedPaymentMethod("pp_system_default")
        })
        .catch((err: any) => setError(err.message))
        .finally(() => setIsLoading(false))
    }
  }, [isOpen])

  const paymentReady =
    (activeSession && cart?.shipping_methods?.length !== 0) ||
    selectedPaymentMethod === "pp_system_default"

  const createQueryString = useCallback(
    (name: string, value: string) => {
      const params = new URLSearchParams(searchParams)
      params.set(name, value)
      return params.toString()
    },
    [searchParams]
  )

  const handleEdit = () => {
    router.push(pathname + "?" + createQueryString("step", "payment"), {
      scroll: false,
    })
  }

  const handleSubmit = () => {
    router.push(
      pathname + "?" + createQueryString("step", "review"),
      { scroll: false }
    )
  }

  useEffect(() => {
    setError(null)
  }, [isOpen])

  return (
    <div className="bg-white">
      <div className="flex flex-row items-center justify-between mb-6">
        <Heading
          level="h2"
          className={clx(
            "flex flex-row text-3xl-regular gap-x-2 items-baseline",
            {
              "opacity-50 pointer-events-none select-none":
                !isOpen && !paymentReady,
            }
          )}
        >
          Payment
          {!isOpen && paymentReady && <CheckCircleSolid />}
        </Heading>
        {!isOpen && paymentReady && (
          <Text>
            <button
              onClick={handleEdit}
              className="text-ui-fg-interactive hover:text-ui-fg-interactive-hover"
              data-testid="edit-payment-button"
            >
              Edit
            </button>
          </Text>
        )}
      </div>

      <div className={isOpen ? "block" : "hidden"}>
        <div className="rounded-rounded border border-ui-border-base bg-ui-bg-subtle p-4 mb-4">
          <div className="flex items-center gap-x-3">
            <CreditCard />
            <div>
              <Text className="text-base-regular text-ui-fg-base">
                Demo Manual Payment
              </Text>
              <Text className="text-small-regular text-ui-fg-subtle">
                No real payment will be processed. You&apos;ll enter a test card
                number on the review page.
              </Text>
            </div>
          </div>
        </div>

        <Button
          size="large"
          className="mt-4"
          onClick={handleSubmit}
          isLoading={isLoading}
          data-testid="submit-payment-button"
        >
          Continue to review
        </Button>
      </div>

      <div className={isOpen ? "hidden" : "block"}>
        {cart && paymentReady && (
          <div className="flex items-start gap-x-1 w-full">
            <div className="flex flex-col w-1/3">
              <Text className="txt-medium-plus text-ui-fg-base mb-1">
                Payment method
              </Text>
              <Text
                className="txt-medium text-ui-fg-subtle"
                data-testid="payment-method-summary"
              >
                Demo Manual Payment
              </Text>
            </div>
          </div>
        )}
      </div>
      <Divider className="mt-8" />
    </div>
  )
}

export default Payment
