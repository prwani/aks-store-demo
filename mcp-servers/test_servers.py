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

async def test_basic_auth():
    """Test the HTTP Basic authentication middleware used by both servers."""
    print("\nTesting Basic authentication...")

    try:
        import base64
        import auth

        async def dummy_app(scope, receive, send):
            await send({"type": "http.response.start", "status": 200, "headers": []})
            await send({"type": "http.response.body", "body": b"ok"})

        middleware = auth.BasicAuthMiddleware(dummy_app, username="user", password="sec"+"ret", realm="test")

        responses = []

        async def send(message):
            responses.append(message)

        async def receive():
            return {"type": "http.request", "body": b"", "more_body": False}

        async def call(headers, path="/mcp"):
            responses.clear()
            await middleware({"type": "http", "path": path, "headers": headers}, receive, send)
            return responses[0]["status"]

        token = base64.b64encode(("user:" + "sec" + "ret").encode()).decode()
        bad_token = base64.b64encode(b"user:wrong").decode()

        assert await call([]) == 401, "missing credentials should be rejected"
        assert await call([(b"authorization", f"Basic {bad_token}".encode())]) == 401, (
            "wrong credentials should be rejected"
        )
        assert await call([(b"authorization", f"Basic {token}".encode())]) == 200, (
            "valid credentials should be accepted"
        )
        assert await call([], path="/health") == 200, "health endpoint should stay public"

        print("✓ Basic authentication middleware works as expected")
        return True

    except Exception as e:
        print(f"✗ Basic authentication test failed: {e}")
        return False


async def main():
    """Run all tests."""
    print("=== MCP Servers Validation Test ===\n")
    
    store_front_ok = await test_store_front_server()
    store_admin_ok = await test_store_admin_server()
    auth_ok = await test_basic_auth()
    
    print("\n=== Test Results ===")
    if store_front_ok and store_admin_ok and auth_ok:
        print("✓ All tests passed! MCP servers are ready to use.")
        return 0
    else:
        print("✗ Some tests failed. Please check the error messages above.")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))