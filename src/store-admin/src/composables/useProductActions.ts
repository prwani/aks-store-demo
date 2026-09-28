import { useProductStore } from '@/stores'
import type { Product } from '@/types'

const productServiceUrl = '/api/product'

/**
 * Product create/update/delete calls that hit the product-service API.
 * Kept as a composable (rather than Pinia store actions) because the store
 * already has local-only `addProduct`/`updateProduct`/`removeProduct`
 * mutators used elsewhere for optimistic array updates; these functions
 * perform the network call and then delegate to those same mutators so both
 * the admin UI (ProductFormView) and the create/update/delete_product
 * WebMCP tools stay in sync with one code path.
 */
export function useProductActions() {
  const productStore = useProductStore()

  async function createProduct(product: Product): Promise<Product> {
    const response = await fetch(productServiceUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(product),
    })
    if (!response.ok) {
      throw new Error('Error occurred while saving product')
    }
    const saved: Product = await response.json()
    productStore.addProduct(saved)
    return saved
  }

  async function updateProduct(product: Product): Promise<Product> {
    const response = await fetch(productServiceUrl, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(product),
    })
    if (!response.ok) {
      throw new Error('Error occurred while saving product')
    }
    const saved: Product = await response.json()
    productStore.updateProduct(saved)
    return saved
  }

  async function deleteProduct(productId: string | number): Promise<void> {
    const response = await fetch(`${productServiceUrl}/${productId}`, {
      method: 'DELETE',
    })
    if (!response.ok) {
      throw new Error('Error occurred while deleting product')
    }
    const existing = productStore.products.find((p) => String(p.id) === String(productId))
    if (existing) {
      productStore.removeProduct(existing)
    }
  }

  return { createProduct, updateProduct, deleteProduct }
}
