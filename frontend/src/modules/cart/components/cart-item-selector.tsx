"use client"

import { useState, useTransition } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@medusajs/ui"
import { backendLineTotal, backendProductName, formatBackendMoney, unwrapBackendValue } from "@lib/backend-native"

type Props = {
  items: any[]
  removeAction: (formData: FormData) => Promise<void>
  checkoutAction: (formData: FormData) => Promise<void>
}

export default function CartItemSelector({ items, removeAction, checkoutAction }: Props) {
  const router = useRouter()
  const [isPending, startTransition] = useTransition()
  const [selected, setSelected] = useState<Set<string>>(() => new Set(items.map((i: any) => backendProductName(i.product))))

  const toggle = (name: string) => {
    setSelected((prev) => {
      const next = new Set(prev)
      if (next.has(name)) next.delete(name)
      else next.add(name)
      return next
    })
  }
  const toggleAll = () => {
    if (selected.size === items.length) setSelected(new Set())
    else setSelected(new Set(items.map((i: any) => backendProductName(i.product))))
  }

  const selectedItems = items.filter((i: any) => selected.has(backendProductName(i.product)))
  const subtotal = selectedItems.reduce((sum: number, i: any) => sum + backendLineTotal(i), 0)

  return (
    <div className="grid grid-cols-1 small:grid-cols-[1fr_360px] gap-x-40">
      <div className="flex flex-col bg-white py-6 gap-y-6">
        <div>
          <div className="pb-3 flex items-center justify-between">
            <h1 className="text-[2rem] leading-[2.75rem]">Cart</h1>
            <button className="text-small-regular text-blue-600 hover:text-blue-800" onClick={toggleAll}>
              {selected.size === items.length ? "Deselect all" : "Select all"}
            </button>
          </div>
          <ul className="border-t border-ui-border-base">
            {items.map((item: any) => {
              const name = backendProductName(item.product)
              return (
                <li className="flex items-center justify-between border-b border-ui-border-base py-4" key={name}>
                  <div className="flex items-center gap-3">
                    <input type="checkbox" checked={selected.has(name)} onChange={() => toggle(name)} className="w-4 h-4" />
                    <div>
                      <p className="text-base-regular text-ui-fg-base">{name}</p>
                      <p className="text-small-regular text-ui-fg-muted">Qty {unwrapBackendValue(item.quantity)}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <p className="text-base-regular text-ui-fg-subtle">{formatBackendMoney(backendLineTotal(item))}</p>
                    <Button variant="secondary" className="h-8 text-small-regular" isLoading={isPending} onClick={() => {
                      startTransition(async () => {
                        const fd = new FormData()
                        fd.set("product_name", name)
                        await removeAction(fd)
                        router.refresh()
                      })
                    }}>Remove</Button>
                  </div>
                </li>
              )
            })}
          </ul>
        </div>
      </div>
      <div className="relative">
        <div className="flex flex-col gap-y-4 sticky top-12 bg-white py-6">
          <h2 className="text-[2rem] leading-[2.75rem]">Summary</h2>
          <div className="flex items-center justify-between text-base-regular">
            <span>Selected</span>
            <span>{selectedItems.length} of {items.length}</span>
          </div>
          <div className="flex items-center justify-between text-base-regular">
            <span>Subtotal</span>
            <span>{formatBackendMoney(subtotal)}</span>
          </div>
          <form
            onSubmit={(event) => {
              event.preventDefault()
              const form = event.currentTarget
              startTransition(async () => {
                await checkoutAction(new FormData(form))
                router.push("/checkout")
              })
            }}
          >
            <input type="hidden" name="selected_items" value={selectedItems.map((i: any) => backendProductName(i.product)).join("|")} />
            <Button className="w-full h-10" type="submit" disabled={selectedItems.length === 0 || isPending} isLoading={isPending}>
              Complete order ({selectedItems.length})
            </Button>
          </form>
        </div>
      </div>
    </div>
  )
}
