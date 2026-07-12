"use client"

import { Button } from "@medusajs/ui"
import Input from "@modules/common/components/input"
import { signup } from "@lib/data/customer"
import { useRouter } from "next/navigation"
import { FormEvent, useState } from "react"

export default function RegisterPage() {
  const router = useRouter()
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setLoading(true)
    setError("")

    const formData = new FormData(event.currentTarget)
    const result = await signup(null, formData)

    if (result?.error) {
      setError(result.error)
      setLoading(false)
    } else {
      router.push(result?.redirectTo ?? "/hall")
      router.refresh()
    }
  }

  return (
    <div className="min-h-screen bg-ui-bg-base">
      <div className="content-container flex min-h-screen items-center justify-center py-16">
        <div className="flex w-full max-w-sm flex-col">
          <div className="mb-8">
            <p className="txt-xsmall-plus uppercase text-ui-fg-muted">Shopping Web</p>
            <h1 className="mt-2 text-xl-semi text-ui-fg-base">Create an account</h1>
            <p className="mt-2 text-small-regular text-ui-fg-subtle">
              Fill in your details to start shopping.
            </p>
          </div>
          <form className="flex flex-col gap-y-4" onSubmit={handleSubmit}>
            <div className="grid grid-cols-2 gap-4">
              <Input label="First name" name="first_name" type="text" autoComplete="given-name" required />
              <Input label="Last name" name="last_name" type="text" autoComplete="family-name" required />
            </div>
            <Input label="Email" name="email" type="email" autoComplete="email" required />
            <Input label="Password" name="password" type="password" autoComplete="new-password" required minLength={8} />
            <Input label="Phone" name="phone" type="tel" autoComplete="tel" />
            <Button type="submit" className="mt-2 h-10 w-full" disabled={loading}>
              {loading ? "Creating account..." : "Create account"}
            </Button>
            {error && <p className="text-small-regular text-rose-500">{error}</p>}
          </form>
          <p className="mt-6 text-small-regular text-ui-fg-muted text-center">
            Already have an account?{" "}
            <a href="/auth/login" className="text-ui-fg-base hover:underline">Sign in</a>
          </p>
        </div>
      </div>
    </div>
  )
}
