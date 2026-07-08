import type {
  BackendProduct,
  BackendProductCategory,
  BackendProductFormPayload,
} from "../../types/backend"
import type { FrontendCategory, FrontendProduct, ProductFormValues } from "../../types/storefront"
import { formatMoney, slugify, unwrapBackendValue } from "./shared"

export function mapBackendCategoryToFrontendCategory(
  category: BackendProductCategory
): FrontendCategory {
  return {
    name: unwrapBackendValue(category.name),
    description: unwrapBackendValue(category.description),
  }
}

export function mapBackendProductToFrontendProduct(
  product: BackendProduct
): FrontendProduct {
  const name = unwrapBackendValue(product.name)
  const price = unwrapBackendValue(product.price)

  return {
    id: slugify(name),
    name,
    title: name,
    description: unwrapBackendValue(product.description),
    price,
    displayPrice: formatMoney(price),
    availableItemCount: unwrapBackendValue(product.available_item_count),
    category: mapBackendCategoryToFrontendCategory(product.category),
  }
}

export function mapFrontendProductFormToCreateProductPayload(
  form: ProductFormValues
): BackendProductFormPayload {
  return {
    name: form.name.trim(),
    description: form.description.trim(),
    price: Number(form.price),
    available_item_count: Number(form.availableItemCount),
    category: {
      name: form.categoryName.trim(),
      description: form.categoryDescription.trim(),
    },
  }
}

export const mapFrontendProductFormToUpdateProductPayload =
  mapFrontendProductFormToCreateProductPayload
