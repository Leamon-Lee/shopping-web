import { NextRequest, NextResponse } from "next/server"

const TOKEN_COOKIE = "shopping_token"
const CART_ID_COOKIE = "shopping_cart_id"

export async function GET(request: NextRequest) {
  const redirectPath = request.nextUrl.searchParams.get("redirect") || "/"
  const loginUrl = new URL("/auth/login", request.url)
  loginUrl.searchParams.set("redirect", redirectPath)

  const response = NextResponse.redirect(loginUrl)
  response.cookies.delete(TOKEN_COOKIE)
  response.cookies.delete(CART_ID_COOKIE)
  return response
}
