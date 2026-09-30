import { computed, ref } from 'vue'

// Small HTTP Basic auth helper shared by the portal.
//
// The credentials are verified server-side by nginx (every /api/* location is
// protected with auth_basic). The login page posts them once to
// /api/auth/login; when nginx accepts them they are kept for the browser
// session and attached to every subsequent API request.
const STORAGE_KEY = 'store-front-auth'

const credentials = ref<string | null>(sessionStorage.getItem(STORAGE_KEY))

export const isAuthenticated = computed(() => credentials.value !== null)

/** Headers to merge into every API request. */
export function authHeaders(): Record<string, string> {
  return credentials.value ? { Authorization: `Basic ${credentials.value}` } : {}
}

/** fetch() wrapper that adds the Basic auth header to API calls. */
export async function authFetch(input: string, init: RequestInit = {}): Promise<Response> {
  const response = await fetch(input, {
    ...init,
    headers: { ...(init.headers as Record<string, string> | undefined), ...authHeaders() },
  })

  if (response.status === 401) {
    logout()
  }

  return response
}

/**
 * Validate credentials against the nginx protected login endpoint and store
 * them for the session when they are accepted.
 */
export async function login(username: string, secret: string): Promise<void> {
  const token = btoa(`${username}:${secret}`)
  const response = await fetch('/api/auth/login', {
    headers: { Authorization: `Basic ${token}` },
  })

  if (response.status === 401) {
    throw new Error('Invalid username or password')
  }
  if (!response.ok) {
    throw new Error('Unable to sign in, please try again')
  }

  credentials.value = token
  sessionStorage.setItem(STORAGE_KEY, token)
}

export function logout(): void {
  credentials.value = null
  sessionStorage.removeItem(STORAGE_KEY)
}
