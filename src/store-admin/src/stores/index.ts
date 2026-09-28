import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import type { Product, Order } from '@/types'

export const useProductStore = defineStore('product', () => {
  const products = ref<Product[]>([])
  const count = computed(() => products.value.length)
  const addProducts = (data: Product[]) => {
    products.value.push(...data)
  }
  const addProduct = (product: Product) => {
    products.value.push(product)
  }
  const updateProduct = (product: Product) => {
    const index = products.value.findIndex((p) => p.id === product.id)
    if (index === -1) return
    products.value[index] = product
  }
  const removeProduct = (product: Product) => {
    const index = products.value.findIndex((p) => p.id === product.id)
    if (index === -1) return
    products.value.splice(index, 1)
  }

  return { products, count, addProducts, addProduct, updateProduct, removeProduct }
})

export const useOrderStore = defineStore('order', () => {
  const orders = ref<Order[]>([])
  const initialized = ref(false)
  const count = computed(() => orders.value.length)
  const addOrders = (data: Order[]) => {
    orders.value.push(...data)
  }
  const addOrder = (order: Order) => {
    orders.value.push(order)
    initialized.value = true
  }
  const removeOrder = (order: Order) => {
    const index = orders.value.findIndex((o) => o.id === order.id)
    if (index === -1) return
    orders.value.splice(index, 1)
  }

  // Shared by the "Complete Order" button (OrderDetailView) and the
  // update_order_status WebMCP tool, so both paths hit the same makeline
  // API call and update the same reactive `orders` state.
  const updateOrderStatus = async (orderId: string | number, status: number): Promise<Order> => {
    const foundOrder = orders.value.find((o) => o.orderId == orderId)
    if (!foundOrder) {
      throw new Error(`Order ${orderId} not found`)
    }

    const updatedOrder = { ...foundOrder, status }
    const response = await fetch('/api/makeline/order', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updatedOrder),
    })

    if (!response.ok) {
      throw new Error('Error occurred while processing order')
    }

    // The makeline service removes completed orders from the pending
    // queue, so mirror that locally the same way the UI button does.
    removeOrder(foundOrder)
    return updatedOrder
  }

  return { orders, count, initialized, addOrders, addOrder, removeOrder, updateOrderStatus }
})
