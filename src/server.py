"""YApi MCP Server - Main server module with fastmcp."""

import json
from typing import Annotated

import httpx
from fastmcp import FastMCP

from config import ServerConfig
from yapi.client import YApiClient
from yapi.errors import map_http_error_to_mcp

# Initialize MCP server
mcp = FastMCP(
    "YApi MCP Server",
    version="0.1.0",
)


def get_config() -> ServerConfig:
    """Get or create ServerConfig instance (lazy loading)."""
    if not hasattr(get_config, "_instance"):
        get_config._instance = ServerConfig()
    return get_config._instance


# Tool implementations will be added in subsequent tasks (T019-T022)


@mcp.tool()
async def yapi_search_interfaces(
    project_id: Annotated[int, "YApi 项目 ID"],
    keyword: Annotated[str, "搜索关键词(匹配接口标题/路径/描述)"],
) -> str:
    """在指定 YApi 项目中搜索接口,支持按标题、路径、描述模糊匹配."""
    config = get_config()
    try:
        async with YApiClient(str(config.yapi_server_url), config.cookies) as client:
            results = await client.search_interfaces(project_id, keyword)
            # Return JSON string with search results
            return json.dumps(
                [result.model_dump(by_alias=True) for result in results],
                ensure_ascii=False,
                indent=2,
            )
    except httpx.HTTPStatusError as e:
        mcp_error = map_http_error_to_mcp(e)
        raise Exception(mcp_error.message) from e
    except Exception as e:
        raise Exception(f"搜索接口失败: {e!s}") from e


@mcp.tool()
async def yapi_get_interface(
    interface_id: Annotated[int, "接口 ID"],
) -> str:
    """获取 YApi 接口的完整定义(包括请求参数、响应结构、描述等)."""
    config = get_config()
    try:
        async with YApiClient(str(config.yapi_server_url), config.cookies) as client:
            interface = await client.get_interface(interface_id)
            return json.dumps(
                interface.model_dump(by_alias=True),
                ensure_ascii=False,
                indent=2,
            )
    except httpx.HTTPStatusError as e:
        mcp_error = map_http_error_to_mcp(e)
        raise Exception(mcp_error.message) from e
    except Exception as e:
        raise Exception(f"获取接口失败: {e!s}") from e


@mcp.tool()
async def yapi_create_interface(
    project_id: Annotated[int, "项目 ID"],
    title: Annotated[str, "接口标题"],
    path: Annotated[str, "接口路径(以 / 开头)"],
    method: Annotated[str, "HTTP 方法(GET/POST/PUT/DELETE等)"],
    req_body: Annotated[str, "请求参数(JSON 字符串,可选)"] = "",
    res_body: Annotated[str, "响应结构(JSON 字符串,可选)"] = "",
    desc: Annotated[str, "接口描述(可选)"] = "",
) -> str:
    """在 YApi 项目中创建新接口定义."""
    config = get_config()
    try:
        # Validate path starts with /
        if not path.startswith("/"):
            raise ValueError("接口路径必须以 / 开头")

        async with YApiClient(str(config.yapi_server_url), config.cookies) as client:
            interface_id = await client.create_interface(
                project_id, title, path, method, req_body, res_body, desc
            )
            return json.dumps(
                {"interface_id": interface_id},
                ensure_ascii=False,
            )
    except httpx.HTTPStatusError as e:
        mcp_error = map_http_error_to_mcp(e)
        raise Exception(mcp_error.message) from e
    except ValueError as e:
        raise Exception(f"参数验证失败: {e!s}") from e
    except Exception as e:
        raise Exception(f"创建接口失败: {e!s}") from e


@mcp.tool()
async def yapi_update_interface(
    interface_id: Annotated[int, "接口 ID"],
    title: Annotated[str | None, "更新的标题"] = None,
    path: Annotated[str | None, "更新的路径"] = None,
    method: Annotated[str | None, "更新的 HTTP 方法"] = None,
    req_body: Annotated[str | None, "更新的请求参数"] = None,
    res_body: Annotated[str | None, "更新的响应结构"] = None,
    desc: Annotated[str | None, "更新的描述"] = None,
) -> str:
    """增量更新 YApi 接口定义(仅更新提供的字段)."""
    config = get_config()
    try:
        # Validate path if provided
        if path is not None and not path.startswith("/"):
            raise ValueError("接口路径必须以 / 开头")

        async with YApiClient(str(config.yapi_server_url), config.cookies) as client:
            success = await client.update_interface(
                interface_id, title, path, method, req_body, res_body, desc
            )
            return json.dumps(
                {"success": success, "message": "接口更新成功"},
                ensure_ascii=False,
            )
    except httpx.HTTPStatusError as e:
        mcp_error = map_http_error_to_mcp(e)
        raise Exception(mcp_error.message) from e
    except ValueError as e:
        raise Exception(f"参数验证失败: {e!s}") from e
    except Exception as e:
        raise Exception(f"更新接口失败: {e!s}") from e


def main() -> None:
    """Entry point for uvx yapi-mcp command."""
    mcp.run()


if __name__ == "__main__":
    main()
