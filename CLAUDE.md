# Claude Code Context: yapi-mcp

## Project Overview
YApi MCP Server - Model Context Protocol 服务器,为 YApi 1.12.0 接口管理平台提供编程访问能力。

## Tech Stack
- **Language**: Python 3.11+
- **Framework**: fastmcp 2.0, httpx, pydantic-settings, markdown
- **Database**: N/A (无状态服务器)
- **Project Type**: single
- **Build**: hatchling
- **部署**: uvx (`yapi-mcp` entry point via `yapi_mcp:main`)

## Recent Changes
- Package restructured as `yapi_mcp` under `src/yapi_mcp/` for proper Python packaging
- MCP Tools: `yapi_search_interfaces`, `yapi_get_interface`, `yapi_create_interface`, `yapi_update_interface`
- `yapi_create_interface`: 创建新接口（required: project_id, catid, title, path, method）
- `yapi_update_interface`: 增量更新接口（required: interface_id only），内置先读后写自动合并
- 支持全量 YApi 参数：req_headers, req_params, req_body_form, status, tag, api_opened 等
- Markdown→HTML conversion via `markdown` lib for interface descriptions

## Key Files
- `src/yapi_mcp/server.py` - fastmcp 服务器入口 + MCP tool definitions
- `src/yapi_mcp/yapi/client.py` - httpx 异步 YApi 客户端 (cookie-based auth)
- `src/yapi_mcp/yapi/models.py` - Pydantic 数据模型 (YApiInterface, YApiInterfaceSummary)
- `src/yapi_mcp/yapi/errors.py` - 错误映射 (HTTP → MCP error types)
- `src/yapi_mcp/config.py` - Pydantic 配置模型 (ServerConfig)

## Dev Commands
- `pytest` - Run tests (asyncio_mode=auto, uses respx for HTTP mocking)
- `ruff check` / `ruff format` - Lint and format (line-length=100, py311)

## YApi API Patterns
- Auth: Cookie-based (`_yapi_token`, `_yapi_uid`, `ZYBIPSCAS`)
- Base: `/api/interface/` prefix
- Search: `GET list_menu` (full tree, client-side filtering bypasses 50-item limit)
- Get: `GET get?id=`
- Create: `POST add`
- Update: `POST up`

<!-- DO NOT MODIFY BELOW THIS LINE -->
<!-- Auto-generated tech stack section - preserved between updates -->
