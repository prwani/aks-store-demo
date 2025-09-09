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

2. Set up environment variables (optional, will use defaults if not set):
```bash
export PRODUCT_SERVICE_URL=http://localhost:3002
export ORDER_SERVICE_URL=http://localhost:3000
export MAKELINE_SERVICE_URL=http://localhost:3001
export AI_SERVICE_URL=http://localhost:5001
```

## Running the Servers

### Store Front Server

The store front server provides tools for customer interactions:

```bash
python store_front_server.py
```

**Available Tools:**
- `get_products()` - Fetch all available products
- `get_product_by_id(product_id)` - Get details of a specific product
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
- `get_product(product_id)` - Get specific product details
- `create_product(name, price, description, ...)` - Create new products
- `update_product(product_id, ...)` - Update existing products
- `delete_product(product_id)` - Delete products

*Order Management:*
- `get_all_orders()` - Fetch all orders
- `get_order(order_id)` - Get specific order details
- `update_order_status(order_id, status)` - Update order status
- `process_order(order_id)` - Mark order as completed
- `get_order_statistics()` - Get order analytics

*AI Features:*
- `generate_product_description(product_name, features?)` - AI-generated descriptions
- `check_ai_service_health()` - Check AI service availability

## Usage with MCP Clients

These servers can be used with any MCP-compatible client. For example, with the MCP CLI:

```bash
# Connect to store front server
mcp connect stdio python store_front_server.py

# Connect to store admin server  
mcp connect stdio python store_admin_server.py
```

## Example Workflows

### Customer Shopping Flow (Store Front)
1. `get_products()` - Browse available products
2. `add_to_cart("product-123", 2)` - Add items to cart
3. `view_cart()` - Review cart contents
4. `submit_order()` - Place the order

### Admin Product Management (Store Admin)
1. `get_all_products()` - View current inventory
2. `create_product("New Pet Toy", 19.99, "Fun toy for cats")` - Add new product
3. `generate_product_description("New Pet Toy", ["interactive", "durable"])` - Generate AI description
4. `update_product("product-123", description="AI generated description")` - Update with AI content

### Order Processing (Store Admin)
1. `get_all_orders()` - View pending orders
2. `get_order("order-456")` - Check order details
3. `update_order_status("order-456", "processing")` - Update status
4. `process_order("order-456")` - Complete the order

## Configuration

The servers support the following environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `PRODUCT_SERVICE_URL` | `http://localhost:3002` | Product service endpoint |
| `ORDER_SERVICE_URL` | `http://localhost:3000` | Order service endpoint |
| `MAKELINE_SERVICE_URL` | `http://localhost:3001` | Makeline service endpoint |
| `AI_SERVICE_URL` | `http://localhost:5001` | AI service endpoint |

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