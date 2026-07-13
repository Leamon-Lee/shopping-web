import LocalizedClientLink from "@modules/common/components/localized-client-link"
import SideMenu from "@modules/layout/components/side-menu"
import { retrieveCustomer } from "@lib/data/customer"

export default async function Nav() {
  let customer = null
  try {
    customer = await retrieveCustomer()
  } catch {
    // Backend unreachable — treat as not logged in
  }

  const role = customer?.role ?? "customer"
  const customerHref = customer
    ? role === "manager" ? "/manager"
    : role === "admin" ? "/admin"
    : `/customer/${encodeURIComponent(customer.user_name)}`
    : "/auth/login"
  const customerLabel = customer
    ? role === "manager" ? "Manager"
    : role === "admin" ? "Admin"
    : "Customer"
    : "Sign in"

  const accountHref = customer
    ? role === "manager" ? "/manager"
    : role === "admin" ? "/admin"
    : `/customer/${encodeURIComponent(customer.user_name)}`
    : "/auth/login"

  return (
    <div className="sticky top-0 inset-x-0 z-50 group">
      <header className="relative h-16 mx-auto border-b duration-200 bg-gray-200 border-ui-border-base">
        <nav className="content-container txt-xsmall-plus text-ui-fg-subtle flex items-center justify-between w-full h-full text-small-regular">
          <div className="flex-1 basis-0 h-full flex items-center">
            <div className="h-full">
              <SideMenu regions={null} locales={null} currentLocale={null} />
            </div>
          </div>

          <div className="flex items-center h-full">
            <LocalizedClientLink
              href="/"
              className="txt-compact-xlarge-plus hover:text-ui-fg-base uppercase"
              data-testid="nav-store-link"
            >
              Shopping Web
            </LocalizedClientLink>
          </div>

          <div className="flex items-center gap-x-6 h-full flex-1 basis-0 justify-end">
            <div className="hidden small:flex items-center gap-x-6 h-full">
              <a className="hover:text-ui-fg-base" href="/hall">
                Hall
              </a>
              <a className="hover:text-ui-fg-base" href="/shop">
                Shop
              </a>
              <LocalizedClientLink
                className="hover:text-ui-fg-base"
                href={customerHref}
              >
                {customerLabel}
              </LocalizedClientLink>
              <a className="hover:text-ui-fg-base" href="/sign-in/manager">
                Manager
              </a>
              <a className="hover:text-ui-fg-base" href="/sign-in/admin">
                Admin
              </a>
              <LocalizedClientLink
                className="hover:text-ui-fg-base"
                href={accountHref}
                data-testid="nav-account-link"
              >
                Account
              </LocalizedClientLink>
            </div>
            {role !== "manager" && role !== "admin" && (
              <LocalizedClientLink
                className="hover:text-ui-fg-base flex gap-2"
                href="/cart"
                data-testid="nav-cart-link"
              >
                Cart
              </LocalizedClientLink>
            )}
          </div>
        </nav>
      </header>
    </div>
  )
}
