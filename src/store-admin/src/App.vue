<template>
  <TopNav v-if="isAuthenticated" />
  <router-view />
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useProductStore, useOrderStore } from '@/stores'
import type { Product, Order } from '@/types'
import TopNav from './components/TopNav.vue'
import { registerOrderTools } from '@/webmcp/tools'
import { authFetch, isAuthenticated } from '@/auth'

const router = useRouter()
const route = useRoute()
const productStore = useProductStore()
const orderStore = useOrderStore()

// A 401 from any API call clears the stored credentials (see authFetch); this
// sends the user back to the login page instead of leaving them on a screen
// that can no longer load or submit data.
watch(isAuthenticated, (authenticated) => {
  if (!authenticated && route.path !== '/login') {
    router.push({ path: '/login', query: { redirect: route.fullPath } })
  }
})

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
        if (!response.ok) {
          throw new Error(`Failed to fetch orders: ${response.status}`)
        }
        return response.json()
      })
      .then((data: Order[]) => {
        if (Array.isArray(data)) {
          orderStore.addOrders(data)
          console.log(`Fetched ${data.length} orders`)
        } else {
          console.error('Unexpected response format:', data)
          orderStore.initialized = true
        }
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
