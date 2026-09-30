# store-admin

This is a Vue.js app that simulates a store admin portal where users can manually process orders, and manage products. It is meant to be used in conjunction with the [product-service](../product-service/) and [makeline-service](../makeline-service). If you have access to OpenAI or Azure OpenAI API keys, you can also deploy the [ai-service](../ai-service) to help you generate product descriptions. You should also run the [virtual-customer](../virtual-customer) to simulate customers placing orders to have some order data to work with.

## Running the app locally

### Prerequisites

- [Node.js](https://nodejs.org/en/download/)
- [Vue CLI Service](https://cli.vuejs.org/guide/cli-service.html)
- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)
- [OpenAI API Key](https://beta.openai.com/docs/developer-quickstart/your-api-keys)
- [Azure OpenAI API Key](https://azure.microsoft.com/products/cognitive-services/openai-service/)

### Running the app

The app relies on the [product-service](../product-service), [makeline-service](../order-service), and optionally the [ai-service](../ai-service) along with mongodb and rabbitmq instances running. A docker-compose file is provided to make this easy.

To run the necessary services, clone the repo, open a terminal, and navigate to the `store-admin` directory.

If you have access to OpenAI or Azure OpenAI, open the `docker-compose.yml` file, uncomment the `ai-services` block, and add your OpenAI or Azure OpenAI credentials.

> IMPORTANT: When filling in the values, do not put the value in double-quotes.

```yaml
environment:
  - USE_AZURE_OPENAI=True # set to False if you are not using Azure OpenAI
  - AZURE_OPENAI_DEPLOYMENT_NAME= # required if using Azure OpenAI
  - AZURE_OPENAI_ENDPOINT= # required if using Azure OpenAI
  - OPENAI_API_KEY= # always required
  - OPENAI_ORG_ID= # required if using OpenAI
```

Then run the following command:

```bash
docker compose up
```

With the services running, open a new terminal and navigate to the `store-admin` directory. Then run the following commands:

```bash
export VITE_PRODUCT_SERVICE_URL=http://localhost:3002/
export VITE_MAKELINE_SERVICE_URL=http://localhost:3001/

npm install
npm run dev
```

When the app is running, you should see output similar to the following:

```text
  App running at:
  - Local:   http://localhost:8081/
  - Network: http://192.168.0.144:8081/

  Note that the development build is not optimized.
  To create a production build, run npm run build.
```

Open a browser and navigate to `http://localhost:8081/`. You should see the store admin app running.

## Authentication

The app is protected with HTTP Basic authentication. The SPA shows a **login
page** at `/login`; the credentials entered there are validated against the
`/api/auth/login` endpoint and then sent as an `Authorization: Basic ...` header
on every API call. nginx enforces the credentials server-side on all `/api/*`
locations, so the API cannot be called without them. The "Sign out" button in
the navigation bar clears the credentials (they are only kept for the browser
session).

The container reads the credentials from environment variables at start-up:

| Variable | Default | Description |
| --- | --- | --- |
| `AUTH_USERNAME` | _(none)_ | Username accepted by the portal (required) |
| `AUTH_PASSWORD` | _(none)_ | Password accepted by the portal (required) |
| `AUTH_REALM` | `Contoso Pet Store Admin` | Realm name used in the auth challenge |
| `AUTH_ENABLED` | `true` | Set to `false` to disable authentication (local development only) |

The container fails to start when authentication is enabled and the credentials
are missing. In Kubernetes the values come from the `store-auth` secret:

```bash
kubectl create secret generic store-auth -n pets \
  --from-literal=username='<your-username>' \
  --from-literal=password='<your-password>'
```

When running `npm run dev`, the Vite dev server validates the login form against
`AUTH_USERNAME`/`AUTH_PASSWORD` if they are set, and accepts any credentials
otherwise.

> Basic credentials are sent on every request, so always serve the portal over
> HTTPS outside of local development.

## WebMCP tools

This app registers [WebMCP](https://github.com/webmachinelearning/webmcp)
tools (`document.modelContext.registerTool`) so a browser-integrated AI agent
can act on the admin portal using the same store actions/API calls the UI
buttons use. Registration is feature-detected and a no-op in browsers
without WebMCP support (native support currently requires Chrome/Edge with
the WebMCP Origin Trial or the local `#enable-webmcp-testing` flag). See
`src/webmcp/tools.ts`.

| Tool | Description |
| --- | --- |
| `list_orders` | Lists orders, optionally filtered by status. |
| `get_order` | Returns full item/price details for one order. |
| `update_order_status` | Updates an order's status (same as the "Complete Order" button). |
| `create_product` | Creates a new product (same as "Save Product" on the Add Product page). |
| `update_product` | Updates an existing product (same as "Save Product" on the Edit Product page). |
| `delete_product` | Permanently deletes a product. Destructive/irreversible — treated as higher-risk. |

> **Note:** this app currently has no authentication/authorization guard on
> any UI action (there is no auth code anywhere in store-admin). The
> `create_product`/`update_product`/`delete_product` tools intentionally
> mirror that existing (unguarded) behavior rather than introducing new
> gating that the UI itself doesn't have.
