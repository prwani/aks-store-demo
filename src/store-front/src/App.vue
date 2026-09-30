<template>
  <TopNav v-if="isAuthenticated" />
  <RouterView />
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, watch } from 'vue'
import { RouterView } from 'vue-router'
import { useProductStore } from '@/stores'
import type { Product } from '@/types'
import TopNav from './components/TopNav.vue'
import { registerCartTools } from '@/webmcp/tools'
import { authFetch, isAuthenticated } from '@/auth'

const productStore = useProductStore()

// Cart tools are relevant on every route (the cart badge/link lives in
// TopNav), so they're registered once for the app's lifetime here rather
// than in a single view.
const webMcpController = new AbortController()

// Products are behind the authenticated API, so they're only fetched once the
// user has signed in (either on load or right after the login form succeeds).
const fetchProducts = () => {
  if (!isAuthenticated.value || productStore.count > 0) return

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

watch(isAuthenticated, fetchProducts)

onMounted(() => {
  fetchProducts()

  registerCartTools(webMcpController.signal)
})

onUnmounted(() => {
  webMcpController.abort()
})
</script>

<style scoped></style>
