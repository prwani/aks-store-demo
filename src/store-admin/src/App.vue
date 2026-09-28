<template>
  <TopNav />
  <router-view />
</template>

<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'
import { useProductStore, useOrderStore } from '@/stores'
import type { Product, Order } from '@/types'
import TopNav from './components/TopNav.vue'
import { registerOrderTools } from '@/webmcp/tools'

const productStore = useProductStore()
const orderStore = useOrderStore()

// Orders (like the order list itself) are relevant across the whole admin
// app, so order tools are registered once for the app's lifetime here.
const webMcpController = new AbortController()

onMounted(() => {
  if (productStore.count === 0) {
    console.log('Fetching products')
    fetch('/api/products')
      .then((response) => response.json())
      .then((data: Product[]) => {
        productStore.addProducts(data)
        console.log(`Fetched ${data.length} products`)
      })
      .catch((error) => {
        console.log(error)
        alert('Error occurred while fetching products')
      })
  }
  if (orderStore.count === 0) {
    console.log('Fetching orders')
    fetch('/api/makeline/order/fetch')
      .then((response) => response.json())
      .then((data: Order[]) => {
        orderStore.addOrders(data)
        console.log(`Fetched ${data.length} orders`)
      })
      .catch((error) => {
        console.log(error)
        orderStore.initialized = true
        console.error(`Error occurred while fetching orders`, error)
      })
  }

  registerOrderTools(webMcpController.signal)
})

onUnmounted(() => {
  webMcpController.abort()
})
</script>

<style scoped></style>
