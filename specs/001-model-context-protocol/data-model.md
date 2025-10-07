# Data Model: YApi MCP Server (Python)

**Feature**: 001-model-context-protocol
**Date**: 2025-10-06 (Updated for Python + fastmcp)

## Overview

YApi MCP Server 作为无状态适配器,使用 Pydantic 模型定义数据结构。本文档定义:
1. 配置模型(Pydantic BaseSettings)
2. YApi API 数据模型(Pydantic BaseModel)
3. MCP Tools 的输入/输出类型

---

## 1. Configuration Model

### 1.1 ServerConfig (Pydantic BaseSettings)
MCP 服务器启动配置,自动从环境变量或 `.env` 文件加载。

```python
from pydantic_settings import BaseSettings
from pydantic import HttpUrl, Field

class ServerConfig(BaseSettings):
    """YApi MCP Server 配置"""

    yapi_server_url: HttpUrl = Field(
        ...,
        description="YApi 服务器地址",
        examples=["https://yapi.example.com"]
    )

    yapi_token: str = Field(
        ...,
        min_length=1,
        description="YApi 认证令牌 (_yapi_token)"
    )

    yapi_uid: str = Field(
        ...,
        min_length=1,
        description="YApi 用户 ID (_yapi_uid)"
    )

    yapi_cas: str = Field(
        ...,
        min_length=1,
        description="额外认证标识 (ZYBIPSCAS)"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# 使用示例
config = ServerConfig()  # 自动加载环境变量
cookies = {
    "_yapi_token": config.yapi_token,
    "_yapi_uid": config.yapi_uid,
    "ZYBIPSCAS": config.yapi_cas
}
```

**Validation Rules**:
- `yapi_server_url` 必须是有效的 HTTP/HTTPS URL(Pydantic HttpUrl 自动验证)
- 所有 cookie 字段不能为空(`min_length=1`)
- 缺失字段时 Pydantic 抛出 `ValidationError`

---

## 2. YApi Data Model

### 2.1 YApiInterface (完整接口定义)
从 YApi API 获取的接口数据,使用 Pydantic 解析和验证。

```python
from pydantic import BaseModel, Field
from typing import Optional, Literal

class YApiInterface(BaseModel):
    """YApi 接口完整定义"""

    id: int = Field(..., alias="_id", description="接口 ID")
    title: str = Field(..., description="接口标题")
    path: str = Field(..., description="接口路径", examples=["/api/user/login"])

    method: Literal["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"] = Field(
        ...,
        description="HTTP 方法"
    )

    project_id: int = Field(..., description="所属项目 ID")

    desc: Optional[str] = Field(None, description="接口描述")
    req_body_other: Optional[str] = Field(None, description="请求参数定义(JSON 字符串)")
    res_body: Optional[str] = Field(None, description="响应结构定义(JSON 字符串)")
    status: Optional[str] = Field(None, description="状态码")

    add_time: Optional[int] = Field(None, description="创建时间(Unix timestamp)")
    up_time: Optional[int] = Field(None, description="更新时间(Unix timestamp)")

    class Config:
        populate_by_name = True  # 允许使用 alias
```

**Notes**:
- `alias="_id"` 映射 YApi 的 `_id` 字段到 Python 的 `id` 属性
- `Literal` 类型确保 method 只能是指定的 HTTP 方法
- `Optional` 字段在 YApi 响应中可能缺失

### 2.2 YApiInterfaceSummary (搜索结果)
搜索接口时返回的精简信息。

```python
class YApiInterfaceSummary(BaseModel):
    """搜索结果的精简接口信息"""

    id: int = Field(..., alias="_id")
    title: str
    path: str
    method: str  # 搜索结果可能不严格验证类型

    class Config:
        populate_by_name = True
```

### 2.3 YApiProject (项目信息)
项目基本信息(通常不需单独获取)。

```python
class YApiProject(BaseModel):
    """YApi 项目信息"""

    id: int = Field(..., alias="_id")
    name: str
    desc: Optional[str] = None

    class Config:
        populate_by_name = True
```

---

## 3. MCP Tool Input/Output Types

### 3.1 Tool Function Signatures

fastmcp 使用 Python 类型提示自动生成 MCP schema,无需额外定义。

#### search_interfaces
```python
from typing import Annotated

@mcp.tool
def yapi_search_interfaces(
    project_id: Annotated[int, "YApi 项目 ID"],
    keyword: Annotated[str, "搜索关键词(匹配标题/路径/描述)"]
) -> str:
    """在 YApi 项目中搜索接口"""
    # 返回: JSON 字符串,YApiInterfaceSummary 列表(最多 50 条)
    pass
```

**Output Format**:
```json
[
  {"id": 123, "title": "用户登录", "path": "/api/login", "method": "POST"},
  ...
]
```

#### get_interface
```python
@mcp.tool
def yapi_get_interface(
    interface_id: Annotated[int, "接口 ID"]
) -> str:
    """获取接口完整定义"""
    # 返回: YApiInterface JSON
    pass
```

#### create_interface
```python
@mcp.tool
def yapi_create_interface(
    project_id: Annotated[int, "项目 ID"],
    title: Annotated[str, "接口标题"],
    path: Annotated[str, "接口路径(以 / 开头)"],
    method: Annotated[str, "HTTP 方法(GET/POST/PUT/DELETE等)"],
    req_body: Annotated[str, "请求参数(JSON 字符串,可选)"] = "",
    res_body: Annotated[str, "响应结构(JSON 字符串,可选)"] = "",
    desc: Annotated[str, "接口描述(可选)"] = ""
) -> str:
    """创建新接口"""
    # 返回: {"interface_id": 456}
    pass
```

#### update_interface
```python
@mcp.tool
def yapi_update_interface(
    interface_id: Annotated[int, "接口 ID"],
    title: Annotated[str | None, "更新的标题"] = None,
    path: Annotated[str | None, "更新的路径"] = None,
    method: Annotated[str | None, "更新的 HTTP 方法"] = None,
    req_body: Annotated[str | None, "更新的请求参数"] = None,
    res_body: Annotated[str | None, "更新的响应结构"] = None,
    desc: Annotated[str | None, "更新的描述"] = None
) -> str:
    """增量更新接口"""
    # 返回: {"success": true, "message": "接口更新成功"}
    pass
```

**Key Points**:
- `Annotated[type, "description"]` 提供 LLM 上下文
- fastmcp 自动将类型提示转换为 MCP JSON Schema
- 可选参数使用 `= None` 或默认值

---

## 4. Error Model

### 4.1 YApiErrorResponse
YApi API 错误响应的 Pydantic 模型。

```python
class YApiErrorResponse(BaseModel):
    """YApi API 错误响应"""

    errcode: int = Field(..., description="错误码(非 0)")
    errmsg: str = Field(..., description="错误消息")
```

### 4.2 MCP Error Handling

fastmcp 使用异常来触发 MCP 错误响应。

```python
from fastmcp import MCPError

# 示例:认证失败
if response.status_code == 401:
    raise MCPError(
        code=-32001,
        message="认证失败: Cookie 无效或过期",
        data={"yapi_error": response.json()}
    )

# 示例:资源不存在
if response.status_code == 404:
    raise MCPError(
        code=-32002,
        message=f"资源不存在: 接口 {interface_id}",
        data={"yapi_error": response.json()}
    )
```

**Error Code Mapping** (unchanged):
| YApi 场景 | HTTP Status | MCP Error Code | Message Template |
|-----------|-------------|----------------|------------------|
| 认证失败 | 401 | -32001 | "认证失败: Cookie 无效或过期" |
| 资源不存在 | 404 | -32002 | "资源不存在: {detail}" |
| 权限不足 | 403 | -32003 | "权限不足: 无法操作该项目/接口" |
| 服务器错误 | 500 | -32000 | "YApi 服务器错误: {detail}" |
| 参数验证错误 | 400 | -32602 | "Invalid params: {detail}" |

---

## 5. Data Validation

### 5.1 Pydantic Validators

使用 Pydantic 的 `@field_validator` 添加自定义验证。

```python
from pydantic import field_validator

class CreateInterfaceInput(BaseModel):
    """创建接口的输入验证模型(可选,用于额外验证)"""

    path: str
    method: str

    @field_validator("path")
    @classmethod
    def path_must_start_with_slash(cls, v: str) -> str:
        if not v.startswith("/"):
            raise ValueError("接口路径必须以 / 开头")
        return v

    @field_validator("method")
    @classmethod
    def method_must_be_uppercase(cls, v: str) -> str:
        allowed = ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]
        if v.upper() not in allowed:
            raise ValueError(f"HTTP 方法必须是: {', '.join(allowed)}")
        return v.upper()
```

### 5.2 JSON Schema Validation

对 `req_body` 和 `res_body` 的 JSON 验证(可选):

```python
import json

def validate_json_string(value: str | None) -> str | None:
    """验证 JSON 字符串格式"""
    if value is None or value == "":
        return value
    try:
        json.loads(value)  # 仅验证格式,不解析
        return value
    except json.JSONDecodeError as e:
        raise ValueError(f"无效的 JSON 格式: {e}")
```

---

## 6. Type Aliases

为常用类型定义别名。

```python
from typing import TypeAlias

# HTTP 方法类型
HttpMethod: TypeAlias = Literal["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]

# Cookie 字典类型
YApiCookies: TypeAlias = dict[str, str]

# 接口 ID 类型
InterfaceId: TypeAlias = int
ProjectId: TypeAlias = int
```

---

**Status**: ✅ Data model complete (Python + Pydantic 版本).
