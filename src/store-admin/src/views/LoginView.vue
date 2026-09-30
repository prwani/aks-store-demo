<template>
  <main class="login">
    <form class="login-form" @submit.prevent="onSubmit">
      <img src="/contoso-pet-store-logo.png" alt="Contoso Pet Store Logo" />
      <h1>Admin sign in</h1>
      <p class="hint">The admin portal requires a username and password.</p>

      <label for="username">Username</label>
      <input id="username" v-model="username" type="text" autocomplete="username" required />

      <label for="password">Password</label>
      <input
        id="password"
        v-model="secret"
        type="password"
        autocomplete="current-password"
        required
      />

      <p v-if="error" class="error">{{ error }}</p>

      <button type="submit" :disabled="loading">{{ loading ? 'Signing in…' : 'Sign in' }}</button>
    </form>
  </main>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { login } from '@/auth'

const router = useRouter()
const route = useRoute()

const username = ref('')
const secret = ref('')
const error = ref('')
const loading = ref(false)

async function onSubmit(): Promise<void> {
  error.value = ''
  loading.value = true
  try {
    await login(username.value, secret.value)
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/'
    router.replace(redirect)
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Unable to sign in'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login {
  display: flex;
  justify-content: center;
  padding-top: 6rem;
}

.login-form {
  display: flex;
  flex-direction: column;
  width: 320px;
  max-width: 90vw;
  padding: 2rem;
  border: 1px solid #ddd;
  border-radius: 8px;
  background-color: #fff;
}

.login-form img {
  width: 120px;
  align-self: center;
}

h1 {
  margin: 0.5rem 0 0.25rem;
  font-size: 1.5rem;
  text-align: center;
}

.hint {
  margin: 0 0 1rem;
  font-size: 0.85rem;
  color: #666;
  text-align: center;
}

label {
  margin-bottom: 0.25rem;
  font-weight: bold;
}

input {
  margin-bottom: 1rem;
  padding: 0.5rem;
  border: 1px solid #ccc;
  border-radius: 4px;
}

button {
  padding: 0.6rem;
  border: none;
  border-radius: 4px;
  background-color: #333;
  color: #fff;
  font-weight: bold;
  cursor: pointer;
}

button:disabled {
  opacity: 0.6;
  cursor: progress;
}

.error {
  margin: 0 0 1rem;
  color: #c00;
  font-size: 0.9rem;
}
</style>
