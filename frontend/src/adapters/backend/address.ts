import type { BackendAddress, BackendAddressPayload } from "../../types/backend"
import type { AddressFormValues, FrontendAddress } from "../../types/storefront"

export function mapBackendAddressToFrontendAddress(
  address: BackendAddress
): FrontendAddress {
  return {
    street: address.street,
    city: address.city,
    state: address.state,
    postalCode: address.postal_code,
    country: address.country,
  }
}

export function mapFrontendAddressFormToBackendAddressPayload(
  form: AddressFormValues
): BackendAddressPayload {
  return {
    street: form.street.trim(),
    city: form.city.trim(),
    state: form.state.trim(),
    postal_code: form.postalCode.trim(),
    country: form.country.trim(),
  }
}
