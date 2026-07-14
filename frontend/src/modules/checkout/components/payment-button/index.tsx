// @ts-nocheck — Input component type mismatch with @medusajs/ui
"use client"

import { isManual, isStripeLike } from "@lib/constants"
import { placeOrder } from "@lib/data/cart"
import { processPayment } from "../../../../api/backend-client"
import { trackOrderCreated, trackOrderPaid } from "@lib/data/events"
import type {
  BackendCart,
} from "types/backend"
import { Button, Input } from "@medusajs/ui"
import { useElements, useStripe } from "@stripe/react-stripe-js"
import React, { useState } from "react"
import ErrorMessage from "../error-message"
import { useParams, useRouter } from "next/navigation"

type PaymentButtonProps = {
  cart: BackendCart
  "data-testid": string
}

const PaymentButton: React.FC<PaymentButtonProps> = ({
  cart,
  "data-testid": dataTestId,
}) => {
  const notReady =
    !cart ||
    !cart.shipping_address ||
    !cart.billing_address ||
    !cart.email ||
    (cart.shipping_methods?.length ?? 0) < 1

  const paymentSession = cart.payment_collection?.payment_sessions?.[0]

  switch (true) {
    case isStripeLike(paymentSession?.provider_id):
      return (
        <StripePaymentButton
          notReady={notReady}
          cart={cart}
          data-testid={dataTestId}
        />
      )
    case isManual(paymentSession?.provider_id):
      return (
        <ManualTestPaymentButton
          notReady={notReady}
          cart={cart}
          data-testid={dataTestId}
        />
      )
    default:
      return <Button disabled>Select a payment method</Button>
  }
}

const StripePaymentButton = ({
  cart,
  notReady,
  "data-testid": dataTestId,
}: {
  cart: BackendCart
  notReady: boolean
  "data-testid"?: string
}) => {
  const [submitting, setSubmitting] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  const onPaymentCompleted = async () => {
    await placeOrder()
      .catch((err) => {
        setErrorMessage(err.message)
      })
      .finally(() => {
        setSubmitting(false)
      })
  }

  const stripe = useStripe()
  const elements = useElements()
  const card = elements?.getElement("card")

  const session = cart.payment_collection?.payment_sessions?.find(
    (s: any) => s.status === "pending"
  )

  const disabled = !stripe || !elements ? true : false

  const handlePayment = async () => {
    setSubmitting(true)

    if (!stripe || !elements || !card || !cart) {
      setSubmitting(false)
      return
    }

    await stripe
      .confirmCardPayment(session?.data.client_secret as string, {
        payment_method: {
          card: card,
          billing_details: {
            name:
              (cart.billing_address?.first_name as string || "") +
              " " +
              (cart.billing_address?.last_name as string || ""),
            address: {
              city: (cart.billing_address?.city as string) ?? undefined,
              country: (cart.billing_address?.country_code as string) ?? undefined,
              line1: (cart.billing_address?.address_1 as string) ?? undefined,
              line2: (cart.billing_address?.address_2 as string) ?? undefined,
              postal_code: (cart.billing_address?.postal_code as string) ?? undefined,
              state: (cart.billing_address?.province as string) ?? undefined,
            },
            email: cart.email as string,
            phone: (cart.billing_address?.phone as string) ?? undefined,
          },
        },
      })
      .then(({ error, paymentIntent }) => {
        if (error) {
          const pi = error.payment_intent
          if (
            (pi && pi.status === "requires_capture") ||
            (pi && pi.status === "succeeded")
          ) {
            onPaymentCompleted()
          }
          setErrorMessage(error.message || null)
          return
        }
        if (
          (paymentIntent && paymentIntent.status === "requires_capture") ||
          paymentIntent.status === "succeeded"
        ) {
          return onPaymentCompleted()
        }
        return
      })
  }

  return (
    <>
      <Button
        disabled={disabled || notReady}
        onClick={handlePayment}
        size="large"
        isLoading={submitting}
        data-testid={dataTestId}
      >
        Place order
      </Button>
      <ErrorMessage
        error={errorMessage}
        data-testid="stripe-payment-error-message"
      />
    </>
  )
}

const ManualTestPaymentButton = ({
  notReady,
  cart,
  "data-testid": dataTestId,
}: {
  notReady: boolean
  cart: BackendCart
  "data-testid"?: string
}) => {
  const [submitting, setSubmitting] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [cardNumber, setCardNumber] = useState("4242424242424242")
  const router = useRouter()
  const params = useParams()
  const countryCode = (params?.countryCode as string) || "cn"

  const handlePayment = async () => {
    setSubmitting(true)
    setErrorMessage(null)

    try {
      // Step 1: Create the order
      const result = await placeOrder()
      const order = result.order

      if (!order?.order_number) {
        setErrorMessage("Order creation failed — no order number returned.")
        setSubmitting(false)
        return
      }

      // Track order created
      const itemCount = order.items?.length ?? cart.items?.length ?? 0
      trackOrderCreated(order.order_number, itemCount)

      // Step 2: Process demo payment
      const subtotal = (cart.subtotal || 0) > 0 ? cart.subtotal : 1.0
      const accessToken = order.access_token || ""
      try {
        await processPayment({
          order_id: order.order_number,
          card_number: cardNumber.replace(/\s/g, ""),
          amount: subtotal,
          currency: cart.currency_code || "CNY",
          access_token: accessToken,
        })
        // Payment succeeded
        trackOrderPaid(order.order_number)
        const tokenParam = accessToken ? `?token=${encodeURIComponent(accessToken)}` : ""
        router.push(`/${countryCode}/order/${order.order_number}/confirmed${tokenParam}`)
      } catch (payErr: any) {
        setErrorMessage(
          `Order ${order.order_number} created but payment failed: ${payErr.message}`
        )
      }
    } catch (err: any) {
      setErrorMessage(err.message || "Order creation failed.")
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="rounded-rounded border border-ui-border-base bg-ui-bg-subtle p-4">
        <p className="text-small-regular text-ui-fg-subtle mb-2">
          Demo Payment — enter a test card number:
        </p>
        <div className="flex gap-2 mb-2">
          <button
            type="button"
            className="text-small-regular text-ui-fg-interactive hover:underline"
            onClick={() => setCardNumber("4242424242424242")}
          >
            4242...4242 (success)
          </button>
          <span className="text-ui-fg-muted">|</span>
          <button
            type="button"
            className="text-small-regular text-ui-fg-interactive hover:underline"
            onClick={() => setCardNumber("4000000000000002")}
          >
            4000...0002 (failure)
          </button>
        </div>
        <Input
          name="demo-card-number"
          label="Card number"
          value={cardNumber}
          onChange={(e) => setCardNumber(e.target.value)}
          data-testid="demo-card-input"
        />
      </div>

      <Button
        disabled={notReady || !cardNumber}
        isLoading={submitting}
        onClick={handlePayment}
        size="large"
        data-testid={dataTestId}
      >
        Place order (Demo Payment)
      </Button>
      <ErrorMessage
        error={errorMessage}
        data-testid="manual-payment-error-message"
      />
    </div>
  )
}

export default PaymentButton
