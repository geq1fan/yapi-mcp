# Technical Research: YApi MCP Server

**Date**: 2025-10-06 (Updated)
**Feature**: 001-model-context-protocol

## Research Questions

### 1. Language & SDK Selection

**Decision**: Python 3.11+ + fastmcp + uvx

**Rationale**:
- **fastmcp**: Pythonic 框架,极简 API,装饰器模式(`@mcp.tool`)零样板代码
- **uvx**: 无需虚拟环境管理,`uvx fastmcp run server.py` 一键启动
- **生态优势**: Python 的 requests/httpx 库成熟,类型提示(Pydantic)强大
- **部署简单**: fastmcp 支持 stdio/http 双传输,uvx 打包分发便捷
- **开发体验**: fastmcp 2.0 提供完整测试框架、认证集成、动态工具管理

**Alternatives Considered**:
- **TypeScript SDK**: 官方支持但需配置 Node.js 环境,样板代码较多
- **Python 官方 SDK**: 功能完整但 API 较底层,fastmcp 是其高层封装

**References**:
- fastmcp: `/jlowin/fastmcp` (Trust Score: 9.3, 1179 code snippets)
- fastmcp 文档: https://gofastmcp.com
- uvx: Python 包执行器,类似 npx

---

### 2. MCP Tool Design

**Decision**: 4 个独立 tools,映射到 YApi 的 4 个核心操作

**Tool Definitions** (Python + Pydantic):

#### 2.1 `yapi_search_interfaces`
- **Purpose**: 在指定项目中搜索接口
- **Function Signature**:
  ```python
  @mcp.tool
  def yapi_search_interfaces(project_id: int, keyword: str) -> str:
      """在 YApi 项目中搜索接口,支持按标题/路径/描述模糊匹配"""
      # project_id: YApi 项目 ID
      # keyword: 搜索关键词
      # 返回: JSON 字符串,最多 50 条接口
  ```
- **Output**: JSON 列表,包含 id, title, path, method

#### 2.2 `yapi_get_interface`
- **Purpose**: 获取接口完整定义
- **Function Signature**:
  ```python
  @mcp.tool
  def yapi_get_interface(interface_id: int) -> str:
      """获取 YApi 接口的完整定义"""
      # interface_id: 接口 ID
      # 返回: 完整接口 JSON
  ```

#### 2.3 `yapi_create_interface`
- **Purpose**: 创建新接口
- **Function Signature**:
  ```python
  @mcp.tool
  def yapi_create_interface(
      project_id: int,
      title: str,
      path: str,
      method: str,
      req_body: str = "",
      res_body: str = "",
      desc: str = ""
  ) -> str:
      """在 YApi 项目中创建新接口"""
      # 返回: {"interface_id": 123}
  ```

#### 2.4 `yapi_update_interface`
- **Purpose**: 增量更新接口
- **Function Signature**:
  ```python
  @mcp.tool
  def yapi_update_interface(
      interface_id: int,
      title: str | None = None,
      path: str | None = None,
      method: str | None = None,
      req_body: str | None = None,
      res_body: str | None = None,
      desc: str | None = None
  ) -> str:
      """增量更新 YApi 接口定义"""
      # 返回: {"success": true}
  ```

**Rationale**:
- fastmcp 自动处理参数验证和 JSON 序列化
- Python 类型提示提供编译时检查
- 装饰器模式简洁,无需手动注册工具

---

### 3. YApi API Integration

**Decision**: 使用 httpx 作为 HTTP 客户端(async 支持)

**HTTP Client**: `httpx` (优于 requests)
- 原生 async/await 支持
- 自动 Cookie 管理
- 超时和重试内置

**Client Implementation**:
```python
import httpx
from typing import Any

class YApiClient:
    def __init__(self, base_url: str, cookies: dict[str, str]):
        self.client = httpx.AsyncClient(
            base_url=f"{base_url}/api",
            cookies=cookies,
            timeout=10.0
        )

    async def search_interfaces(self, project_id: int, keyword: str) -> list[dict]:
        response = await self.client.post("/interface/list", json={
            "project_id": project_id,
            "q": keyword
        })
        response.raise_for_status()
        return response.json()["data"]["list"][:50]  # 限制 50 条
```

**Error Mapping** (unchanged):
| YApi 错误 | MCP 错误码 | 消息 |
|-----------|-----------|------|
| 401 Unauthorized | -32001 | "认证失败: Cookie 无效或过期" |
| 404 Not Found | -32002 | "资源不存在: {详情}" |
| 403 Forbidden | -32003 | "权限不足: 无法操作该项目/接口" |
| 500 Server Error | -32000 | "YApi 服务器错误: {详情}" |

---

### 4. Configuration Management

**Decision**: 环境变量 + Pydantic Settings

**Configuration Model** (Pydantic BaseSettings):
```python
from pydantic_settings import BaseSettings

class ServerConfig(BaseSettings):
    yapi_server_url: str
    yapi_token: str
    yapi_uid: str
    yapi_cas: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# 使用
config = ServerConfig()  # 自动从环境变量或 .env 加载
```

**Loading Priority**:
1. 环境变量: `YAPI_SERVER_URL`, `YAPI_TOKEN`, `YAPI_UID`, `YAPI_CAS`
2. `.env` 文件(不纳入版本控制)
3. Pydantic 自动验证必填字段

**Rationale**:
- Pydantic 提供类型验证和错误提示
- 支持多种配置源(环境变量、文件、CLI 参数)
- fastmcp 原生集成 Pydantic

---

### 5. Testing Strategy

**Decision**: pytest + fastmcp 内置测试工具

#### 5.1 Tool Tests
```python
import pytest
from fastmcp.testing import Client

@pytest.mark.asyncio
async def test_search_interfaces():
    """测试搜索接口工具"""
    async with Client(mcp) as client:
        result = await client.call_tool("yapi_search_interfaces", {
            "project_id": 123,
            "keyword": "login"
        })
        assert result.content[0].text  # 验证返回非空
```

#### 5.2 Integration Tests (Mock YApi)
```python
import respx

@pytest.mark.asyncio
@respx.mock
async def test_yapi_search_with_mock():
    """Mock YApi API 响应"""
    respx.post("https://yapi.example.com/api/interface/list").mock(
        return_value=httpx.Response(200, json={"data": {"list": []}})
    )

    result = await yapi_client.search_interfaces(123, "test")
    assert result == []
```

#### 5.3 End-to-End Tests
- 使用 fastmcp Client 连接真实 YApi 实例(可选)
- 在 CI 环境中跳过(需要真实凭证)

**Framework**: pytest + pytest-asyncio + respx(HTTP mocking)

---

### 6. Performance & Constraints

**Decision**: 无需复杂优化,保持简单

**Baseline Goals**:
- 响应延迟: <500ms (主要受 YApi API 性能限制)
- 并发支持: 10 个请求(httpx 异步客户端天然支持)
- 内存占用: <30MB (Python 解释器 + fastmcp 开销)

**Non-Goals** (unchanged):
- 不实现请求缓存
- 不支持批量操作
- 不做连接池优化(httpx 自动管理)

**Rationale**: Linus 原则 - "先让它跑起来,再让它跑得快"

---

## Resolved Unknowns

| Technical Context Item | Resolution |
|------------------------|-----------|
| Language/Version | ✅ Python 3.11+ |
| Primary Dependencies | ✅ fastmcp, httpx, pydantic-settings |
| Testing | ✅ pytest + pytest-asyncio + respx |
| 部署方式 | ✅ uvx (无需虚拟环境) |

## Remaining Unknowns (Phase 4 Implementation)

1. **YApi API Endpoints**: 需实际测试确认精确路径和参数格式
2. **搜索 API 行为**: 服务端是否支持多字段模糊匹配?
3. **权限验证机制**: YApi 如何返回权限错误?(FR-009)

**Mitigation Strategy**:
- Phase 4 实现时通过本地 YApi 实例验证
- 或分析 YApi 源码 `server/controllers/interface.js`
- 或浏览器开发者工具抓包分析

---

## Dependencies

### Core Dependencies
```toml
# pyproject.toml or requirements.txt
fastmcp = "^2.0.0"
httpx = "^0.27.0"
pydantic-settings = "^2.0.0"
```

### Dev Dependencies
```toml
pytest = "^8.0.0"
pytest-asyncio = "^0.23.0"
respx = "^0.21.0"  # HTTP mocking
```

### Runtime
- Python 3.11+
- uvx (安装: `pip install uv`)

---

**Status**: ✅ Research complete. Ready for Phase 1 design (Python 版本).
