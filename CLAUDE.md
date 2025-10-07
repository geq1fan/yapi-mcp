# Claude Code Context: yapi-mcp

## Project Overview
YApi MCP Server - Model Context Protocol 服务器,为 YApi 1.12.0 接口管理平台提供编程访问能力。

## Tech Stack
- **Language**: Python 3.11+
- **Framework**: fastmcp 2.0, httpx, pydantic-settings
- **Database**: N/A (无状态服务器)
- **Project Type**: single
- **部署**: uvx (无需虚拟环境)

## Recent Changes
- 2025-10-06: 技术栈调整为 Python + fastmcp + uvx
- MCP Tools: yapi_search_interfaces, yapi_get_interface, yapi_create_interface, yapi_update_interface
- Data Model: Pydantic 模型(ServerConfig, YApiInterface, 错误处理)

## Key Files
- `src/server.py` - fastmcp 服务器入口
- `src/yapi/client.py` - httpx 异步 YApi 客户端
- `src/config.py` - Pydantic 配置模型
- `specs/001-model-context-protocol/` - 设计文档目录

<!-- DO NOT MODIFY BELOW THIS LINE -->
<!-- Auto-generated tech stack section - preserved between updates -->
