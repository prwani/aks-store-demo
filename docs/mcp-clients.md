# Using the AKS Store Demo MCP servers with AI assistants

This guide walks through connecting the two [MCP servers](../mcp-servers/README.md)
of the AKS Store Demo to ChatGPT, Claude Desktop and Microsoft 365 Copilot.

- **Store Front MCP** — browse products, manage a cart, submit orders
- **Store Admin MCP** — manage products, view and process orders, AI helpers

Both servers speak the **Model Context Protocol over Streamable HTTP** and are
protected with **HTTP Basic authentication**.

## Before you start

You need three things for every client below:

1. **The server URL**, ending in `/mcp`, for example:
   - `https://<store-front-endpoint>.azurefd.net/mcp`
   - `https://<store-admin-endpoint>.azurefd.net/mcp`
2. **The Basic auth credentials** (`MCP_AUTH_USERNAME` / `MCP_AUTH_PASSWORD`
   from the deployment, or the `mcp-auth` Kubernetes secret).
3. **A publicly reachable HTTPS endpoint with a trusted certificate**. ChatGPT
   and Microsoft 365 Copilot call the server from the cloud, so `localhost` and
   self-signed certificates do not work for them. See the
   [deployment notes](../mcp-servers/README.md#deployment) for the Azure Front
   Door setup that provides a Microsoft-managed certificate.

Prefer sending credentials as an `Authorization: Basic ...` request header over
embedding them in the URL. None of the clients covered in this guide document
support for URL-embedded credentials (`https://<user>:<password>@host/mcp`),
and putting the password there risks it leaking into logs, proxies, or link
previews.

### Verify the endpoint first

Confirm the server answers with your credentials before configuring a client:

```bash
curl -i -u "$MCP_AUTH_USERNAME:$MCP_AUTH_PASSWORD" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' \
  https://<your-endpoint>/mcp
```

You should get `HTTP/1.1 200 OK` and a list of tools. Without `-u` you get
`401 Unauthorized` and a `WWW-Authenticate: Basic` header — that confirms
authentication is active.

Generate the header value yourself when a client asks for a raw header:

```bash
# macOS/Linux
printf '%s:%s' "$MCP_AUTH_USERNAME" "$MCP_AUTH_PASSWORD" | base64
```

Use the output as `Authorization: Basic <output>`.

---

## ChatGPT

ChatGPT supports remote MCP servers through **connectors** (Developer mode /
custom connectors, available on ChatGPT Plus, Pro, Business, Enterprise and Edu
plans; availability varies by plan and region).

1. Deploy the MCP server so it is reachable on a public HTTPS URL.
2. In ChatGPT, open **Settings** → **Connectors** (Business/Enterprise admins do
   this under **Settings** → **Connectors** for the workspace).
3. Enable **Developer mode** if custom connectors are not visible
   (**Settings** → **Connectors** → **Advanced** → **Developer mode**).
4. Choose **Create**/**Add custom connector** and fill in:
   - **Name**: `AKS Store Front` (or `AKS Store Admin`)
   - **Description**: e.g. *Browse products and place orders in the Contoso Pet Store*
   - **MCP server URL**: `https://<store-front-endpoint>.azurefd.net/mcp`
   - **Authentication**: choose **Custom headers** (or *API key / header* depending
     on the ChatGPT build) and add
     `Authorization: Basic <base64 of username:password>`.
     If only OAuth and "no authentication" are offered, your ChatGPT build does
     not yet support custom headers for this connector type; use the `curl`
     check above to confirm the server itself is reachable and reauthenticate
     with a build/plan that exposes the custom-header option instead of
     putting credentials in the URL, which ChatGPT does not support.
5. Confirm the trust prompt and create the connector. ChatGPT immediately calls
   `tools/list`; a failure here almost always means the URL is wrong, the
   certificate is not trusted, or the credentials are missing.
6. Start a new chat, open the **＋**/tools menu, and enable the connector for the
   conversation (in Developer mode it appears under **Developer mode** tools).
7. Try a prompt such as *"List the pet store products and add two of the cheapest
   to my cart"*.

> Note: ChatGPT applies extra confirmation prompts for tools that write data
> (create/update/delete product, submit order). Approve them when prompted.

---

## Claude Desktop

Claude's remote-connector authentication only supports OAuth 2.0 or a
static credential sent in a request header (a Claude Desktop beta feature with
limited availability) — there is no option to authenticate with credentials
embedded in the connector URL, and Claude does not support HTTP Basic auth
directly. The reliable way to reach a Basic-auth-protected server such as this
one is the **config file with `mcp-remote`** below, which runs locally and adds
the `Authorization: Basic ...` header itself.

### Configure `claude_desktop_config.json`

1. Open **Settings** → **Developer** → **Edit Config**, which opens
   `claude_desktop_config.json`:
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
2. Add both servers using the `mcp-remote` bridge (requires
   [Node.js](https://nodejs.org)); it turns a remote Streamable HTTP server into
   the stdio transport Claude Desktop launches locally:

```json
{
  "mcpServers": {
    "aks-store-front": {
      "command": "npx",
      "args": [
        "-y",
        "mcp-remote",
        "https://<store-front-endpoint>.azurefd.net/mcp",
        "--header",
        "Authorization: Basic ${STORE_MCP_AUTH}"
      ],
      "env": {
        "STORE_MCP_AUTH": "<base64 of username:password>"
      }
    },
    "aks-store-admin": {
      "command": "npx",
      "args": [
        "-y",
        "mcp-remote",
        "https://<store-admin-endpoint>.azurefd.net/mcp",
        "--header",
        "Authorization: Basic ${STORE_MCP_AUTH}"
      ],
      "env": {
        "STORE_MCP_AUTH": "<base64 of username:password>"
      }
    }
  }
}
```

3. Save the file and **restart Claude Desktop completely** (quit, don't just
   close the window).
4. Open the tools (🔌/hammer) icon in the chat box — the store tools should be
   listed. Ask *"What pet products are available?"* to test.

Troubleshooting: check the Claude logs at
`~/Library/Logs/Claude/mcp*.log` (macOS) or `%APPDATA%\Claude\logs\` (Windows).
A `401` there means the `Authorization` header did not reach the server; a
connection error usually means the URL or certificate is wrong.

---

## Microsoft 365 Copilot

M365 Copilot consumes MCP servers as **agents built in Copilot Studio**. The
server must be reachable from the Microsoft cloud over HTTPS with a publicly
trusted certificate.

1. Go to [Copilot Studio](https://copilotstudio.microsoft.com) and select the
   environment you want to publish the agent in.
2. Open **Tools** (or **Agents** → your agent → **Tools**) and choose
   **Add a tool** → **New tool** → **Model Context Protocol**.
3. Provide the server details:
   - **Server name**: `AKS Store Front MCP`
   - **Server description**: *Contoso Pet Store shopping tools*
   - **Server URL**: `https://<store-front-endpoint>.azurefd.net/mcp`
   - **Authentication**: select **API key** / **Basic**. When only a generic key
     is offered, use the header name `Authorization` and the value
     `Basic <base64 of username:password>`.
4. Create the tool. Copilot Studio creates a custom connector, then calls the
   server to enumerate the tools — they appear in the connector details when the
   connection succeeds.
5. Create (or open) an agent, choose **Add tool**, pick the MCP tool you just
   created, and select the connection.
6. Test the agent in the **Test** pane, e.g. *"Show me the pending orders"* for
   the admin server.
7. **Publish** the agent, then in the **Channels** tab enable **Microsoft 365
   Copilot** (and Teams, if wanted). An admin must approve the agent in the
   [Microsoft 365 admin center](https://admin.microsoft.com) → **Settings** →
   **Integrated apps** before users see it.
8. In Microsoft 365 Copilot, open the **Agents** side panel, add the published
   agent, and chat with it.

> Tip: only expose the store-admin server to trusted users — its tools can
> create, update and delete products and change order status.

---

## Tool reference

Full tool lists are in [mcp-servers/README.md](../mcp-servers/README.md):

| Server | Example tools |
| --- | --- |
| Store Front | `get_products`, `get_product_by_id`, `add_to_cart`, `view_cart`, `update_cart_quantity`, `remove_from_cart`, `clear_cart`, `submit_order` |
| Store Admin | `get_all_products`, `create_product`, `update_product`, `delete_product`, `get_all_orders`, `get_order`, `update_order_status`, `process_order`, `get_order_statistics`, `generate_product_description`, `check_ai_service_health` |

## Common problems

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `401 Unauthorized` | Missing or wrong Basic credentials | Re-check `MCP_AUTH_USERNAME`/`MCP_AUTH_PASSWORD` and the base64 encoding (no newline) |
| Client cannot connect at all | URL missing `/mcp`, server not public, or untrusted certificate | Test with `curl` from outside your network; use the Azure Front Door HTTPS endpoint |
| Tools list is empty | Client connected to the wrong server or the pod is not ready | `kubectl get pods -n pets` and check the server logs |
| Tool call returns `{"error": "Failed to fetch ..."}` | Backend service (product/order/makeline/ai) is unreachable | Verify the `*_SERVICE_URL` environment variables and that the backends are running |
