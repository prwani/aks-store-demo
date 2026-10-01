# AKS Store Demo MCP Servers

This directory contains Model Context Protocol (MCP) servers for the AKS Store Demo applications. These servers expose the functionality of the store-front and store-admin Vue.js applications as MCP tools that can be used by AI assistants.

## Overview

The MCP servers provide a programmatic interface to interact with the store demo applications:

- **`store_front_server.py`** - Exposes customer-facing store functionality
- **`store_admin_server.py`** - Exposes administrative store management functionality

## Prerequisites

1. Python 3.8 or higher
2. The AKS Store Demo backend services running (product-service, order-service, makeline-service, ai-service)

## Installation

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables (backend URLs are optional and fall back to the defaults below, the authentication credentials are required):
```bash
export PRODUCT_SERVICE_URL=http://localhost:3002
export ORDER_SERVICE_URL=http://localhost:3000
export MAKELINE_SERVICE_URL=http://localhost:3001
export AI_SERVICE_URL=http://localhost:5001

# HTTP Basic authentication credentials (required)
export MCP_AUTH_USERNAME=<your-username>
export MCP_AUTH_PASSWORD=<your-password>
```

## Running the Servers

### Store Front Server

The store front server provides tools for customer interactions:

```bash
python store_front_server.py
```

**Available Tools:**
- `get_products()` - Fetch all available products
- `get_product_by_id(product_id)` - Get details of a specific product (numeric id)
- `add_to_cart(product_id, quantity)` - Add items to shopping cart
- `view_cart()` - View current cart contents and total
- `remove_from_cart(product_id)` - Remove items from cart
- `update_cart_quantity(product_id, quantity)` - Update item quantities
- `clear_cart()` - Empty the shopping cart
- `submit_order(customer_id?)` - Submit cart as an order

### Store Admin Server

The store admin server provides tools for administrative tasks:

```bash
python store_admin_server.py
```

**Available Tools:**

*Product Management:*
- `get_all_products()` - Fetch all products for management
- `get_product(product_id)` - Get specific product details (numeric id)
- `create_product(name, price, description, image?)` - Create new products
- `update_product(product_id, ...)` - Update existing products
- `delete_product(product_id)` - Delete products

*Order Management:*
- `get_all_orders()` - Fetch all orders
- `get_order(order_id)` - Get specific order details
- `update_order_status(order_id, status)` - Update order status (0=Pending, 1=Processing/Completed, 2=Complete)
- `process_order(order_id)` - Mark order as processed (sets status to 1, matching the "Complete Order" button in store-admin)
- `get_order_statistics()` - Get order analytics

*AI Features:*
- `generate_product_description(product_name, tags?)` - AI-generated descriptions
- `check_ai_service_health()` - Check AI service availability

## Transport

Both servers run over **Streamable HTTP** (not stdio), so they can be deployed as
regular network services. Each server binds `0.0.0.0` on the port from the `PORT`
env var (default `8100` for store-front, `8101` for store-admin) and serves the
MCP endpoint at `/mcp`.

## Authentication

Both servers are protected with **HTTP Basic authentication**. Every request to
`/mcp` must include an `Authorization: Basic <base64(username:password)>` header;
requests without valid credentials get `401 Unauthorized` with a
`WWW-Authenticate: Basic` challenge. Health/probe paths (`/health`, `/healthz`,
`/readyz`) stay open so Kubernetes probes keep working.

Credentials come from `MCP_AUTH_USERNAME` / `MCP_AUTH_PASSWORD`. Authentication
is on by default and the server refuses to start when the credentials are
missing. For local development only, it can be turned off with
`MCP_AUTH_ENABLED=false`.

Quick check with curl:

```bash
curl -i -u "$MCP_AUTH_USERNAME:$MCP_AUTH_PASSWORD" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' \
  http://localhost:8100/mcp
```

> Basic authentication sends credentials on every request, so always use it over
> HTTPS (the deployment below terminates TLS at the ingress / Azure Front Door).

## Usage with MCP Clients

These servers can be used with any MCP-compatible client that supports Streamable
HTTP, by pointing the client at `http://<host>:<port>/mcp` (or the HTTPS URL if
deployed behind TLS, see [Deployment](#deployment) below) and supplying the Basic
auth credentials.

Step-by-step instructions for ChatGPT, Claude Desktop and Microsoft 365 Copilot
are in [docs/mcp-clients.md](../docs/mcp-clients.md).

## Example Workflows

### Customer Shopping Flow (Store Front)
1. `get_products()` - Browse available products
2. `add_to_cart(123, 2)` - Add items to cart
3. `view_cart()` - Review cart contents
4. `submit_order()` - Place the order

### Admin Product Management (Store Admin)
1. `get_all_products()` - View current inventory
2. `create_product("New Pet Toy", 19.99, "Fun toy for cats")` - Add new product
3. `generate_product_description("New Pet Toy", ["interactive", "durable"])` - Generate AI description
4. `update_product(123, description="AI generated description")` - Update with AI content

### Order Processing (Store Admin)
1. `get_all_orders()` - View pending orders
2. `get_order("456")` - Check order details
3. `update_order_status("456", 1)` - Update status
4. `process_order("456")` - Complete the order

## Configuration

The servers support the following environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `PRODUCT_SERVICE_URL` | `http://localhost:3002` | Product service endpoint |
| `ORDER_SERVICE_URL` | `http://localhost:3000` | Order service endpoint |
| `MAKELINE_SERVICE_URL` | `http://localhost:3001` | Makeline service endpoint |
| `AI_SERVICE_URL` | `http://localhost:5001` | AI service endpoint |
| `MCP_AUTH_USERNAME` | _(none)_ | Username required for HTTP Basic authentication |
| `MCP_AUTH_PASSWORD` | _(none)_ | Password required for HTTP Basic authentication |
| `MCP_AUTH_ENABLED` | `true` | Set to `false` to disable authentication (local development only) |
| `PORT` | `8100` / `8101` | Port the server listens on |

## Error Handling

All tools return structured responses with error information when requests fail:

```json
{
  "error": "Failed to fetch products: Connection timeout"
}
```

Successful responses include relevant data and confirmation messages.

## Notes

- The store front server maintains an in-memory shopping cart per session
- The servers communicate with the backend microservices via HTTP APIs
- AI features require the ai-service to be running and configured with API keys
- All monetary values are handled as floats and formatted with appropriate currency symbols

## Deployment

Container images are built with `Dockerfile.store-front` / `Dockerfile.store-admin`
and can be built remotely with `az acr build` (no local Docker required):

```bash
az acr build --registry <acr-name> --image aks-store-demo/store-front-mcp:latest \
  --file mcp-servers/Dockerfile.store-front mcp-servers
az acr build --registry <acr-name> --image aks-store-demo/store-admin-mcp:latest \
  --file mcp-servers/Dockerfile.store-admin mcp-servers
```

Kubernetes manifests to run both servers in the same `pets` namespace as the rest
of the app, wired to the in-cluster backend services, are under
[`mcp-servers/k8s`](./k8s):

- `store-front-mcp.yaml` / `store-admin-mcp.yaml` — Deployment + ClusterIP Service
- `ingress.yaml` — ingress-nginx `Ingress` resources exposing each server at
  `http://<server>.<ingress-ip>.nip.io/mcp` (plain HTTP; public HTTPS is
  terminated at Azure Front Door, see below, so no in-cluster TLS cert is
  needed)

Both deployments read their Basic auth credentials from a `mcp-auth` secret in the
`pets` namespace, so create it before applying the manifests:

```bash
kubectl create secret generic mcp-auth --namespace pets \
  --from-literal=username='<your-username>' \
  --from-literal=password='<your-password>'
```

```bash
kubectl apply -f mcp-servers/k8s/store-front-mcp.yaml -f mcp-servers/k8s/store-admin-mcp.yaml
kubectl apply -f mcp-servers/k8s/ingress.yaml
```

### Public HTTPS endpoint (Azure Front Door)

For a publicly trusted TLS certificate (needed for registering these servers as
tools in Copilot Studio / M365 Copilot), an Azure Front Door Standard profile sits
in front of the ingress-nginx controller's public IP and terminates TLS with a
Microsoft-managed certificate on the default `*.azurefd.net` hostname — no
custom domain or third-party CA (e.g. Let's Encrypt) is involved:

- `https://<store-front-endpoint>.azurefd.net/mcp`
- `https://<store-admin-endpoint>.azurefd.net/mcp`

Front Door forwards to the ingress-nginx origin over plain HTTP (`ssl-redirect`
disabled on the ingress), so TLS is only terminated once, at the Front Door edge.

## Architecture

```
AI Assistant/Client
       ↓
   MCP Server (FastMCP)
       ↓
Backend Microservices
   ├── product-service (Rust)
   ├── order-service (Node.js)
   ├── makeline-service (Go)
   └── ai-service (Python/FastAPI)
```