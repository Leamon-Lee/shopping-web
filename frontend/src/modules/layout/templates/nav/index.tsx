import LocalizedClientLink from "@modules/common/components/localized-client-link"
import SideMenu from "@modules/layout/components/side-menu"
import { getServerCartHref } from "@lib/data/cart-url"
import { retrieveCart } from "@lib/data/cart"
import { getCartForUsername } from "api/backend"

export default async function Nav({ cartOwner }: { cartOwner?: string }) {
  const cartHref = await getServerCartHref(cartOwner)
  const cart =
    cartOwner && cartOwner !== "cart" && cartOwner !== "guest"
      ? await getCartForUsername(cartOwner).catch(() => null)
      : await retrieveCart().catch(() => null)
  const totalQuantity = cart?.total_quantity ?? 0

  return (
    <div className="sticky top-0 inset-x-0 z-50 group">
      <header className="relative h-16 mx-auto border-b duration-200 bg-white border-ui-border-base">
        <nav className="content-container txt-xsmall-plus text-ui-fg-subtle flex items-center justify-between w-full h-full text-small-regular">
          <div className="flex-1 basis-0 h-full flex items-center">
            <div className="h-full">
              <SideMenu regions={null} locales={null} currentLocale={null} />
            </div>
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
                href="/account"
                data-testid="nav-account-link"
              >
                Account
              </LocalizedClientLink>
            </div>
            <LocalizedClientLink
              className="hover:text-ui-fg-base flex gap-2"
              href={cartHref}
              data-testid="nav-cart-link"
            >
              Cart ({totalQuantity})
            </LocalizedClientLink>
          </div>
        </nav>
      </header>
    </div>
  )
}
