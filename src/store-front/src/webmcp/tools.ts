// WebMCP (https://github.com/webmachinelearning/webmcp) tool registration for
// store-front. Tools are thin adapters over the existing Pinia stores/API
// calls used by the UI — they must not duplicate business logic, only call
// the same store actions the buttons already call, so the UI and any agent
// invoking a tool always see the same reactive state.
//
// Tools are registered dynamically per-view (via each view's onMounted) and
// unregistered on unmount using an AbortSignal, per the spec's tool-budget
// best practice, rather than one large static list declared in main.ts.
import { useCartStore, useProductStore } from '@/stores'
import type { Product } from '@/types'

/**
 * Resolves the WebMCP entry point, preferring `document.modelContext` (used
 * throughout the spec's examples) and falling back to `navigator.modelContext`
 * in case a given implementation exposes it there instead. Returns undefined
 * when WebMCP isn't supported, so callers can no-op gracefully.
 */
function getModelContext(): ModelContext | undefined {
  if (typeof document !== 'undefined' && document.modelContext) {
    return document.modelContext
  }
  if (typeof navigator !== 'undefined' && navigator.modelContext) {
    return navigator.modelContext
  }
  return undefined
}

function textResult(text: string, isError = false): ModelContextToolResult {
  return { content: [{ type: 'text', text }], isError }
}

function summarizeProduct(product: Product) {
  return {
    id: product.id,
    name: product.name,
    price: product.price,
    description: product.description,
  }
}

/**
 * Registers read-only product browsing tools. Scoped to ProductListView
 * since that's where an agent (or user) is browsing the catalog.
 */
export async function registerProductBrowsingTools(signal: AbortSignal): Promise<void> {
  const modelContext = getModelContext()
  if (!modelContext) return

  const productStore = useProductStore()

  await modelContext.registerTool(
    {
      name: 'search_products',
      description:
        'Searches the product catalog by a natural-language keyword matched against product name and description. Omit the query to list every available product.',
      inputSchema: {
        type: 'object',
        properties: {
          query: {
            type: 'string',
            description: 'Optional keyword to filter products by. Omit to list all products.',
          },
        },
      },
      execute(args: Record<string, unknown>) {
        const { query } = args
        const term = typeof query === 'string' ? query.trim().toLowerCase() : ''
        const matches = term
          ? productStore.products.filter(
              (p) =>
                p.name.toLowerCase().includes(term) ||
                (p.description ?? '').toLowerCase().includes(term),
            )
          : productStore.products

        return textResult(JSON.stringify(matches.map(summarizeProduct)))
      },
    },
    { signal },
  )

  await modelContext.registerTool(
    {
      name: 'get_product_details',
      description: 'Returns the full details (name, price, description, image) for one product ID.',
      inputSchema: {
        type: 'object',
        properties: {
          productId: {
            type: 'string',
            description: 'The ID of the product to look up.',
          },
        },
        required: ['productId'],
      },
      execute(args: Record<string, unknown>) {
        const { productId } = args
        const product = productStore.products.find((p) => String(p.id) === String(productId))
        if (!product) {
          return textResult(
            `No product found with ID "${String(productId)}". Use search_products to find a valid product ID.`,
            true,
          )
        }
        return textResult(JSON.stringify(product))
      },
    },
    { signal },
  )
}

/**
 * Registers cart & checkout tools. Registered globally from App.vue (rather
 * than a single view) because the cart badge/link in TopNav, and the cart
 * itself, are relevant on every route — not just the cart page.
 */
export async function registerCartTools(signal: AbortSignal): Promise<void> {
  const modelContext = getModelContext()
  if (!modelContext) return

  const cartStore = useCartStore()
  const productStore = useProductStore()

  await modelContext.registerTool(
    {
      name: 'get_cart',
      description: "Returns the current user's shopping cart contents and total price.",
      execute() {
        return textResult(
          JSON.stringify({
            items: cartStore.items,
            total: cartStore.total,
            count: cartStore.count,
          }),
        )
      },
    },
    { signal },
  )

  await modelContext.registerTool(
    {
      name: 'add_to_cart',
      description: 'Adds a quantity of a product to the shopping cart.',
      inputSchema: {
        type: 'object',
        properties: {
          productId: { type: 'string', description: 'The ID of the product to add.' },
          quantity: {
            type: 'number',
            description: 'How many units to add. Must be a positive whole number.',
          },
        },
        required: ['productId', 'quantity'],
      },
      execute(args: Record<string, unknown>) {
        const { productId, quantity } = args
        const qty = Number(quantity)
        if (!Number.isFinite(qty) || qty < 1) {
          return textResult('quantity must be a positive whole number.', true)
        }
        const product = productStore.products.find((p) => String(p.id) === String(productId))
        if (!product) {
          return textResult(
            `No product found with ID "${String(productId)}". Use search_products to find a valid product ID.`,
            true,
          )
        }
        cartStore.addItem({ product, quantity: Math.floor(qty) })
        return textResult(`Added ${Math.floor(qty)} x "${product.name}" to the cart.`)
      },
    },
    { signal },
  )

  await modelContext.registerTool(
    {
      name: 'update_cart_item',
      description: "Changes the quantity of a product already in the cart. Use add_to_cart if it isn't in the cart yet.",
      inputSchema: {
        type: 'object',
        properties: {
          productId: { type: 'string', description: 'The ID of the product already in the cart.' },
          quantity: {
            type: 'number',
            description: 'The new quantity. Must be a positive whole number.',
          },
        },
        required: ['productId', 'quantity'],
      },
      execute(args: Record<string, unknown>) {
        const { productId, quantity } = args
        const qty = Number(quantity)
        if (!Number.isFinite(qty) || qty < 1) {
          return textResult('quantity must be a positive whole number.', true)
        }
        const updated = cartStore.setItemQuantity(productId as string | number, qty)
        if (!updated) {
          return textResult(
            `No cart item found for product ID "${String(productId)}". Use add_to_cart to add it first.`,
            true,
          )
        }
        return textResult(`Updated quantity for product "${String(productId)}" to ${Math.floor(qty)}.`)
      },
    },
    { signal },
  )

  await modelContext.registerTool(
    {
      name: 'remove_from_cart',
      description: 'Removes a product from the shopping cart entirely.',
      inputSchema: {
        type: 'object',
        properties: {
          productId: { type: 'string', description: 'The ID of the product to remove from the cart.' },
        },
        required: ['productId'],
      },
      execute(args: Record<string, unknown>) {
        const { productId } = args
        const existed = cartStore.items.some((i) => String(i.product.id) === String(productId))
        if (!existed) {
          return textResult(`No cart item found for product ID "${String(productId)}".`, true)
        }
        cartStore.removeItem(productId as string | number)
        return textResult(`Removed product "${String(productId)}" from the cart.`)
      },
    },
    { signal },
  )

  await modelContext.registerTool(
    {
      name: 'checkout',
      description:
        'Submits the current cart as an order (the same action as the "Proceed to Checkout" button) and clears the cart. Requires at least one item in the cart.',
      execute() {
        if (cartStore.items.length === 0) {
          return textResult('The cart is empty. Add items with add_to_cart before checking out.', true)
        }
        return cartStore
          .checkout()
          .then((order) => textResult(`Order submitted successfully for customer ${order.customerId}.`))
          .catch(() => textResult('Error occurred while submitting the order. Please try again.', true))
      },
    },
    { signal },
  )
}
