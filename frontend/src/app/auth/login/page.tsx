"use client"

import { Suspense, useId, useRef } from "react"
import { Button } from "@medusajs/ui"
import Input from "@modules/common/components/input"
import { login } from "@lib/data/customer"
import { useRouter, useSearchParams } from "next/navigation"
import { FormEvent, useState } from "react"

function LoginForm() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const redirect = searchParams.get("redirect") || "/hall"
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)
  const formRef = useRef<HTMLFormElement>(null)
  const formKey = useId()

  const resetForm = () => {
    setEmail("")
    setPassword("")
  }

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
      resetForm()
      const target = result?.redirectTo ?? redirect
      const roleLockedTarget = target === "/manager" || target === "/admin"
      router.replace(searchParams.has("redirect") && !roleLockedTarget ? redirect : target)
    }
  }

  return (
    <div className="min-h-screen bg-ui-bg-base">
      <div className="content-container flex min-h-screen items-center justify-center py-16">
        <div className="flex w-full max-w-sm flex-col">
          <div className="mb-8">
            <p className="txt-xsmall-plus uppercase text-ui-fg-muted">Shopping Web</p>
            <h1 className="mt-2 text-xl-semi text-ui-fg-base">Sign in to your account</h1>
            <p className="mt-2 text-small-regular text-ui-fg-subtle">
              Enter your email and password to continue.
            </p>
          </div>
          <form
            key={formKey}
            ref={formRef}
            className="flex flex-col gap-y-4"
            onSubmit={handleSubmit}
          >
            <input
              type="text"
              name="username"
              autoComplete="username"
              style={{ display: "none" }}
              tabIndex={-1}
              readOnly
            />
            <input
              type="password"
              name="current-password"
              autoComplete="current-password"
              style={{ display: "none" }}
              tabIndex={-1}
              readOnly
            />
            <Input
              label="Email"
              name="email"
              type="text"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="new-email"
              required
            />
            <Input
              label="Password"
              name="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="new-password"
              required
            />
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
