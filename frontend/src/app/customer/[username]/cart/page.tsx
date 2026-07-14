import { cartHrefForUsername } from "@lib/cart-url"
import { retrieveCustomer } from "@lib/data/customer"
import { redirect } from "next/navigation"

export default async function CustomerCart(props: {
  params: Promise<{ username: string }>
}) {
  const { username } = await props.params
  const customer = await retrieveCustomer()
  if (customer?.user_name) {
    redirect(cartHrefForUsername(customer.user_name))
  }

  redirect(cartHrefForUsername(username))
}
