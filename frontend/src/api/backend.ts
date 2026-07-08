import type {
  BackendAccount,
  BackendLoginPayload,
  BackendOrder,
  BackendOrderPayload,
  BackendProduct,
  BackendProductCategory,
  BackendProductFormPayload,
  BackendRegisterAccountPayload,
  BackendShoppingCart,
} from "../types/backend"

export class BackendEndpointUnavailableError extends Error {
  constructor(operation: string) {
    super(
      `Backend endpoint for "${operation}" is not defined in the current Python backend.`
    )
    this.name = "BackendEndpointUnavailableError"
  }
}

function unavailable(operation: string): never {
  throw new BackendEndpointUnavailableError(operation)
}

export async function listProducts(): Promise<BackendProduct[]> {
  return unavailable("listProducts")
}

export async function getProduct(): Promise<BackendProduct> {
  return unavailable("getProduct")
}

export async function createProduct(
  _payload: BackendProductFormPayload
): Promise<BackendProduct> {
  return unavailable("createProduct")
}

export async function listCategories(): Promise<BackendProductCategory[]> {
  return unavailable("listCategories")
}

export async function getCart(): Promise<BackendShoppingCart> {
  return unavailable("getCart")
}

export async function placeOrder(
  _payload: BackendOrderPayload
): Promise<BackendOrder> {
  return unavailable("placeOrder")
}

export async function login(
  _payload: BackendLoginPayload
): Promise<BackendAccount> {
  return unavailable("login")
}

export async function registerAccount(
  _payload: BackendRegisterAccountPayload
): Promise<BackendAccount> {
  return unavailable("registerAccount")
}
