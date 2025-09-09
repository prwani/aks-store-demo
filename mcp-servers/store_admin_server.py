#!/usr/bin/env python3
"""
MCP Server for AKS Store Demo - Store Admin

This server provides MCP tools for the store admin functionality including:
- Manage products (CRUD operations)
- View and manage orders
- Generate product descriptions with AI
"""

import os
import json
import httpx
from typing import List, Dict, Any, Optional
from mcp.server import FastMCP

# Initialize the FastMCP server
mcp = FastMCP("Store Admin")

# Configuration
PRODUCT_SERVICE_URL = os.getenv("PRODUCT_SERVICE_URL", "http://localhost:3002")
ORDER_SERVICE_URL = os.getenv("ORDER_SERVICE_URL", "http://localhost:3000")
MAKELINE_SERVICE_URL = os.getenv("MAKELINE_SERVICE_URL", "http://localhost:3001")
AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://localhost:5001")


@mcp.tool()
async def get_all_products() -> List[Dict[str, Any]]:
    """
    Fetch all products from the product service for admin management.
    
    Returns:
        List of all products with complete details
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
async def get_product(product_id: str) -> Dict[str, Any]:
    """
    Get details of a specific product for admin management.
    
    Args:
        product_id: The unique identifier of the product
        
    Returns:
        Complete product details
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
async def create_product(
    name: str,
    price: float,
    description: str,
    image: str = "",
    category: str = "",
    tags: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Create a new product in the catalog.
    
    Args:
        name: Product name
        price: Product price
        description: Product description
        image: Product image URL (optional)
        category: Product category (optional)
        tags: List of product tags (optional)
        
    Returns:
        Created product details or error message
    """
    try:
        product_data = {
            "name": name,
            "price": price,
            "description": description,
            "image": image or "",
            "category": category or "",
            "tags": tags or []
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{PRODUCT_SERVICE_URL}/product",
                json=product_data,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            created_product = response.json()
            return {
                "message": f"Successfully created product: {name}",
                "product": created_product
            }
    except httpx.RequestError as e:
        return {"error": f"Failed to create product: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


@mcp.tool()
async def update_product(
    product_id: str,
    name: Optional[str] = None,
    price: Optional[float] = None,
    description: Optional[str] = None,
    image: Optional[str] = None,
    category: Optional[str] = None,
    tags: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Update an existing product in the catalog.
    
    Args:
        product_id: The unique identifier of the product to update
        name: New product name (optional)
        price: New product price (optional)
        description: New product description (optional)
        image: New product image URL (optional)
        category: New product category (optional)
        tags: New list of product tags (optional)
        
    Returns:
        Updated product details or error message
    """
    try:
        # First get the existing product
        existing_product = await get_product(product_id)
        if "error" in existing_product:
            return existing_product
        
        # Update only provided fields
        update_data = {}
        if name is not None:
            update_data["name"] = name
        if price is not None:
            update_data["price"] = price
        if description is not None:
            update_data["description"] = description
        if image is not None:
            update_data["image"] = image
        if category is not None:
            update_data["category"] = category
        if tags is not None:
            update_data["tags"] = tags
        
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{PRODUCT_SERVICE_URL}/product/{product_id}",
                json=update_data,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            updated_product = response.json()
            return {
                "message": f"Successfully updated product: {product_id}",
                "product": updated_product
            }
    except httpx.RequestError as e:
        return {"error": f"Failed to update product: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


@mcp.tool()
async def delete_product(product_id: str) -> Dict[str, Any]:
    """
    Delete a product from the catalog.
    
    Args:
        product_id: The unique identifier of the product to delete
        
    Returns:
        Confirmation message or error
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.delete(f"{PRODUCT_SERVICE_URL}/product/{product_id}")
            response.raise_for_status()
            return {
                "message": f"Successfully deleted product: {product_id}"
            }
    except httpx.RequestError as e:
        return {"error": f"Failed to delete product: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


@mcp.tool()
async def get_all_orders() -> List[Dict[str, Any]]:
    """
    Fetch all orders from the makeline service for admin management.
    
    Returns:
        List of all orders with details
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{MAKELINE_SERVICE_URL}/order/fetch")
            response.raise_for_status()
            orders = response.json()
            return orders
    except httpx.RequestError as e:
        return {"error": f"Failed to fetch orders: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


@mcp.tool()
async def get_order(order_id: str) -> Dict[str, Any]:
    """
    Get details of a specific order.
    
    Args:
        order_id: The unique identifier of the order
        
    Returns:
        Complete order details
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{MAKELINE_SERVICE_URL}/order/{order_id}")
            response.raise_for_status()
            order = response.json()
            return order
    except httpx.RequestError as e:
        return {"error": f"Failed to fetch order {order_id}: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


@mcp.tool()
async def update_order_status(order_id: str, status: str) -> Dict[str, Any]:
    """
    Update the status of an order.
    
    Args:
        order_id: The unique identifier of the order
        status: New status (e.g., "pending", "processing", "completed", "cancelled")
        
    Returns:
        Updated order details or error message
    """
    try:
        update_data = {"status": status}
        
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{MAKELINE_SERVICE_URL}/order/{order_id}",
                json=update_data,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            updated_order = response.json()
            return {
                "message": f"Successfully updated order {order_id} status to {status}",
                "order": updated_order
            }
    except httpx.RequestError as e:
        return {"error": f"Failed to update order status: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


@mcp.tool()
async def process_order(order_id: str) -> Dict[str, Any]:
    """
    Process an order (mark as completed).
    
    Args:
        order_id: The unique identifier of the order to process
        
    Returns:
        Processing confirmation or error message
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.put(f"{MAKELINE_SERVICE_URL}/order/{order_id}/process")
            response.raise_for_status()
            processed_order = response.json()
            return {
                "message": f"Successfully processed order: {order_id}",
                "order": processed_order
            }
    except httpx.RequestError as e:
        return {"error": f"Failed to process order: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


@mcp.tool()
async def generate_product_description(product_name: str, features: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Generate an AI-powered product description.
    
    Args:
        product_name: Name of the product
        features: List of product features to highlight (optional)
        
    Returns:
        Generated product description or error message
    """
    try:
        request_data = {
            "productName": product_name,
            "features": features or []
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{AI_SERVICE_URL}/ai/generate/description",
                json=request_data,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            result = response.json()
            return {
                "message": f"Generated description for {product_name}",
                "description": result.get("description", ""),
                "product_name": product_name
            }
    except httpx.RequestError as e:
        return {"error": f"Failed to generate description: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


@mcp.tool()
async def check_ai_service_health() -> Dict[str, Any]:
    """
    Check if the AI service is available and healthy.
    
    Returns:
        Health status of the AI service
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{AI_SERVICE_URL}/health")
            response.raise_for_status()
            health_data = response.json()
            return {
                "message": "AI service is healthy",
                "status": "healthy",
                "capabilities": health_data.get("capabilities", [])
            }
    except httpx.RequestError as e:
        return {"error": f"AI service is not available: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error checking AI service: {str(e)}"}


@mcp.tool()
async def get_order_statistics() -> Dict[str, Any]:
    """
    Get statistical information about orders.
    
    Returns:
        Order statistics including count, status distribution, etc.
    """
    try:
        orders = await get_all_orders()
        if "error" in orders:
            return orders
        
        if not isinstance(orders, list):
            return {"error": "Invalid orders data format"}
        
        total_orders = len(orders)
        status_counts = {}
        total_revenue = 0
        
        for order in orders:
            # Count by status
            status = order.get("status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1
            
            # Calculate revenue (if order has items with prices)
            if "items" in order:
                for item in order["items"]:
                    price = item.get("price", 0)
                    quantity = item.get("quantity", 0)
                    total_revenue += price * quantity
        
        return {
            "total_orders": total_orders,
            "status_distribution": status_counts,
            "total_revenue": total_revenue,
            "formatted_revenue": f"${total_revenue:.2f}"
        }
    except Exception as e:
        return {"error": f"Failed to calculate order statistics: {str(e)}"}


if __name__ == "__main__":
    # Run the MCP server
    mcp.run()