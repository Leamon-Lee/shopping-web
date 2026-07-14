"use server"

import { cartHrefForUsername } from "@lib/cart-url"
import { retrieveCustomer } from "@lib/data/customer"

export async function getServerCartHref(username?: string | null): Promise<string> {
  const customer = await retrieveCustomer()
  const fallbackUsername = username ? decodeURIComponent(username) : username
  return cartHrefForUsername(customer?.user_name || fallbackUsername)
}
