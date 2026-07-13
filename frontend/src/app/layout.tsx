import { getBaseURL } from "@lib/util/env"
import { Metadata } from "next"
import "styles/globals.css"
import BfCacheGuard from "@modules/common/components/bfcache-guard"

export const metadata: Metadata = {
  metadataBase: new URL(getBaseURL()),
}

export default function RootLayout(props: { children: React.ReactNode }) {
  return (
    <html lang="en" data-mode="light" translate="no">
      <body>
        <BfCacheGuard />
        <main className="relative">{props.children}</main>
      </body>
    </html>
  )
}
