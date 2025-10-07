"""Contract tests for MCP tools - verify tool definitions match schema.

These tests MUST fail before implementation (TDD approach).
They verify that once implemented, MCP tools conform to the contract
defined in specs/001-model-context-protocol/contracts/mcp-tools.schema.json
"""

import pytest


@pytest.mark.skip(reason="MCP tools not implemented yet - TDD placeholder")
def test_yapi_search_interfaces_contract() -> None:
    """Test yapi_search_interfaces tool matches SearchInterfacesTool schema.

    Contract requirements:
    - name: "yapi_search_interfaces"
    - description: "在指定 YApi 项目中搜索接口,支持按标题、路径、描述模糊匹配"
    - inputSchema.properties:
        - projectId: number (minimum: 1, required)
        - keyword: string (minLength: 1, maxLength: 100, required)
    """
    # This test will be implemented after MCP server setup
    # It should:
    # 1. Get tool definition from MCP server
    # 2. Verify tool name
    # 3. Verify tool description
    # 4. Verify inputSchema matches contract exactly
    #    - projectId: type=number, minimum=1, required
    #    - keyword: type=string, minLength=1, maxLength=100, required
    #    - additionalProperties: false
    pytest.fail("Tool not implemented - verify contract when implemented")


@pytest.mark.skip(reason="MCP tools not implemented yet - TDD placeholder")
def test_yapi_get_interface_contract() -> None:
    """Test yapi_get_interface tool matches GetInterfaceTool schema.

    Contract requirements:
    - name: "yapi_get_interface"
    - description: "获取 YApi 接口的完整定义(包括请求参数、响应结构、描述等)"
    - inputSchema.properties:
        - interfaceId: number (minimum: 1, required)
    """
    # This test will be implemented after MCP server setup
    # It should:
    # 1. Get tool definition from MCP server
    # 2. Verify tool name
    # 3. Verify tool description
    # 4. Verify inputSchema matches contract:
    #    - interfaceId: type=number, minimum=1, required
    #    - additionalProperties: false
    pytest.fail("Tool not implemented - verify contract when implemented")


@pytest.mark.skip(reason="MCP tools not implemented yet - TDD placeholder")
def test_yapi_create_interface_contract() -> None:
    """Test yapi_create_interface tool matches CreateInterfaceTool schema.

    Contract requirements:
    - name: "yapi_create_interface"
    - description: "在 YApi 项目中创建新接口定义"
    - inputSchema.properties (required):
        - projectId: number (minimum: 1)
        - title: string (minLength: 1, maxLength: 200)
        - path: string (pattern: ^/)
        - method: string (enum: GET/POST/PUT/DELETE/PATCH/HEAD/OPTIONS)
    - inputSchema.properties (optional):
        - reqBody: string
        - resBody: string
        - desc: string
    """
    # This test will be implemented after MCP server setup
    # It should:
    # 1. Get tool definition from MCP server
    # 2. Verify tool name
    # 3. Verify tool description
    # 4. Verify inputSchema matches contract:
    #    - All required fields: projectId, title, path, method
    #    - All optional fields: reqBody, resBody, desc
    #    - Correct types and constraints for each field
    #    - additionalProperties: false
    pytest.fail("Tool not implemented - verify contract when implemented")


@pytest.mark.skip(reason="MCP tools not implemented yet - TDD placeholder")
def test_yapi_update_interface_contract() -> None:
    """Test yapi_update_interface tool matches UpdateInterfaceTool schema.

    Contract requirements:
    - name: "yapi_update_interface"
    - description: "增量更新 YApi 接口定义(仅更新提供的字段)"
    - inputSchema.properties (required):
        - interfaceId: number (minimum: 1)
    - inputSchema.properties (optional):
        - title: string (minLength: 1, maxLength: 200)
        - path: string (pattern: ^/)
        - method: string (enum: GET/POST/PUT/DELETE/PATCH/HEAD/OPTIONS)
        - reqBody: string
        - resBody: string
        - desc: string
    """
    # This test will be implemented after MCP server setup
    # It should:
    # 1. Get tool definition from MCP server
    # 2. Verify tool name
    # 3. Verify tool description
    # 4. Verify inputSchema matches contract:
    #    - interfaceId is required
    #    - All other fields are optional
    #    - Correct types and constraints for each field
    #    - additionalProperties: false
    pytest.fail("Tool not implemented - verify contract when implemented")


@pytest.mark.skip(reason="MCP tools not implemented yet - TDD placeholder")
def test_all_four_tools_registered() -> None:
    """Test that exactly 4 MCP tools are registered.

    Contract requirement:
    - tools array must have exactly 4 items (minItems: 4, maxItems: 4)
    - tools must be: yapi_search_interfaces, yapi_get_interface,
                     yapi_create_interface, yapi_update_interface
    """
    # This test will be implemented after MCP server setup
    # It should:
    # 1. Get all registered tools from MCP server
    # 2. Verify exactly 4 tools
    # 3. Verify tool names match expected set
    pytest.fail("MCP server not implemented - verify all 4 tools registered")
