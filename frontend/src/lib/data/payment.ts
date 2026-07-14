"use server"

export const listCartPaymentMethods = async (..._args: any[]) => {
  return [
    {
      id: "pp_system_default",
      is_enabled: true,
    },
  ]
}
