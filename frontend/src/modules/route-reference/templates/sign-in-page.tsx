import LocalizedClientLink from "@modules/common/components/localized-client-link"

type SignInPageProps = {
  role: "customer" | "manager" | "admin"
}

const roleCopy = {
  customer: {
    title: "Customer sign in",
    description: "Access cart, orders, wishlist, reviews, payment, and profile settings.",
    demoPath: "/customer/demo/hall",
  },
  manager: {
    title: "Manager sign in",
    description: "Manage shops, products, orders, analytics, income, and settings.",
    demoPath: "/manager/demo/dashboard",
  },
  admin: {
    title: "Admin sign in",
    description: "Review shops, products, users, categories, reports, and platform settings.",
    demoPath: "/admin/demo/dashboard",
  },
}

export default function SignInPage({ role }: SignInPageProps) {
  const copy = roleCopy[role]

  return (
    <div className="min-h-screen bg-ui-bg-base">
      <div className="content-container flex min-h-screen items-center justify-center py-16">
        <div className="grid w-full max-w-4xl grid-cols-1 gap-10 small:grid-cols-[1fr_360px]">
          <section className="flex flex-col justify-center">
            <p className="txt-xsmall-plus uppercase text-ui-fg-muted">
              Sign in
            </p>
            <h1 className="mt-3 text-2xl-semi text-ui-fg-base">
              {copy.title}
            </h1>
            <p className="mt-3 text-base-regular text-ui-fg-subtle">
              {copy.description}
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <LocalizedClientLink
                href="/sign-in/customer"
                className="rounded-md border border-ui-border-base px-4 py-2 text-small-semi hover:bg-ui-bg-subtle"
              >
                Customer
              </LocalizedClientLink>
              <LocalizedClientLink
                href="/sign-in/manager"
                className="rounded-md border border-ui-border-base px-4 py-2 text-small-semi hover:bg-ui-bg-subtle"
              >
                Manager
              </LocalizedClientLink>
              <LocalizedClientLink
                href="/sign-in/admin"
                className="rounded-md border border-ui-border-base px-4 py-2 text-small-semi hover:bg-ui-bg-subtle"
              >
                Admin
              </LocalizedClientLink>
            </div>
          </section>

          <form className="rounded-rounded border border-ui-border-base bg-white p-6">
            <label className="block text-small-regular text-ui-fg-subtle">
              Email
              <input
                name="email"
                type="email"
                defaultValue={`${role}@email.com`}
                className="mt-2 block h-10 w-full rounded-md border border-ui-border-base px-3 text-ui-fg-base"
              />
            </label>
            <label className="mt-4 block text-small-regular text-ui-fg-subtle">
              Password
              <input
                name="password"
                type="password"
                defaultValue="leamonlee04"
                className="mt-2 block h-10 w-full rounded-md border border-ui-border-base px-3 text-ui-fg-base"
              />
            </label>
            <LocalizedClientLink
              href={copy.demoPath}
              className="mt-6 inline-flex h-10 w-full items-center justify-center rounded-md bg-ui-fg-base text-small-semi text-ui-bg-base hover:bg-ui-fg-subtle"
            >
              Continue
            </LocalizedClientLink>
          </form>
        </div>
      </div>
    </div>
  )
}
