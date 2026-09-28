<template>
  <TopNav />
  <RouterView />
</template>

<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'
import { RouterView } from 'vue-router'
import { useProductStore } from '@/stores'
import type { Product } from '@/types'
import TopNav from './components/TopNav.vue'
import { registerCartTools } from '@/webmcp/tools'

const productStore = useProductStore()

// Cart tools are relevant on every route (the cart badge/link lives in
// TopNav), so they're registered once for the app's lifetime here rather
// than in a single view.
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

  registerCartTools(webMcpController.signal)
})

onUnmounted(() => {
  webMcpController.abort()
})
</script>

<style scoped></style>
