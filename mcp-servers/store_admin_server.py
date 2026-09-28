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
            response = await client.get(f"{PRODUCT_SERVICE_URL}/")
            response.raise_for_status()
            products = response.json()
            return products
    except httpx.RequestError as e:
        return {"error": f"Failed to fetch products: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


@mcp.tool()
async def get_product(product_id: int) -> Dict[str, Any]:
    """
    Get details of a specific product for admin management.
    
    Args:
        product_id: The numeric identifier of the product
        
    Returns:
        Complete product details
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{PRODUCT_SERVICE_URL}/{product_id}")
            if response.status_code == 404:
                return {"error": f"Product {product_id} not found"}
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
    image: str = ""
) -> Dict[str, Any]:
    """
    Create a new product in the catalog.
    
    The product-service assigns the new product's id; it does not accept
    an id, category, or tags field.
    
    Args:
        name: Product name
        price: Product price
        description: Product description
        image: Product image URL (optional)
        
    Returns:
        Created product details or error message
    """
    try:
        product_data = {
            "name": name,
            "price": price,
            "description": description,
            "image": image or ""
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{PRODUCT_SERVICE_URL}/",
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
    product_id: int,
    name: Optional[str] = None,
    price: Optional[float] = None,
    description: Optional[str] = None,
    image: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update an existing product in the catalog.
    
    product-service's update endpoint replaces the whole product record
    (matched by id), so this reads the current product first and merges
    in only the fields that were provided.
    
    Args:
        product_id: The numeric identifier of the product to update
        name: New product name (optional)
        price: New product price (optional)
        description: New product description (optional)
        image: New product image URL (optional)
        
    Returns:
        Updated product details or error message
    """
    try:
        # First get the existing product, since the API requires the full record
        existing_product = await get_product(product_id)
        if "error" in existing_product:
            return existing_product
        
        updated_data = {
            "id": product_id,
            "name": name if name is not None else existing_product["name"],
            "price": price if price is not None else existing_product["price"],
            "description": description if description is not None else existing_product["description"],
            "image": image if image is not None else existing_product["image"]
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{PRODUCT_SERVICE_URL}/",
                json=updated_data,
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
async def delete_product(product_id: int) -> Dict[str, Any]:
    """
    Delete a product from the catalog.
    
    Args:
        product_id: The numeric identifier of the product to delete
        
    Returns:
        Confirmation message or error
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.delete(f"{PRODUCT_SERVICE_URL}/{product_id}")
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
        order_id: The numeric identifier of the order (as a string)
        
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
async def update_order_status(order_id: str, status: int) -> Dict[str, Any]:
    """
    Update the status of an order.
    
    makeline-service's update endpoint takes the whole order object at
    PUT /order (no id in the path), so this reads the current order first
    and PUTs it back with the new status.
    
    Args:
        order_id: The numeric identifier of the order (as a string)
        status: New status code: 0 = Pending, 1 = Processing/Completed, 2 = Complete
        
    Returns:
        Updated order details or error message
    """
    try:
        existing_order = await get_order(order_id)
        if "error" in existing_order:
            return existing_order
        
        existing_order["status"] = status
        
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{MAKELINE_SERVICE_URL}/order",
                json=existing_order,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            return {
                "message": f"Successfully updated order {order_id} status to {status}",
                "order": existing_order
            }
    except httpx.RequestError as e:
        return {"error": f"Failed to update order status: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


@mcp.tool()
async def process_order(order_id: str) -> Dict[str, Any]:
    """
    Process an order, mirroring the "Complete Order" action in store-admin,
    which sets the order status to 1.
    
    Args:
        order_id: The numeric identifier of the order to process
        
    Returns:
        Processing confirmation or error message
    """
    result = await update_order_status(order_id, 1)
    if "error" in result:
        return result
    return {
        "message": f"Successfully processed order: {order_id}",
        "order": result.get("order")
    }


@mcp.tool()
async def generate_product_description(product_name: str, tags: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Generate an AI-powered product description using the ai-service.
    
    Args:
        product_name: Name of the product
        tags: List of tags/features to highlight in the description (optional)
        
    Returns:
        Generated product description or error message
    """
    try:
        request_data = {
            "name": product_name,
            "tags": tags or []
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{AI_SERVICE_URL}/generate/description",
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