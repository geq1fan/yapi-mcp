# Quickstart Guide: YApi MCP Server (Python + uvx)

**Feature**: 001-model-context-protocol
**Date**: 2025-10-06 (Updated for Python + fastmcp)

## Overview
本指南演示如何使用 uvx 快速启动和测试 YApi MCP Server,验证核心功能是否正常工作。

---

## Prerequisites

### 1. 环境要求
- Python 3.11+ (推荐 3.12)
- 可访问的 YApi 1.12.0 实例
- 有效的 YApi 认证 Cookie

### 2. 安装 uvx
```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# 或使用 pip
pip install uv
```

### 3. 获取 YApi Cookies
1. 在浏览器中登录 YApi
2. 打开开发者工具(F12) → Application/Storage → Cookies
3. 复制以下 Cookie 值:
   - `_yapi_token`
   - `_yapi_uid`
   - `ZYBIPSCAS`

---

## Installation

```bash
# 克隆仓库
git clone <repo-url>
cd yapi-mcp

# uvx 会自动处理依赖,无需手动安装
```

---

## Configuration

### 方式 1: 环境变量(推荐)
```bash
# macOS/Linux
export YAPI_SERVER_URL="https://your-yapi-instance.com"
export YAPI_TOKEN="your_yapi_token_value"
export YAPI_UID="your_uid_value"
export YAPI_CAS="your_cas_value"

# Windows (PowerShell)
$env:YAPI_SERVER_URL="https://your-yapi-instance.com"
$env:YAPI_TOKEN="your_yapi_token_value"
$env:YAPI_UID="your_uid_value"
$env:YAPI_CAS="your_cas_value"
```

### 方式 2: .env 文件
创建 `.env` 文件(不要提交到 Git):
```env
YAPI_SERVER_URL=https://your-yapi-instance.com
YAPI_TOKEN=your_yapi_token_value
YAPI_UID=your_uid_value
YAPI_CAS=your_cas_value
```

---

## Start the Server

### 使用 uvx (推荐)
```bash
uvx fastmcp run src/server.py
```

### 或使用 fastmcp dev 模式(支持热重载)
```bash
uvx fastmcp dev src/server.py
```

Expected output:
```
FastMCP Server: YApi MCP Server
Connected to YApi: https://your-yapi-instance.com
Registered tools: yapi_search_interfaces, yapi_get_interface, yapi_create_interface, yapi_update_interface
Server ready on stdio transport
```

---

## Test Scenarios

### Test 1: 搜索接口 (FR-003)

**Objective**: 验证能够搜索 YApi 项目中的接口

**Precondition**:
- 已知的 YApi 项目 ID (例如: 123)
- 项目中存在包含关键词的接口

**Steps (使用 fastmcp client)**:
```python
# test_quickstart.py
import asyncio
from fastmcp import FastMCP
from fastmcp.testing import Client

async def test_search():
    # 假设 mcp 是你的服务器实例
    async with Client(mcp) as client:
        result = await client.call_tool("yapi_search_interfaces", {
            "project_id": 123,
            "keyword": "login"
        })
        print(result.content[0].text)

asyncio.run(test_search())
```

**Expected Result**:
```json
[
  {"id": 456, "title": "用户登录接口", "path": "/api/user/login", "method": "POST"}
]
```

**Success Criteria**:
- ✅ 返回至少 1 个匹配的接口
- ✅ 结果包含 id, title, path, method 四个字段
- ✅ 如果超过 50 条,仅返回前 50 条

---

### Test 2: 获取接口详情 (FR-004)

**Objective**: 验证能够获取接口的完整定义

**Precondition**:
- 从 Test 1 获取的有效接口 ID (例如: 456)

**Steps**:
```python
async def test_get_interface():
    async with Client(mcp) as client:
        result = await client.call_tool("yapi_get_interface", {
            "interface_id": 456
        })
        print(result.content[0].text)
```

**Expected Result**:
```json
{
  "id": 456,
  "title": "用户登录接口",
  "path": "/api/user/login",
  "method": "POST",
  "project_id": 123,
  "desc": "用户登录",
  "req_body_other": "{...}",
  "res_body": "{...}"
}
```

**Success Criteria**:
- ✅ 返回完整接口定义
- ✅ 包含请求参数(`req_body_other`)和响应结构(`res_body`)
- ✅ 如果接口不存在,抛出 MCPError(code=-32002)

---

### Test 3: 创建接口 (FR-005)

**Objective**: 验证能够创建新接口

**Precondition**:
- 有权限创建接口的项目 ID
- 有效的认证 Cookie

**Steps**:
```python
async def test_create_interface():
    async with Client(mcp) as client:
        result = await client.call_tool("yapi_create_interface", {
            "project_id": 123,
            "title": "测试接口",
            "path": "/api/test",
            "method": "GET",
            "req_body": "{}",
            "res_body": "{}",
            "desc": "Quickstart 测试接口"
        })
        print(result.content[0].text)
```

**Expected Result**:
```json
{"interface_id": 789}
```

**Success Criteria**:
- ✅ 返回新创建接口的 ID
- ✅ 在 YApi Web UI 中能看到新接口
- ✅ 必填字段缺失时抛出 MCPError(code=-32602)

---

### Test 4: 更新接口 (FR-006)

**Objective**: 验证能够增量更新接口

**Precondition**:
- 从 Test 3 获取的接口 ID (例如: 789)

**Steps**:
```python
async def test_update_interface():
    async with Client(mcp) as client:
        result = await client.call_tool("yapi_update_interface", {
            "interface_id": 789,
            "title": "测试接口(已修改)"
        })
        print(result.content[0].text)
```

**Expected Result**:
```json
{"success": true, "message": "接口更新成功"}
```

**Success Criteria**:
- ✅ 接口标题更新成功
- ✅ 其他字段(path, method)保持不变
- ✅ 在 YApi Web UI 中确认更改

---

### Test 5: 错误处理 (FR-007, FR-008)

**Objective**: 验证错误场景处理

**Scenarios**:

#### 5.1 认证失败
```python
# 修改 .env 中的 YAPI_TOKEN 为无效值,重启服务器
# 尝试调用任意 Tool
async def test_auth_error():
    try:
        async with Client(mcp) as client:
            await client.call_tool("yapi_search_interfaces", {
                "project_id": 123,
                "keyword": "test"
            })
    except MCPError as e:
        assert e.code == -32001
        assert "认证失败" in e.message
```

**Expected**: MCPError(code=-32001, message="认证失败: Cookie 无效或过期")

#### 5.2 资源不存在
```python
async def test_not_found():
    try:
        async with Client(mcp) as client:
            await client.call_tool("yapi_get_interface", {
                "interface_id": 999999
            })
    except MCPError as e:
        assert e.code == -32002
        assert "资源不存在" in e.message
```

**Expected**: MCPError(code=-32002)

#### 5.3 服务器不可用
```python
# 修改 YAPI_SERVER_URL 为无效地址
async def test_server_error():
    try:
        async with Client(mcp) as client:
            await client.call_tool("yapi_search_interfaces", {
                "project_id": 123,
                "keyword": "test"
            })
    except MCPError as e:
        assert e.code == -32000
        assert "YApi 服务器错误" in e.message
```

**Expected**: MCPError(code=-32000)

---

## Cleanup

测试完成后清理测试数据(手动在 YApi Web UI 中删除 Test 3 创建的接口)。

---

## Validation Checklist

完成以下所有测试后,验证:
- [ ] Test 1: 搜索接口成功
- [ ] Test 2: 获取接口详情成功
- [ ] Test 3: 创建接口成功
- [ ] Test 4: 更新接口成功
- [ ] Test 5.1: 认证失败错误处理正确
- [ ] Test 5.2: 资源不存在错误处理正确
- [ ] Test 5.3: 服务器不可用错误处理正确

**All tests passed** → ✅ Ready for production use

---

## Troubleshooting

### 问题: uvx 命令未找到
- **解决**: 确保已安装 uv: `pip install uv` 或参考安装部分
- **检查**: `uvx --version` 应显示版本号

### 问题: Server 无法启动
- **检查**: Python 版本 >= 3.11 (`python --version`)
- **检查**: 环境变量或 `.env` 文件正确配置
- **检查**: `src/server.py` 文件存在

### 问题: 所有请求返回 -32001 认证错误
- **检查**: Cookie 值是否正确复制(无多余空格)
- **检查**: Cookie 是否过期(重新登录 YApi 获取新 Cookie)
- **检查**: YApi 服务器 URL 是否正确

### 问题: 搜索返回空结果
- **检查**: 项目 ID 是否正确
- **检查**: 项目中是否存在包含关键词的接口
- **检查**: 是否有权限访问该项目

### 问题: fastmcp 导入错误
- **解决**: 使用 uvx 会自动处理依赖,无需手动安装
- **或**: `pip install fastmcp httpx pydantic-settings`

---

## Next Steps

Quickstart 通过后:
1. 将 MCP Server 集成到你的 IDE/编辑器(Claude Code, Cursor, etc.)
2. 参考 [README.md](../../../README.md) 了解高级配置
3. 查看 [data-model.md](./data-model.md) 了解完整数据结构

**Status**: ✅ Quickstart guide complete (Python + uvx 版本).
