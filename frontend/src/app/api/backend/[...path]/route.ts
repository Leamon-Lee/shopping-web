import { NextRequest, NextResponse } from "next/server"

const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8001"

async function proxyBackendRequest(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> }
) {
  const { path } = await context.params
  const target = new URL(`/${path.join("/")}`, BACKEND_URL)
  target.search = request.nextUrl.search

  const headers = new Headers(request.headers)
  headers.set("host", target.host)
  // Convert httpOnly cookie to Authorization header for backend auth
  const tokenCookie = request.cookies.get("shopping_token")
  if (tokenCookie?.value) {
    headers.set("Authorization", `Bearer ${tokenCookie.value}`)
  }

  let body: BodyInit | undefined
  if (request.method !== "GET" && request.method !== "HEAD") {
    const contentType = request.headers.get("content-type") || ""
    body = contentType.includes("multipart/form-data")
      ? await request.arrayBuffer()
      : await request.text()
    // Strip original length/encoding headers so fetch sets correct values for the body
    headers.delete("content-length")
    headers.delete("transfer-encoding")
  }

  const response = await fetch(target, {
    method: request.method,
    headers,
    body,
    cache: "no-store",
  })

  const responseHeaders = new Headers(response.headers)
  responseHeaders.delete("content-encoding")
  responseHeaders.delete("content-length")

  return new NextResponse(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers: responseHeaders,
  })
}

export const GET = proxyBackendRequest
export const POST = proxyBackendRequest
export const PUT = proxyBackendRequest
export const PATCH = proxyBackendRequest
export const DELETE = proxyBackendRequest
