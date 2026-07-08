import type { BackendProduct, BackendShoppingCart } from "../types/backend"

export const backendProductFixtures: BackendProduct[] = [
  {
    name: { value: "Everyday Tote" },
    description: {
      value: "A durable carryall for daily shopping and errands.",
    },
    price: { value: 48 },
    available_item_count: { value: 24 },
    category: {
      name: { value: "Accessories" },
      description: { value: "Functional add-ons for everyday commerce." },
    },
  },
  {
    name: { value: "Cloud Cotton Hoodie" },
    description: {
      value: "Soft midweight fleece with a relaxed ecommerce-staple fit.",
    },
    price: { value: 86 },
    available_item_count: { value: 12 },
    category: {
      name: { value: "Apparel" },
      description: { value: "Wearable essentials and seasonal basics." },
    },
  },
  {
    name: { value: "Desk Shelf" },
    description: {
      value: "A compact shelf for organizing checkout, packing, or desk tools.",
    },
    price: { value: 120 },
    available_item_count: { value: 8 },
    category: {
      name: { value: "Home" },
      description: { value: "Useful goods for home and workspace." },
    },
  },
]

export const backendCartFixture: BackendShoppingCart = {
  items: [],
}
