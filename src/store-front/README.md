# store-front

This is a Vue.js app that simulates a store front. It is meant to be used in conjunction with the [product-service](../product-service/) and [order-service](../order-service). The app is extremely simple in that it only has a cart and a order submission button. When the order submission button is clicked, the cart is emptied and the order is sent to the order service. Currently there is no order checkout pages to collect any customer information.

## Running the app locally

### Prerequisites

- [Node.js](https://nodejs.org/en/download/)
- [Vue CLI Service](https://cli.vuejs.org/guide/cli-service.html)
- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

### Running the app

The app relies on the [product-service](../product-service) and the [order-service](../order-service) and the rabbitmq instance running. A docker-compose file is provided to make this easy.

To run the necessary services, clone the repo, open a terminal, and navigate to the `store-front` directory. Then run the following command:

```bash
docker compose up
```

With the services running, open a new terminal and navigate to the `store-front` directory. Then run the following commands:

```bash
export VITE_PRODUCT_SERVICE_URL=http://localhost:3002/
export VITE_ORDER_SERVICE_URL=http://localhost:3000/

npm install
npm run dev
```

When the app is running, you should see output similar to the following:

```text
  App running at:
  - Local:   http://localhost:8080/
  - Network: http://192.168.0.144:8080/

  Note that the development build is not optimized.
  To create a production build, run npm run build.
```

Open a browser and navigate to `http://localhost:8080/`. You should see the store front app running.

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
| `AUTH_REALM` | `Contoso Pet Store` | Realm name used in the auth challenge |
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
can act on the store using the same store actions the UI buttons use.
Registration is feature-detected and a no-op in browsers without WebMCP
support (native support currently requires Chrome/Edge with the WebMCP Origin
Trial or the local `#enable-webmcp-testing` flag). See `src/webmcp/tools.ts`.

| Tool | Description |
| --- | --- |
| `search_products` | Searches (or lists, if no query) the product catalog. |
| `get_product_details` | Returns full details for one product ID. |
| `get_cart` | Returns the current cart contents and total. |
| `add_to_cart` | Adds a quantity of a product to the cart. |
| `update_cart_item` | Changes the quantity of a product already in the cart. |
| `remove_from_cart` | Removes a product from the cart. |
| `checkout` | Submits the cart as an order and clears it (same as the "Proceed to Checkout" button). |
