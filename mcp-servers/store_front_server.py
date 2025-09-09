#!/usr/bin/env python3
"""
MCP Server for AKS Store Demo - Store Front

This server provides MCP tools for the store front functionality including:
- Browse products
- Manage shopping cart  
- Submit orders
"""

import os
import json
import httpx
from typing import List, Dict, Any, Optional
from mcp.server import FastMCP

# Initialize the FastMCP server
mcp = FastMCP("Store Front")

# Configuration
PRODUCT_SERVICE_URL = os.getenv("PRODUCT_SERVICE_URL", "http://localhost:3002")
ORDER_SERVICE_URL = os.getenv("ORDER_SERVICE_URL", "http://localhost:3000")

# In-memory cart storage (in a real implementation, this might use a database)
cart_items: List[Dict[str, Any]] = []


@mcp.tool()
async def get_products() -> List[Dict[str, Any]]:
    """
    Fetch all available products from the product service.
    
    Returns:
        List of products with their details (id, name, price, description, etc.)
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{PRODUCT_SERVICE_URL}/products")
            response.raise_for_status()
            products = response.json()
            return products
    except httpx.RequestError as e:
        return {"error": f"Failed to fetch products: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


@mcp.tool()
async def get_product_by_id(product_id: str) -> Dict[str, Any]:
    """
    Get details of a specific product by its ID.
    
    Args:
        product_id: The unique identifier of the product
        
    Returns:
        Product details including id, name, price, description, image, etc.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{PRODUCT_SERVICE_URL}/product/{product_id}")
            response.raise_for_status()
            product = response.json()
            return product
    except httpx.RequestError as e:
        return {"error": f"Failed to fetch product {product_id}: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


@mcp.tool()
async def add_to_cart(product_id: str, quantity: int = 1) -> Dict[str, Any]:
    """
    Add a product to the shopping cart.
    
    Args:
        product_id: The unique identifier of the product to add
        quantity: Number of items to add (default: 1)
        
    Returns:
        Updated cart information and confirmation message
    """
    try:
        # First, get product details
        product_data = await get_product_by_id(product_id)
        if "error" in product_data:
            return product_data
            
        # Check if product already exists in cart
        for item in cart_items:
            if item["product"]["id"] == product_id:
                item["quantity"] += quantity
                return {
                    "message": f"Updated quantity of {product_data['name']} in cart",
                    "cart": cart_items,
                    "cart_total": sum(item["product"]["price"] * item["quantity"] for item in cart_items)
                }
        
        # Add new item to cart
        cart_item = {
            "product": product_data,
            "quantity": quantity
        }
        cart_items.append(cart_item)
        
        return {
            "message": f"Added {quantity} x {product_data['name']} to cart",
            "cart": cart_items,
            "cart_total": sum(item["product"]["price"] * item["quantity"] for item in cart_items)
        }
    except Exception as e:
        return {"error": f"Failed to add product to cart: {str(e)}"}


@mcp.tool()
async def view_cart() -> Dict[str, Any]:
    """
    View current shopping cart contents and total.
    
    Returns:
        Cart items, quantities, individual totals, and grand total
    """
    try:
        cart_total = sum(item["product"]["price"] * item["quantity"] for item in cart_items)
        cart_count = sum(item["quantity"] for item in cart_items)
        
        return {
            "items": cart_items,
            "cart_count": cart_count,
            "cart_total": cart_total,
            "formatted_total": f"${cart_total:.2f}"
        }
    except Exception as e:
        return {"error": f"Failed to retrieve cart: {str(e)}"}


@mcp.tool()
async def remove_from_cart(product_id: str) -> Dict[str, Any]:
    """
    Remove a product from the shopping cart.
    
    Args:
        product_id: The unique identifier of the product to remove
        
    Returns:
        Updated cart information and confirmation message
    """
    try:
        global cart_items
        initial_count = len(cart_items)
        cart_items = [item for item in cart_items if item["product"]["id"] != product_id]
        
        if len(cart_items) < initial_count:
            cart_total = sum(item["product"]["price"] * item["quantity"] for item in cart_items)
            return {
                "message": f"Removed product {product_id} from cart",
                "cart": cart_items,
                "cart_total": cart_total
            }
        else:
            return {"error": f"Product {product_id} not found in cart"}
    except Exception as e:
        return {"error": f"Failed to remove product from cart: {str(e)}"}


@mcp.tool()
async def update_cart_quantity(product_id: str, quantity: int) -> Dict[str, Any]:
    """
    Update the quantity of a specific product in the cart.
    
    Args:
        product_id: The unique identifier of the product
        quantity: New quantity (must be positive)
        
    Returns:
        Updated cart information and confirmation message
    """
    try:
        if quantity <= 0:
            return {"error": "Quantity must be positive"}
            
        for item in cart_items:
            if item["product"]["id"] == product_id:
                item["quantity"] = quantity
                cart_total = sum(item["product"]["price"] * item["quantity"] for item in cart_items)
                return {
                    "message": f"Updated quantity of {item['product']['name']} to {quantity}",
                    "cart": cart_items,
                    "cart_total": cart_total
                }
        
        return {"error": f"Product {product_id} not found in cart"}
    except Exception as e:
        return {"error": f"Failed to update cart quantity: {str(e)}"}


@mcp.tool()
async def clear_cart() -> Dict[str, Any]:
    """
    Clear all items from the shopping cart.
    
    Returns:
        Confirmation message
    """
    try:
        global cart_items
        items_count = len(cart_items)
        cart_items = []
        return {
            "message": f"Cleared {items_count} items from cart",
            "cart": cart_items,
            "cart_total": 0
        }
    except Exception as e:
        return {"error": f"Failed to clear cart: {str(e)}"}


@mcp.tool()
async def submit_order(customer_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Submit the current cart as an order.
    
    Args:
        customer_id: Optional customer identifier (will generate random if not provided)
        
    Returns:
        Order confirmation with order details
    """
    try:
        if not cart_items:
            return {"error": "Cart is empty. Add items before submitting order."}
        
        # Generate customer ID if not provided
        if not customer_id:
            import random
            customer_id = str(random.randint(1000000000, 9999999999))
        
        # Prepare order data
        order_data = {
            "customerId": customer_id,
            "items": [
                {
                    "productId": item["product"]["id"],
                    "quantity": item["quantity"],
                    "price": item["product"]["price"]
                }
                for item in cart_items
            ]
        }
        
        # Submit order to order service
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{ORDER_SERVICE_URL}/orders",
                json=order_data,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
        
        # Calculate order total
        order_total = sum(item["product"]["price"] * item["quantity"] for item in cart_items)
        submitted_items = cart_items.copy()
        
        # Clear cart after successful order
        cart_items.clear()
        
        return {
            "message": "Order submitted successfully",
            "order": {
                "customer_id": customer_id,
                "items": submitted_items,
                "total": order_total,
                "formatted_total": f"${order_total:.2f}"
            }
        }
    except httpx.RequestError as e:
        return {"error": f"Failed to submit order: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error during order submission: {str(e)}"}


if __name__ == "__main__":
    # Run the MCP server
    mcp.run()