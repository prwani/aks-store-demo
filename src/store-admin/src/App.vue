<template>
  <TopNav v-if="isAuthenticated" />
  <router-view />
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, watch } from 'vue'
import { useProductStore, useOrderStore } from '@/stores'
import type { Product, Order } from '@/types'
import TopNav from './components/TopNav.vue'
import { registerOrderTools } from '@/webmcp/tools'
import { authFetch, isAuthenticated } from '@/auth'

const productStore = useProductStore()
const orderStore = useOrderStore()

// Orders (like the order list itself) are relevant across the whole admin
// app, so order tools are registered once for the app's lifetime here.
const webMcpController = new AbortController()

// The admin APIs are behind authentication, so data is only fetched once the
// user has signed in (either on load or right after the login form succeeds).
const fetchData = () => {
  if (!isAuthenticated.value) return

  if (productStore.count === 0) {
    console.log('Fetching products')
    authFetch('/api/products')
      .then((response) => {
        if (!response.ok) throw new Error(`Request failed with status ${response.status}`)
        return response.json()
      })
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
    authFetch('/api/makeline/order/fetch')
      .then((response) => {
        if (!response.ok) throw new Error(`Request failed with status ${response.status}`)
        return response.json()
      })
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
}

watch(isAuthenticated, fetchData)

onMounted(() => {
  fetchData()

  registerOrderTools(webMcpController.signal)
})

onUnmounted(() => {
  webMcpController.abort()
})
</script>

<style scoped></style>
