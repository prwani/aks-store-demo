import { createRouter, createWebHistory } from 'vue-router'
import OrderListView from '../views/OrderListView.vue'
import OrderDetailView from '../views/OrderDetailView.vue'
import ProductListView from '../views/ProductListView.vue'
import ProductDetailView from '../views/ProductDetailView.vue'
import ProductFormView from '../views/ProductFormView.vue'
import LoginView from '../views/LoginView.vue'
import { isAuthenticated } from '@/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/login', component: LoginView, meta: { public: true } },
    { path: '/', component: OrderListView },
    { path: '/orders', component: OrderListView },
    { path: '/order/:id', component: OrderDetailView },
    { path: '/products', component: ProductListView },
    { path: '/product/:id', component: ProductDetailView },
    { path: '/product/:id/edit', component: ProductFormView },
    { path: '/product/add', component: ProductFormView },
  ],
})

// Every route except the login page requires credentials. The credentials
// themselves are always verified by nginx on each API call; this guard only
// keeps the UI from rendering views that cannot load any data.
router.beforeEach((to) => {
  if (to.meta.public) {
    return isAuthenticated.value && to.path === '/login' ? { path: '/' } : true
  }

  if (!isAuthenticated.value) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }

  return true
})

export default router
