// WebMCP (https://github.com/webmachinelearning/webmcp) tool registration for
// store-admin. Tools are thin adapters over the existing Pinia stores and the
// useProductActions composable — they must not duplicate business logic,
// only call the same code paths the UI buttons already call.
//
// Tools are registered dynamically per-view (via each view's onMounted) and
// unregistered on unmount using an AbortSignal, per the spec's tool-budget
// best practice, rather than one large static list declared in main.ts.
//
// NOTE: this app currently has no authentication/authorization guard on any
// of its UI actions (verified: no auth/login/role code exists anywhere in
// store-admin). The product write tools below therefore have the same
// (absence of) gating as the buttons they adapt — this is a pre-existing
// property of the app, not something introduced by WebMCP support.
import { useOrderStore, useProductStore } from '@/stores'
import { useProductActions } from '@/composables/useProductActions'
import type { Order, Product } from '@/types'

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

function summarizeOrder(order: Order) {
  return {
    orderId: order.orderId,
    customerId: order.customerId,
    status: order.status === 0 ? 'pending' : 'completed',
    total: order.items.reduce((total, item) => total + item.quantity * item.price, 0),
  }
}

// Backend order status is numeric (0 = pending, 1 = completed); accept the
// natural-language strings an agent is more likely to pass and map them.
function parseStatus(status: unknown): number | undefined {
  if (typeof status === 'number') return status
  if (typeof status === 'string') {
    const normalized = status.trim().toLowerCase()
    if (normalized === 'pending') return 0
    if (normalized === 'completed' || normalized === 'complete') return 1
  }
  return undefined
}

/**
 * Registers order tools. Registered globally from App.vue since orders (like
 * the order list itself) are relevant across the whole admin app, not one
 * view.
 */
export async function registerOrderTools(signal: AbortSignal): Promise<void> {
  const modelContext = getModelContext()
  if (!modelContext) return

  const orderStore = useOrderStore()

  await modelContext.registerTool(
    {
      name: 'list_orders',
      description:
        'Lists orders, optionally filtered by status ("pending" or "completed"). Omit status to list all orders.',
      inputSchema: {
        type: 'object',
        properties: {
          status: {
            type: 'string',
            enum: ['pending', 'completed'],
            description: 'Optional status filter.',
          },
        },
      },
      execute(args: Record<string, unknown>) {
        const { status } = args
        const filtered =
          status === undefined
            ? orderStore.orders
            : orderStore.orders.filter((o) => o.status === parseStatus(status))
        return textResult(JSON.stringify(filtered.map(summarizeOrder)))
      },
    },
    { signal },
  )

  await modelContext.registerTool(
    {
      name: 'get_order',
      description: 'Returns full details (items, quantities, prices) for one order ID.',
      inputSchema: {
        type: 'object',
        properties: {
          orderId: { type: 'string', description: 'The order ID to look up.' },
        },
        required: ['orderId'],
      },
      execute(args: Record<string, unknown>) {
        const { orderId } = args
        const order = orderStore.orders.find((o) => String(o.orderId) === String(orderId))
        if (!order) {
          return textResult(
            `No order found with ID "${String(orderId)}". Use list_orders to find a valid order ID.`,
            true,
          )
        }
        return textResult(JSON.stringify(order))
      },
    },
    { signal },
  )

  await modelContext.registerTool(
    {
      name: 'update_order_status',
      description:
        'Updates an order\'s status. Setting status to "completed" is the same action as the "Complete Order" button.',
      inputSchema: {
        type: 'object',
        properties: {
          orderId: { type: 'string', description: 'The order ID to update.' },
          status: {
            type: 'string',
            enum: ['pending', 'completed'],
            description: 'The new status for the order.',
          },
        },
        required: ['orderId', 'status'],
      },
      execute(args: Record<string, unknown>) {
        const { orderId, status } = args
        const parsedStatus = parseStatus(status)
        if (parsedStatus === undefined) {
          return textResult('status must be "pending" or "completed".', true)
        }
        return orderStore
          .updateOrderStatus(orderId as string | number, parsedStatus)
          .then(() => textResult(`Order "${String(orderId)}" status updated to ${status}.`))
          .catch((error: Error) => textResult(error.message, true))
      },
    },
    { signal },
  )
}

const PRODUCT_INPUT_SCHEMA_PROPERTIES = {
  name: { type: 'string', description: 'Product name.' },
  price: { type: 'number', description: 'Product price (must be greater than 0).' },
  description: { type: 'string', description: 'Product description.' },
  tags: { type: 'string', description: 'Comma-separated keywords for the product.' },
  image: { type: 'string', description: 'Optional product image URL.' },
} as const

function validateProductFields(args: Record<string, unknown>): string | undefined {
  if (typeof args.name !== 'string' || args.name.length === 0) {
    return 'name is required.'
  }
  if (typeof args.price !== 'number' || args.price <= 0) {
    return 'price must be a number greater than 0.'
  }
  if (typeof args.description !== 'string' || args.description.length === 0) {
    return 'description is required.'
  }
  return undefined
}

/**
 * Registers the create/update product tools. Scoped to ProductFormView,
 * which is the only view with the create/update code path (via
 * useProductActions), mirroring the "Save Product" button.
 */
export async function registerProductFormTools(signal: AbortSignal): Promise<void> {
  const modelContext = getModelContext()
  if (!modelContext) return

  const { createProduct, updateProduct } = useProductActions()

  await modelContext.registerTool(
    {
      name: 'create_product',
      description: 'Creates a new product (same action as the "Save Product" button on the Add Product page).',
      inputSchema: {
        type: 'object',
        properties: PRODUCT_INPUT_SCHEMA_PROPERTIES,
        required: ['name', 'price', 'description'],
      },
      execute(args: Record<string, unknown>) {
        const validationError = validateProductFields(args)
        if (validationError) return textResult(validationError, true)

        const product: Product = {
          id: 0,
          name: args.name as string,
          price: args.price as number,
          description: args.description as string,
          tags: (args.tags as string) ?? '',
          image: (args.image as string) ?? '/placeholder.png',
        }
        return createProduct(product)
          .then((saved) => textResult(`Created product "${saved.name}" with ID ${saved.id}.`))
          .catch((error: Error) => textResult(error.message, true))
      },
    },
    { signal },
  )

  await modelContext.registerTool(
    {
      name: 'update_product',
      description: 'Updates an existing product (same action as the "Save Product" button on the Edit Product page).',
      inputSchema: {
        type: 'object',
        properties: {
          productId: { type: 'string', description: 'The ID of the product to update.' },
          ...PRODUCT_INPUT_SCHEMA_PROPERTIES,
        },
        required: ['productId', 'name', 'price', 'description'],
      },
      execute(args: Record<string, unknown>) {
        const validationError = validateProductFields(args)
        if (validationError) return textResult(validationError, true)

        const { productId } = args
        const product: Product = {
          id: productId as string,
          name: args.name as string,
          price: args.price as number,
          description: args.description as string,
          tags: (args.tags as string) ?? '',
          image: (args.image as string) ?? '/placeholder.png',
        }
        return updateProduct(product)
          .then((saved) => textResult(`Updated product "${saved.name}" (ID ${saved.id}).`))
          .catch((error: Error) => textResult(error.message, true))
      },
    },
    { signal },
  )
}

/**
 * Registers the destructive delete_product tool. Kept separate from the
 * create/update tools and scoped to ProductListView (the closest equivalent
 * of a product management surface), since delete has no undo and the spec's
 * best practices call for treating destructive tools as higher-risk.
 */
export async function registerProductDeleteTool(signal: AbortSignal): Promise<void> {
  const modelContext = getModelContext()
  if (!modelContext) return

  const productStore = useProductStore()
  const { deleteProduct } = useProductActions()

  await modelContext.registerTool(
    {
      name: 'delete_product',
      description:
        'Permanently deletes a product. Destructive and irreversible — confirm the product ID and intent before calling.',
      inputSchema: {
        type: 'object',
        properties: {
          productId: { type: 'string', description: 'The ID of the product to delete.' },
        },
        required: ['productId'],
      },
      execute(args: Record<string, unknown>) {
        const { productId } = args
        const existing = productStore.products.find((p) => String(p.id) === String(productId))
        if (!existing) {
          return textResult(`No product found with ID "${String(productId)}".`, true)
        }
        return deleteProduct(productId as string | number)
          .then(() => textResult(`Deleted product "${existing.name}" (ID ${String(productId)}).`))
          .catch((error: Error) => textResult(error.message, true))
      },
    },
    { signal },
  )
}
