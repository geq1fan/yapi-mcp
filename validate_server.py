"""Quick validation script to verify MCP server structure."""

import sys


def validate_server():
    """Validate that the MCP server is properly configured."""
    errors = []

    # Check imports
    try:
        from src.config import ServerConfig
        print("✓ ServerConfig import successful")
    except ImportError as e:
        errors.append(f"✗ Failed to import ServerConfig: {e}")

    try:
        from src.yapi.client import YApiClient
        print("✓ YApiClient import successful")
    except ImportError as e:
        errors.append(f"✗ Failed to import YApiClient: {e}")

    try:
        from src.yapi.errors import MCPError, map_http_error_to_mcp
        print("✓ Error handling imports successful")
    except ImportError as e:
        errors.append(f"✗ Failed to import error handling: {e}")

    try:
        from src.server import mcp
        print("✓ MCP server import successful")
    except ImportError as e:
        errors.append(f"✗ Failed to import MCP server: {e}")
        return errors

    # Check MCP tools exist in module
    try:
        from src import server

        expected_tools = [
            "yapi_search_interfaces",
            "yapi_get_interface",
            "yapi_create_interface",
            "yapi_update_interface",
        ]

        found_tools = []
        for tool_name in expected_tools:
            if hasattr(server, tool_name):
                found_tools.append(tool_name)

        if len(found_tools) == 4:
            print("✓ All 4 expected MCP tools are defined:")
            for tool_name in sorted(found_tools):
                print(f"  - {tool_name}")
        else:
            missing = set(expected_tools) - set(found_tools)
            errors.append(f"✗ Missing tool functions: {missing}")

    except Exception as e:
        errors.append(f"✗ Failed to validate tools: {e}")

    return errors


if __name__ == "__main__":
    print("=" * 60)
    print("YApi MCP Server Validation")
    print("=" * 60)
    print()

    errors = validate_server()

    print()
    print("=" * 60)
    if errors:
        print("VALIDATION FAILED")
        print("=" * 60)
        for error in errors:
            print(error)
        sys.exit(1)
    else:
        print("VALIDATION PASSED ✓")
        print("=" * 60)
        print()
        print("Server is ready to run. To start:")
        print("  1. Configure .env with your YApi credentials")
        print("  2. Run: uvx fastmcp run src/server.py")
        sys.exit(0)
