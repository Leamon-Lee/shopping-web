"use client"

import { Button } from "@medusajs/ui"
import { useRouter } from "next/navigation"
import { useState, useTransition } from "react"
import {
  backendProductName,
  formatBackendMoney,
} from "@lib/backend-native"
import type { ShoppingCart, Account, Address } from "types/backend"

type PaymentMethod = { id: string; label: string; method_type: string }

type Props = {
  cart: ShoppingCart
  customer: Account
  addresses: Address[]
  paymentMethods: PaymentMethod[]
  addAddressAction: (formData: FormData) => Promise<any[]>
  updateAddressAction: (addressId: string, formData: FormData) => Promise<any[]>
  addPaymentMethodAction: (label: string) => Promise<any[]>
  placeOrderAction: (items: Array<{ product_name: string; quantity: number }>, subtotal: number) => Promise<any>
}

export default function OrderConfirmation({
  cart: initialCart, customer, addresses: initialAddresses, paymentMethods: initialPMs,
  addAddressAction, updateAddressAction, addPaymentMethodAction, placeOrderAction,
}: Props) {
  const router = useRouter()
  const [isPending, startTransition] = useTransition()
  const [addresses, setAddresses] = useState<Address[]>(initialAddresses)
  const [selectedAddressId, setSelectedAddressId] = useState<string>(
    initialAddresses.find((a) => a.is_default_shipping)?.id || initialAddresses[0]?.id || ""
  )
  const [showAddressForm, setShowAddressForm] = useState(false)
  const [editingAddressId, setEditingAddressId] = useState<string | null>(null)
  const [toast, setToast] = useState<{ message: string; type: "success" | "error" } | null>(null)
  const [addressForm, setAddressForm] = useState({
    street: "",
    city: "",
    state: "",
    postal_code: "",
    country: "",
    is_default_shipping: false,
  })
  const [paymentMethods, setPaymentMethods] = useState<PaymentMethod[]>(initialPMs)
  const [selectedPMId, setSelectedPMId] = useState(initialPMs[0]?.id || "")
  const [newPMLabel, setNewPMLabel] = useState("")
  const [showPMForm, setShowPMForm] = useState(false)

  const items = initialCart.items || []
  const subtotal = initialCart.subtotal || initialCart.total || 0

  const resetAddressForm = () => {
    setAddressForm({ street: "", city: "", state: "", postal_code: "", country: "", is_default_shipping: false })
    setShowAddressForm(false)
    setEditingAddressId(null)
  }

  const handleAddAddress = () => {
    startTransition(async () => {
      try {
        const fd = new FormData()
        fd.set("street", addressForm.street)
        fd.set("city", addressForm.city)
        fd.set("state", addressForm.state)
        fd.set("postal_code", addressForm.postal_code)
        fd.set("country", addressForm.country)
        fd.set("is_default_shipping", String(addressForm.is_default_shipping))
        const result = await addAddressAction(fd)
        setAddresses(result)
        const newest = result[result.length - 1]
        if (newest?.id) setSelectedAddressId(newest.id)
        resetAddressForm()
        setToast({ message: "Address added", type: "success" })
        setTimeout(() => setToast(null), 2000)
      } catch (e: any) {
        setToast({ message: e.message || "Failed to add address", type: "error" })
        setTimeout(() => setToast(null), 3000)
      }
    })
  }

  const handleUpdateAddress = () => {
    if (!editingAddressId) return
    startTransition(async () => {
      try {
        const fd = new FormData()
        fd.set("street", addressForm.street)
        fd.set("city", addressForm.city)
        fd.set("state", addressForm.state)
        fd.set("postal_code", addressForm.postal_code)
        fd.set("country", addressForm.country)
        fd.set("is_default_shipping", String(addressForm.is_default_shipping))
        const result = await updateAddressAction(editingAddressId, fd)
        setAddresses(result)
        resetAddressForm()
        setToast({ message: "Address updated", type: "success" })
        setTimeout(() => setToast(null), 2000)
      } catch (e: any) {
        setToast({ message: e.message || "Failed to update address", type: "error" })
        setTimeout(() => setToast(null), 3000)
      }
    })
  }

  const handleEditClick = (addr: Address) => {
    setEditingAddressId(addr.id || null)
    setAddressForm({
      street: addr.street || "",
      city: addr.city || "",
      state: addr.state || "",
      postal_code: addr.postal_code || "",
      country: addr.country || "",
      is_default_shipping: addr.is_default_shipping || false,
    })
    setShowAddressForm(true)
  }

  const handlePayment = () => {
    startTransition(async () => {
      try {
        const orderItems = items.map((item: any) => ({
          product_name: item.product_title || item.product?.name || "",
          quantity: item.quantity || 1,
        }))
        const order = await placeOrderAction(orderItems, subtotal)
        setToast({ message: `Payment successful! Order #${order.order_number}`, type: "success" })
        setTimeout(() => {
          router.push(`/customer/${encodeURIComponent(customer.user_name)}/orders`)
        }, 1500)
      } catch (e: any) {
        setToast({ message: e.message || "Payment failed", type: "error" })
        setTimeout(() => setToast(null), 3000)
      }
    })
  }

  return (
    <div className="grid grid-cols-1 small:grid-cols-[1fr_360px] gap-x-40">
      {toast && (
        <div className="fixed top-20 right-4 z-[100]">
          <div className={`rounded-lg px-4 py-3 text-small-regular shadow-lg ${
            toast.type === "success" ? "bg-green-600 text-white" : "bg-red-600 text-white"
          }`}>
            {toast.message}
          </div>
        </div>
      )}

      {/* Left: items + address */}
      <div className="flex flex-col gap-y-8">
        {/* Cart Items */}
        <div className="bg-white py-6">
          <h2 className="text-xl-semi mb-4">Items</h2>
          <ul className="border-t border-ui-border-base">
            {items.map((item: any, i: number) => (
              <li key={i} className="flex items-center justify-between border-b border-ui-border-base py-4">
                <div>
                  <p className="text-base-regular">{item.product_title || backendProductName(item.product)}</p>
                  <p className="text-small-regular text-ui-fg-muted">Qty {item.quantity}</p>
                </div>
                <p className="text-base-regular">{formatBackendMoney((item.unit_price || item.price) * item.quantity)}</p>
              </li>
            ))}
          </ul>
          <div className="flex justify-between mt-4 text-xl-semi">
            <span>Total</span>
            <span>{formatBackendMoney(subtotal)}</span>
          </div>
        </div>

        {/* Address Section */}
        <div className="bg-white py-6">
          <h2 className="text-xl-semi mb-4">Shipping Address</h2>

          {addresses.length > 0 && (
            <div className="mb-4">
              <label className="text-small-regular text-ui-fg-muted block mb-1">Select address</label>
              <select
                className="w-full border border-ui-border-base rounded-lg p-2 text-small-regular"
                value={selectedAddressId}
                onChange={(e) => setSelectedAddressId(e.target.value)}
              >
                {addresses.map((addr, i) => (
                  <option key={addr.id || i} value={addr.id}>
                    {addr.street}, {addr.city}, {addr.state} {addr.postal_code}, {addr.country}
                    {addr.is_default_shipping ? " (Default)" : ""}
                  </option>
                ))}
              </select>
              <button
                className="text-small-regular text-ui-fg-muted hover:text-ui-fg-base mt-1"
                onClick={() => {
                  const addr = addresses.find((a) => a.id === selectedAddressId)
                  if (addr) handleEditClick(addr)
                }}
              >
                Edit selected address
              </button>
            </div>
          )}

          {!showAddressForm ? (
            <button
              className="text-small-regular text-blue-600 hover:text-blue-800"
              onClick={() => setShowAddressForm(true)}
            >
              + Add new address
            </button>
          ) : (
            <div className="border border-ui-border-base rounded-lg p-4 flex flex-col gap-y-3">
              <p className="text-small-regular font-medium">
                {editingAddressId ? "Edit address" : "New address"}
              </p>
              <input className="border rounded p-2 text-small-regular" placeholder="Street" value={addressForm.street}
                onChange={(e) => setAddressForm({ ...addressForm, street: e.target.value })} />
              <div className="grid grid-cols-2 gap-2">
                <input className="border rounded p-2 text-small-regular" placeholder="City" value={addressForm.city}
                  onChange={(e) => setAddressForm({ ...addressForm, city: e.target.value })} />
                <input className="border rounded p-2 text-small-regular" placeholder="State" value={addressForm.state}
                  onChange={(e) => setAddressForm({ ...addressForm, state: e.target.value })} />
              </div>
              <div className="grid grid-cols-2 gap-2">
                <input className="border rounded p-2 text-small-regular" placeholder="Postal code" value={addressForm.postal_code}
                  onChange={(e) => setAddressForm({ ...addressForm, postal_code: e.target.value })} />
                <input className="border rounded p-2 text-small-regular" placeholder="Country" value={addressForm.country}
                  onChange={(e) => setAddressForm({ ...addressForm, country: e.target.value })} />
              </div>
              <label className="flex items-center gap-2 text-small-regular">
                <input type="checkbox" checked={addressForm.is_default_shipping}
                  onChange={(e) => setAddressForm({ ...addressForm, is_default_shipping: e.target.checked })} />
                Set as default
              </label>
              <div className="flex gap-2">
                <Button variant="secondary" className="h-8 text-small-regular" onClick={resetAddressForm}>
                  Cancel
                </Button>
                <Button variant="secondary" className="h-8 text-small-regular" onClick={editingAddressId ? handleUpdateAddress : handleAddAddress}>
                  {editingAddressId ? "Update" : "Save"}
                </Button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Right: payment */}
      <div className="relative">
        <div className="flex flex-col gap-y-4 sticky top-12 bg-white py-6">
          <h2 className="text-[2rem] leading-[2.75rem]">Summary</h2>
          <div className="flex items-center justify-between text-base-regular">
            <span>Subtotal</span>
            <span>{formatBackendMoney(subtotal)}</span>
          </div>
          <div className="flex items-center justify-between text-base-regular">
            <span>Shipping</span>
            <span>Free</span>
          </div>
          <div className="flex items-center justify-between text-xl-semi border-t pt-4">
            <span>Total</span>
            <span>{formatBackendMoney(subtotal)}</span>
          </div>

          {/* Payment Method */}
          <div className="flex flex-col gap-y-2">
            <p className="text-small-regular text-ui-fg-muted">Payment method</p>
            {paymentMethods.length > 0 && (
              <select className="w-full border rounded p-2 text-small-regular" value={selectedPMId} onChange={(e) => setSelectedPMId(e.target.value)}>
                {paymentMethods.map((pm) => <option key={pm.id} value={pm.id}>{pm.label}</option>)}
              </select>
            )}
            {!showPMForm ? (
              <button className="text-small-regular text-blue-600 hover:text-blue-800 text-left" onClick={() => setShowPMForm(true)}>+ Add payment method</button>
            ) : (
              <div className="flex gap-2">
                <input className="border rounded p-2 text-small-regular flex-1" placeholder="e.g. My Credit Card" value={newPMLabel}
                  onChange={(e) => setNewPMLabel(e.target.value)} />
                <Button variant="secondary" className="h-8 text-small-regular" onClick={() => { setShowPMForm(false); setNewPMLabel("") }}>Cancel</Button>
                <Button variant="secondary" className="h-8 text-small-regular" onClick={() => {
                  if (!newPMLabel.trim()) return
                  startTransition(async () => {
                    try { const result = await addPaymentMethodAction(newPMLabel.trim()); setPaymentMethods(result); setSelectedPMId(result[result.length - 1]?.id || ""); setNewPMLabel(""); setShowPMForm(false) } catch {}
                  })
                }} disabled={isPending}>Save</Button>
              </div>
            )}
          </div>

          <Button className="w-full h-10 mt-4" onClick={handlePayment} disabled={isPending} isLoading={isPending}>
            {isPending ? "Processing..." : "Pay Now"}
          </Button>
        </div>
      </div>
    </div>
  )
}
