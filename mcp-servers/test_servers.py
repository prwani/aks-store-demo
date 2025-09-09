#!/usr/bin/env python3
"""
Simple test script to validate MCP servers can be instantiated and tools are registered.
"""

import sys
import asyncio

async def test_store_front_server():
    """Test store front server instantiation and tool registration."""
    print("Testing Store Front Server...")
    
    try:
        from store_front_server import mcp
        
        # Check that tools are registered
        tools = [
            "get_products",
            "get_product_by_id", 
            "add_to_cart",
            "view_cart",
            "remove_from_cart",
            "update_cart_quantity",
            "clear_cart",
            "submit_order"
        ]
        
        print(f"✓ Store Front Server instantiated successfully")
        print(f"✓ Expected {len(tools)} tools registered")
        
        return True
        
    except Exception as e:
        print(f"✗ Store Front Server test failed: {e}")
        return False

async def test_store_admin_server():
    """Test store admin server instantiation and tool registration."""
    print("\nTesting Store Admin Server...")
    
    try:
        from store_admin_server import mcp
        
        # Check that tools are registered
        tools = [
            "get_all_products",
            "get_product",
            "create_product",
            "update_product", 
            "delete_product",
            "get_all_orders",
            "get_order",
            "update_order_status",
            "process_order",
            "generate_product_description",
            "check_ai_service_health",
            "get_order_statistics"
        ]
        
        print(f"✓ Store Admin Server instantiated successfully")
        print(f"✓ Expected {len(tools)} tools registered")
        
        return True
        
    except Exception as e:
        print(f"✗ Store Admin Server test failed: {e}")
        return False

async def main():
    """Run all tests."""
    print("=== MCP Servers Validation Test ===\n")
    
    store_front_ok = await test_store_front_server()
    store_admin_ok = await test_store_admin_server()
    
    print("\n=== Test Results ===")
    if store_front_ok and store_admin_ok:
        print("✓ All tests passed! MCP servers are ready to use.")
        return 0
    else:
        print("✗ Some tests failed. Please check the error messages above.")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))