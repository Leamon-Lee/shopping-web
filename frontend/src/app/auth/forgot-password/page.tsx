"use client"

import { Button } from "@medusajs/ui"
import Input from "@modules/common/components/input"
import { useState } from "react"

export default function ForgotPasswordPage() {
  const [sent, setSent] = useState(false)

  return (
    <div className="min-h-screen bg-ui-bg-base">
      <div className="content-container flex min-h-screen items-center justify-center py-16">
        <div className="flex w-full max-w-sm flex-col">
          <div className="mb-8">
            <p className="txt-xsmall-plus uppercase text-ui-fg-muted">Shopping Web</p>
            <h1 className="mt-2 text-xl-semi text-ui-fg-base">Reset your password</h1>
            <p className="mt-2 text-small-regular text-ui-fg-subtle">
              {sent
                ? "If an account with that email exists, we've sent a reset link."
                : "Enter your email and we'll send you a reset link."}
            </p>
          </div>
          {!sent ? (
            <form className="flex flex-col gap-y-4" onSubmit={(e) => { e.preventDefault(); setSent(true) }}>
              <Input label="Email" name="email" type="email" autoComplete="email" required />
              <Button type="submit" className="mt-2 h-10 w-full">Send reset link</Button>
            </form>
          ) : (
            <Button variant="secondary" className="h-10 w-full" onClick={() => setSent(false)}>
              Send another
            </Button>
          )}
          <p className="mt-6 text-small-regular text-ui-fg-muted text-center">
            <a href="/auth/login" className="text-ui-fg-base hover:underline">Back to sign in</a>
          </p>
        </div>
      </div>
    </div>
  )
}
