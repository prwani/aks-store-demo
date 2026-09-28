// Ambient types for the WebMCP proposal (https://github.com/webmachinelearning/webmcp).
// The API is not yet part of TypeScript's DOM lib, so we declare the minimal
// surface this app uses. Kept intentionally small / permissive since the
// spec is still experimental and evolving.

export {}

// This file has a top-level `export {}` (making it a module), so the ambient
// declarations below must be wrapped in `declare global` to merge into the
// global `Document`/`Navigator` types instead of being module-scoped.
declare global {
  interface ModelContextToolResultContent {
    type: 'text'
    text: string
  }

  interface ModelContextToolResult {
    content: ModelContextToolResultContent[]
    isError?: boolean
  }

  interface ModelContextTool {
    name: string
    description: string
    inputSchema?: Record<string, unknown>
    execute: (
      args: Record<string, unknown>,
      options?: { signal?: AbortSignal },
    ) => ModelContextToolResult | Promise<ModelContextToolResult>
  }

  interface ModelContextRegisterOptions {
    signal?: AbortSignal
  }

  interface ModelContext {
    registerTool: (tool: ModelContextTool, options?: ModelContextRegisterOptions) => Promise<void>
  }

  interface Document {
    modelContext?: ModelContext
  }

  interface Navigator {
    modelContext?: ModelContext
  }
}
