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

  const response = await fetch(target, {
    method: request.method,
    headers,
    body:
      request.method === "GET" || request.method === "HEAD"
        ? undefined
        : await request.text(),
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
