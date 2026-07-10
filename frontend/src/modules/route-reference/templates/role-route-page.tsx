import LocalizedClientLink from "@modules/common/components/localized-client-link"

type RouteLink = {
  href: string
  label: string
}

type RoleRoutePageProps = {
  eyebrow: string
  title: string
  description: string
  username?: string
  activePath: string
  links: RouteLink[]
  primaryAction?: RouteLink
  stats?: Array<{
    label: string
    value: string
    detail: string
  }>
}

export default function RoleRoutePage({
  eyebrow,
  title,
  description,
  username,
  activePath,
  links,
  primaryAction,
  stats = [],
}: RoleRoutePageProps) {
  return (
    <div className="min-h-screen bg-ui-bg-base text-ui-fg-base">
      <header className="border-b border-ui-border-base bg-white">
        <div className="content-container flex h-16 items-center justify-between text-small-regular">
          <LocalizedClientLink
            href="/"
            className="txt-compact-xlarge-plus uppercase text-ui-fg-base"
          >
            Shopping Web
          </LocalizedClientLink>
          <nav className="flex items-center gap-x-5 text-ui-fg-subtle">
            <LocalizedClientLink href="/hall" className="hover:text-ui-fg-base">
              Hall
            </LocalizedClientLink>
            <LocalizedClientLink href="/sign-in/customer" className="hover:text-ui-fg-base">
              Sign in
            </LocalizedClientLink>
          </nav>
        </div>
      </header>

      <div className="content-container grid grid-cols-1 gap-8 py-8 small:grid-cols-[260px_1fr]">
        <aside className="small:sticky small:top-8 small:self-start">
          <div className="mb-5">
            <p className="txt-xsmall-plus uppercase text-ui-fg-muted">
              {eyebrow}
            </p>
            {username && (
              <p className="mt-2 text-small-regular text-ui-fg-subtle">
                @{username}
              </p>
            )}
          </div>
          <nav className="flex flex-row gap-2 overflow-x-auto border-b border-ui-border-base pb-4 small:flex-col small:overflow-visible small:border-b-0 small:pb-0">
            {links.map((link) => {
              const isActive = link.href === activePath
              return (
                <LocalizedClientLink
                  key={link.href}
                  href={link.href}
                  className={
                    isActive
                      ? "whitespace-nowrap rounded-md bg-ui-bg-subtle px-3 py-2 text-small-semi text-ui-fg-base"
                      : "whitespace-nowrap rounded-md px-3 py-2 text-small-regular text-ui-fg-subtle hover:bg-ui-bg-subtle hover:text-ui-fg-base"
                  }
                >
                  {link.label}
                </LocalizedClientLink>
              )
            })}
          </nav>
        </aside>

        <main className="flex min-w-0 flex-col gap-y-8">
          <section className="flex flex-col justify-between gap-4 border-b border-ui-border-base pb-8 small:flex-row small:items-end">
            <div>
              <p className="txt-xsmall-plus uppercase text-ui-fg-muted">
                {eyebrow}
              </p>
              <h1 className="mt-2 text-2xl-semi text-ui-fg-base">
                {title}
              </h1>
              <p className="mt-2 max-w-2xl text-small-regular text-ui-fg-subtle">
                {description}
              </p>
            </div>
            {primaryAction && (
              <LocalizedClientLink
                href={primaryAction.href}
                className="inline-flex h-10 items-center justify-center rounded-md border border-ui-border-base px-4 text-small-semi text-ui-fg-base hover:bg-ui-bg-subtle"
              >
                {primaryAction.label}
              </LocalizedClientLink>
            )}
          </section>

          {stats.length > 0 && (
            <section className="grid grid-cols-1 gap-4 small:grid-cols-2 medium:grid-cols-4">
              {stats.map((stat) => (
                <div
                  key={stat.label}
                  className="rounded-rounded border border-ui-border-base bg-white p-5"
                >
                  <p className="text-small-regular text-ui-fg-subtle">
                    {stat.label}
                  </p>
                  <p className="mt-3 text-xl-semi text-ui-fg-base">
                    {stat.value}
                  </p>
                  <p className="mt-1 text-small-regular text-ui-fg-muted">
                    {stat.detail}
                  </p>
                </div>
              ))}
            </section>
          )}

          <section className="grid grid-cols-1 gap-6 medium:grid-cols-[1fr_320px]">
            <div className="rounded-rounded border border-ui-border-base bg-white p-5">
              <h2 className="text-base-semi">Route overview</h2>
              <p className="mt-2 text-small-regular text-ui-fg-subtle">
                This page is wired to the route map and ready to be connected
                to role-specific data and actions.
              </p>
              <div className="mt-5 grid grid-cols-1 gap-3 text-small-regular text-ui-fg-subtle small:grid-cols-2">
                {links.slice(0, 8).map((link) => (
                  <LocalizedClientLink
                    key={link.href}
                    href={link.href}
                    className="rounded-md border border-ui-border-base px-3 py-2 hover:bg-ui-bg-subtle hover:text-ui-fg-base"
                  >
                    {link.label}
                  </LocalizedClientLink>
                ))}
              </div>
            </div>
            <div className="rounded-rounded border border-ui-border-base bg-ui-bg-subtle p-5">
              <h2 className="text-base-semi">Current route</h2>
              <p className="mt-3 break-all text-small-regular text-ui-fg-subtle">
                {activePath}
              </p>
              <p className="mt-4 text-small-regular text-ui-fg-muted">
                Route parameters and child pages are handled by the Next.js app
                router under this path.
              </p>
            </div>
          </section>
        </main>
      </div>
    </div>
  )
}
