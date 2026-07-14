"use client"

import React, { useEffect, useActionState } from "react";

import Input from "@modules/common/components/input"

import AccountInfo from "../account-info"
import type {
  BackendAddress,
  BackendCart,
  BackendCartLineItem,
  BackendCollection,
  BackendCustomer,
  BackendOrder,
  BackendOrderLineItem,
  BackendPaymentSession,
  BackendPrice,
  BackendProduct,
  BackendProductCategory,
  BackendProductImage,
  BackendProductListParams,
  BackendProductOption,
  BackendProductVariant,
  BackendPromotion,
  BackendRecord,
  BackendRegion,
  BackendShippingOption,
} from "types/backend"
import { updateCustomer } from "@lib/data/customer"

type MyInformationProps = {
  customer: BackendCustomer
}

const ProfileEmail: React.FC<MyInformationProps> = ({ customer }) => {
  const [successState, setSuccessState] = React.useState(false)

  const updateCustomerPhone = async (
    _currentState: Record<string, unknown>,
    formData: FormData
  ) => {
    try {
      await updateCustomer(_currentState, formData)
      return { success: true, error: null }
    } catch (error: any) {
      return { success: false, error: error.toString() }
    }
  }

  const [state, formAction] = useActionState(updateCustomerPhone, {
    error: false,
    success: false,
  })

  const clearState = () => {
    setSuccessState(false)
  }

  useEffect(() => {
    setSuccessState(state.success)
  }, [state.success])

  return (
    <form action={formAction} className="w-full">
      <AccountInfo
        label="Phone"
        currentInfo={`${customer.phone}`}
        isSuccess={successState}
        isError={!!state.error}
        errorMessage={state.error}
        clearState={clearState}
        data-testid="account-phone-editor"
      >
        <div className="grid grid-cols-1 gap-y-2">
          <Input
            label="Phone"
            name="phone"
            type="phone"
            autoComplete="phone"
            required
            defaultValue={customer.phone ?? ""}
            data-testid="phone-input"
          />
        </div>
      </AccountInfo>
    </form>
  )
}

export default ProfileEmail
