import type {
  BackendAccount,
  BackendLoginPayload,
  BackendRegisterAccountPayload,
} from "../../types/backend"
import type { FrontendUser, LoginFormValues, RegisterFormValues } from "../../types/storefront"
import { mapBackendAddressToFrontendAddress, mapFrontendAddressFormToBackendAddressPayload } from "./address"
import { unwrapBackendValue } from "./shared"

export function mapBackendAccountToFrontendUser(
  account: BackendAccount
): FrontendUser {
  return {
    userName: unwrapBackendValue(account.user_name),
    status: account.status,
    firstName: account.name.first_name,
    lastName: account.name.last_name,
    email: unwrapBackendValue(account.email),
    phone: `${account.phone.country_code} ${account.phone.number}`.trim(),
    shippingAddress: mapBackendAddressToFrontendAddress(
      account.shipping_address
    ),
  }
}

export function mapFrontendLoginFormToLoginPayload(
  form: LoginFormValues
): BackendLoginPayload {
  return {
    user_name: form.userName.trim(),
    password: form.password,
  }
}

export function mapFrontendRegisterFormToCreateAccountPayload(
  form: RegisterFormValues
): BackendRegisterAccountPayload {
  return {
    user_name: form.userName.trim(),
    password: form.password,
    name: {
      first_name: form.firstName.trim(),
      last_name: form.lastName.trim(),
    },
    email: form.email.trim(),
    phone: {
      country_code: form.countryCode.trim(),
      number: form.phoneNumber.trim(),
    },
    shipping_address: mapFrontendAddressFormToBackendAddressPayload(
      form.shippingAddress
    ),
  }
}
