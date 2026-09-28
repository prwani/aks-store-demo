import { ref, computed, watch } from 'vue'
import { defineStore } from 'pinia'
import type { Product, CartItem } from '@/types'

export const useProductStore = defineStore('product', () => {
  const products = ref<Product[]>([])
  const count = computed(() => products.value.length)
  const addProducts = (data: Product[]) => {
    products.value.push(...data)
  }
  return { products, count, addProducts }
})

export const useCartStore = defineStore('cart', () => {
  const storedCart = localStorage.getItem('cart')
  const items = ref<CartItem[]>(storedCart ? JSON.parse(storedCart) : [])
  const total = computed(() =>
    items.value.reduce((acc, item) => acc + item.product.price * item.quantity, 0),
  )
  const count = computed(() => items.value.reduce((acc, item) => acc + item.quantity, 0))
  const addItem = (item: CartItem) => {
    const existingItem = items.value.find((i) => i.product.id === item.product.id)
    if (existingItem) {
      existingItem.quantity += item.quantity
    } else {
      items.value.push(item)
    }
  }
  const removeItem = (id: number | string) => {
    const index = items.value.findIndex((i) => i.product.id === id)
    items.value.splice(index, 1)
  }
  const setItemQuantity = (id: number | string, quantity: number) => {
    const item = items.value.find((i) => i.product.id === id)
    if (!item) return false
    item.quantity = Math.max(1, Math.floor(quantity))
    return true
  }
  const clear = () => {
    items.value = []
  }

  // Submits the current cart as an order, same request the "Proceed to
  // Checkout" button makes. Shared by the UI and the WebMCP checkout tool
  // so there's exactly one place that talks to the order API.
  const checkout = async () => {
    const order = {
      customerId: Math.floor(Math.random() * 10000000000).toString(),
      items: items.value.map((item) => ({
        productId: item.product.id,
        quantity: item.quantity,
        price: item.product.price,
      })),
    }

    const response = await fetch('/api/orders', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(order),
    })

    if (!response.ok) {
      throw new Error('Error occurred while submitting order')
    }

    clear()
    return order
  }

  watch(
    items,
    (newItems) => {
      localStorage.setItem('cart', JSON.stringify(newItems))
    },
    { deep: true },
  )
  return { items, total, count, addItem, clear, removeItem, setItemQuantity, checkout }
})
