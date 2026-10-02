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
- AI features require the ai-service and a configured OpenAI-compatible model;
  Azure OpenAI authentication uses the AKS workload identity when enabled
- All monetary values are handled as floats and formatted with appropriate currency symbols

## Deployment

### Fresh AKS deployment order

For a fresh environment, first run `azd up` from the repository root to
provision the AKS infrastructure and deploy the main store application. Make
sure the `pw-dev` azd environment is selected and its required settings
(including `AUTH_USERNAME` and `AUTH_PASSWORD`) are configured. To provision
Azure OpenAI (the model resource used by this app) and enable both text and
image generation, configure the environment before `azd up`:

```bash
azd env set DEPLOY_AZURE_CONTAINER_REGISTRY true
azd env set DEPLOY_AZURE_SERVICE_BUS true
azd env set DEPLOY_AZURE_COSMOSDB true
azd env set DEPLOY_AZURE_OPENAI true
azd env set AZURE_OPENAI_LOCATION swedencentral
azd env set DEPLOY_IMAGE_GENERATION_MODEL true
azd env set BUILD_CONTAINERS true
azd env set AUTH_USERNAME admin
azd env set AUTH_PASSWORD '<choose-a-strong-password>'
azd up
```

The Terraform defaults deploy `gpt-5.4-mini` for product descriptions and
`gpt-image-2` when image generation is enabled. Azure OpenAI is provisioned
with local key authentication disabled and the AI service uses AKS workload
identity. `BUILD_CONTAINERS=true` builds the app images from this checkout into
the created ACR; without it, azd imports the upstream demo images instead.

`azd up` does not deploy the MCP servers or configure ingress-nginx/Azure Front
Door. After it completes, build the MCP server images into the same ACR using
the commands below, then run the one-shot public access script. It builds the MCP images in ACR
and expects the `pets` namespace and main app Services to already exist. The
azd predeploy hooks explicitly set the portal Services to `ClusterIP`, so
those services use the ingress/Front Door path rather than getting separate
public load balancers.

The public-access script builds the MCP server images from
`Dockerfile.store-front` / `Dockerfile.store-admin` remotely with `az acr build`
(no local Docker required), and resolves the ACR created by `azd up`. The
Kubernetes manifests use an `__ACR_NAME__` placeholder that the script replaces
with that registry's name.

Kubernetes manifests to run both servers in the same `pets` namespace as the rest
of the app, wired to the in-cluster backend services, are under
[`mcp-servers/k8s`](./k8s):

- `store-front-mcp.yaml` / `store-admin-mcp.yaml` — Deployment + ClusterIP Service
- `ingress.yaml` — ingress-nginx `Ingress` resources exposing each server at
  `http://<server>.<ingress-ip>.nip.io/mcp` (plain HTTP; public HTTPS is
  terminated at Azure Front Door, see below, so no in-cluster TLS cert is
  needed)

> The `store-front` / `store-admin` app Services (from the main Helm chart)
> are also `ClusterIP` (not `LoadBalancer`): public access to the portals goes
> through this same ingress-nginx + Front Door path, so no separate public IP
> is needed for them.

### One-shot setup script

[`deploy-public-access.ps1`](./deploy-public-access.ps1) /
[`deploy-public-access.sh`](./deploy-public-access.sh) automate everything
below against a freshly provisioned (or existing) AKS cluster: discovering the
ACR, building both MCP images, installing ingress-nginx, creating the
`mcp-auth` secret, applying the `k8s/` manifests, and provisioning the Azure
Front Door profile/endpoints. It's plain
`az`/`kubectl`/`helm` CLI — intentionally not Terraform/Bicep, so it can be
re-run freely without touching [`infra/terraform`](../infra/terraform) or
risking merge conflicts with upstream. Safe to re-run; every step is
idempotent.

```powershell
./deploy-public-access.ps1 -ResourceGroup <rg> -ClusterName <aks-cluster> `
  -McpAuthUsername <user> -McpAuthPassword <password>
```

```bash
./deploy-public-access.sh -g <rg> -c <aks-cluster> -u <user> -p <password>
```

This creates/updates:
- The ingress-nginx controller (`ingress-nginx` namespace), discovering its
  public LoadBalancer IP dynamically (it changes on every fresh cluster, so
  nothing is hardcoded).
- The two MCP images in the ACR found in the AKS resource group; image
  references are populated dynamically when the manifests are applied.
- The `mcp-auth` secret in the `pets` namespace, from the credentials you pass in.
- The `store-front-mcp` / `store-admin-mcp` Deployments+Services and the
  `store-front-mcp` / `store-admin-mcp` / `store-front` Ingress resources
  (`k8s/ingress.yaml`, with its `__INGRESS_IP__` placeholder substituted at
  apply-time with the discovered ingress IP — see [Manual steps](#manual-steps)
  below if you'd rather run this by hand).
- An Azure Front Door Standard profile (default name `fd-aks-store-mcp`) with
  3 endpoints/routes/origin-groups pointed at the ingress-nginx IP.

#### Manual steps

If you'd rather do this by hand instead of running the script:

```bash
kubectl create secret generic mcp-auth --namespace pets \
  --from-literal=username='<your-username>' \
  --from-literal=password='<your-password>'

kubectl apply -f mcp-servers/k8s/store-front-mcp.yaml -f mcp-servers/k8s/store-admin-mcp.yaml

# ingress.yaml uses the __INGRESS_IP__ placeholder in its hostnames; substitute
# your ingress-nginx controller's public IP before applying, e.g.:
sed 's/__INGRESS_IP__/<ingress-controller-ip>/g' mcp-servers/k8s/ingress.yaml | kubectl apply -f -
```

### Public HTTPS endpoint (Azure Front Door)

For a publicly trusted TLS certificate (needed for registering these servers as
tools in Copilot Studio / M365 Copilot), an Azure Front Door Standard profile sits
in front of the ingress-nginx controller's public IP and terminates TLS with a
Microsoft-managed certificate on the default `*.azurefd.net` hostname — no
custom domain or third-party CA (e.g. Let's Encrypt) is involved:

- `https://<store-front-mcp-endpoint>.azurefd.net/mcp`
- `https://<store-admin-mcp-endpoint>.azurefd.net/mcp`

The same Front Door profile also fronts the `store-front` web portal itself
(origin: the `store-front` ingress host defined in
[`ingress.yaml`](./k8s/ingress.yaml)), so customers get a publicly trusted
HTTPS URL for the app too, not just the MCP tools:

- `https://<store-front-endpoint>.azurefd.net/login?redirect=/`

Front Door forwards to the ingress-nginx origin over plain HTTP (`ssl-redirect`
disabled on the ingress), so TLS is only terminated once, at the Front Door edge.

> All three Front Door endpoints (profile `fd-aks-store-mcp`) are provisioned
> by `deploy-public-access.ps1`/`.sh` via `az afd ...` CLI commands; they are
> intentionally not defined in this repo's Terraform/Bicep IaC (see script
> header comments for why).

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