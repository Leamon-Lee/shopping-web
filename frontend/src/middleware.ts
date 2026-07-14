import { NextResponse } from "next/server"
import type { NextRequest } from "next/server"

const TOKEN_COOKIE = "shopping_token"

// ── Route categories ─────────────────────────────────────────────────

const PUBLIC_PATTERNS = [
  /^\/$/,                           // home
  /^\/hall/,                        // marketplace
  /^\/products/,                    // product browsing
  /^\/categories/,                  // category browsing
  /^\/shops/,                       // shop browsing
  /^\/catlog/,                      // category catalog browsing
  /^\/catalog/,                     // category catalog browsing
  /^\/shop/,                        // legacy shop route
  /^\/cart/,                        // cart (guest allowed)
  /^\/auth/,                        // auth pages
  /^\/sign-in/,                     // legacy sign-in pages
  /^\/_next/,                       // Next.js internals
  /^\/api/,                         // API routes (if any)
  /^\/favicon\.ico/,                // favicon
  /^\/images/,                      // static images
  /^\/assets/,                      // static assets
  /\.(png|svg|jpg|jpeg|gif|webp)$/, // image files
]

const CUSTOMER_PATTERNS = [/^\/customer/]
const MANAGER_PATTERNS = [/^\/manager/]
const ADMIN_PATTERNS = [/^\/admin/]
const RESERVED_TOP_LEVEL_SEGMENTS = new Set([
  "_next",
  "admin",
  "api",
  "auth",
  "cart",
  "catalog",
  "catlog",
  "customer",
  "customer-panel",
  "hall",
  "manager",
  "products",
  "shop",
  "shops",
  "sign-in",
])

// ── Helper ───────────────────────────────────────────────────────────

function hasToken(request: NextRequest): boolean {
  return request.cookies.has(TOKEN_COOKIE)
}

function matchesAny(pathname: string, patterns: RegExp[]): boolean {
  return patterns.some((pattern) => pattern.test(pathname))
}

// ── Main middleware ──────────────────────────────────────────────────

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl
  const hallAliasMatch = pathname.match(/^\/([^/]+)\/hall\/?$/)

  if (
    hallAliasMatch &&
    !RESERVED_TOP_LEVEL_SEGMENTS.has(hallAliasMatch[1])
  ) {
    if (!hasToken(request)) {
      const loginUrl = new URL("/auth/login", request.url)
      loginUrl.searchParams.set("redirect", pathname)
      return NextResponse.redirect(loginUrl)
    }

    const rewriteUrl = request.nextUrl.clone()
    rewriteUrl.pathname = `/customer/${hallAliasMatch[1]}/hall`
    return NextResponse.rewrite(rewriteUrl)
  }

  // Allow public routes without authentication
  if (matchesAny(pathname, PUBLIC_PATTERNS)) {
    return NextResponse.next()
  }

  // Check for protected routes
  const isCustomer = matchesAny(pathname, CUSTOMER_PATTERNS)
  const isManager = matchesAny(pathname, MANAGER_PATTERNS)
  const isAdmin = matchesAny(pathname, ADMIN_PATTERNS)

  if (isCustomer || isManager || isAdmin) {
    if (!hasToken(request)) {
      const loginUrl = new URL("/auth/login", request.url)
      loginUrl.searchParams.set("redirect", pathname)
      return NextResponse.redirect(loginUrl)
    }
    // User has a token — allow access (full role check happens on backend API)
    return NextResponse.next()
  }

  // All other routes pass through
  return NextResponse.next()
}

export const config = {
  matcher: [
    "/((?!_next/static|_next/image|favicon.ico|.*\\.(?:png|svg|jpg|jpeg|gif|webp)$).*)",
  ],
}
