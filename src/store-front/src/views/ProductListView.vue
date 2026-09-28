<template>
  <div class="product-list">
    <ProductCard v-for="product in products" :key="product.id" :product="product" />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted } from 'vue'
import { useProductStore } from '@/stores'
import ProductCard from '@/components/ProductCard.vue'
import { registerProductBrowsingTools } from '@/webmcp/tools'

const productStore = useProductStore()
const products = computed(() => productStore.products)

const webMcpController = new AbortController()

onMounted(() => {
  registerProductBrowsingTools(webMcpController.signal)
})

onUnmounted(() => {
  webMcpController.abort()
})
</script>
