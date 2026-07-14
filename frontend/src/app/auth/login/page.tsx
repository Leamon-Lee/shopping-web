"use client"

import { Suspense } from "react"
import { Button } from "@medusajs/ui"
import Input from "@modules/common/components/input"
import { login } from "@lib/data/customer"
import { useRouter, useSearchParams } from "next/navigation"
import { FormEvent, useState } from "react"

function LoginForm() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const redirect = searchParams.get("redirect") || "/hall"
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setLoading(true)
    setError("")

    const formData = new FormData(event.currentTarget)
    const result = await login(null, formData)

    if (result?.error) {
      setError(result.error)
      setLoading(false)
    } else {
      router.push(searchParams.has("redirect") ? redirect : result?.redirectTo ?? redirect)
      router.refresh()
    }
  }

  return (
    <div className="min-h-screen bg-ui-bg-base">
      <div className="content-container flex min-h-screen items-center justify-center py-16">
        <div className="flex w-full max-w-sm flex-col">
          <div className="mb-8">
            <p className="txt-xsmall-plus uppercase text-ui-fg-muted">Account</p>
            <h1 className="mt-2 text-xl-semi text-ui-fg-base">Sign in to your account</h1>
            <p className="mt-2 text-small-regular text-ui-fg-subtle">
              Enter your email and password to continue.
            </p>
          </div>
          <form className="flex flex-col gap-y-4" onSubmit={handleSubmit}>
            <Input label="Email" name="email" type="email" autoComplete="email" required />
            <Input label="Password" name="password" type="password" autoComplete="current-password" required />
            <Button type="submit" className="mt-2 h-10 w-full" disabled={loading}>
              {loading ? "Signing in..." : "Sign in"}
            </Button>
            {error && <p className="text-small-regular text-rose-500">{error}</p>}
          </form>
          <p className="mt-6 text-small-regular text-ui-fg-muted text-center">
            Don&apos;t have an account?{" "}
            <a href="/auth/register" className="text-ui-fg-base hover:underline">Create one</a>
          </p>
          <p className="mt-2 text-small-regular text-ui-fg-muted text-center">
            <a href="/auth/forgot-password" className="text-ui-fg-subtle hover:text-ui-fg-base">Forgot password?</a>
          </p>
        </div>
      </div>
    </div>
  )
}

export default function LoginPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-ui-bg-base flex items-center justify-center">
        <p className="text-small-regular text-ui-fg-subtle">Loading...</p>
      </div>
    }>
      <LoginForm />
    </Suspense>
  )
}
