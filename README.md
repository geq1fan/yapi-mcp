# YApi MCP Server

[![CI](https://github.com/YOUR_USERNAME/yapi-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR_USERNAME/yapi-mcp/actions/workflows/ci.yml)
[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

基于 [YApi 1.12.0](https://github.com/YMFE/yapi) 接口管理平台的 Model Context Protocol (MCP) 服务器。

使开发者能够在支持 MCP 的 IDE 和编辑器(Claude Code、Cursor 等)中直接搜索、查看、创建和更新 YApi 接口定义,无需离开开发环境。

## 功能特性

- 🔍 **搜索接口**: 通过标题、路径或描述查找 API 端点
- 📖 **查看定义**: 获取完整的接口规范,包括请求/响应结构
- ➕ **创建接口**: 向 YApi 项目添加新的 API 定义
- ✏️ **更新接口**: 修改现有接口配置
- 🔐 **Cookie 认证**: 基于会话的安全认证
- ⚡ **异步性能**: 基于 httpx 实现高效的并发操作

## 环境要求

- Python 3.11 或更高版本
- YApi 1.12.0 实例(可通过 HTTP/HTTPS 访问)
- 有效的 YApi 认证 cookies

## 安装

### 使用 uvx(推荐)

[uvx](https://github.com/astral-sh/uv) 允许在不管理虚拟环境的情况下运行服务器:

```bash
# 如果未安装 uv,先安装
pip install uv

# 本地开发运行
uvx --from . yapi-mcp

# 或使用 uv run(自动管理虚拟环境)
uv run yapi-mcp
```

### 使用 pip

```bash
# 克隆仓库
git clone <repository-url>
cd yapi-mcp

# 安装依赖
pip install -e .

# 开发环境安装
pip install -e ".[dev]"
```

## 配置

### 1. 获取 YApi Cookies

1. 在浏览器中登录 YApi 实例
2. 打开开发者工具(F12)
3. 导航到 **Application** → **Cookies**(Chrome) 或 **Storage** → **Cookies**(Firefox)
4. 复制以下 cookie 值:
   - `_yapi_token` (必需)
   - `_yapi_uid` (必需)
   - `ZYBIPSCAS` (可选，仅某些自定义部署需要)

### 2. 设置环境变量

#### 方式 A: 环境变量

```bash
# Linux/macOS
export YAPI_SERVER_URL="https://your-yapi-instance.com"
export YAPI_TOKEN="your_yapi_token_value"
export YAPI_UID="your_uid_value"
# export YAPI_CAS="your_cas_value"  # 可选

# Windows (PowerShell)
$env:YAPI_SERVER_URL="https://your-yapi-instance.com"
$env:YAPI_TOKEN="your_yapi_token_value"
$env:YAPI_UID="your_uid_value"
# $env:YAPI_CAS="your_cas_value"  # 可选
```

#### 方式 B: .env 文件

在项目根目录创建 `.env` 文件(从 `.env.example` 复制):

```env
YAPI_SERVER_URL=https://your-yapi-instance.com
YAPI_TOKEN=your_yapi_token_value
YAPI_UID=your_yapi_uid_value
# YAPI_CAS=your_cas_value  # 可选，仅某些自定义部署需要
```

**⚠️ 安全提示**: 永远不要将 `.env` 文件提交到版本控制。该文件已在 `.gitignore` 中。

## 使用方法

### 启动服务器

```bash
# 使用 uvx(推荐)
uvx --from . yapi-mcp

# 使用 uv run(自动管理虚拟环境)
uv run yapi-mcp

# 开发模式(支持热重载)
uvx fastmcp dev src/server.py
```

服务器将在 stdio 传输上启动,并准备接受 MCP 工具调用。

### 可用的 MCP 工具

#### 1. `yapi_search_interfaces`

在 YApi 项目中搜索接口。

**参数**:
- `project_id` (int): YApi 项目 ID
- `keyword` (string): 搜索关键词(匹配标题、路径、描述)

**示例**:
```json
{
  "project_id": 123,
  "keyword": "login"
}
```

**返回**: 接口摘要的 JSON 数组(最多 50 条结果)

#### 2. `yapi_get_interface`

获取完整的接口定义。

**参数**:
- `interface_id` (int): YApi 接口 ID

**示例**:
```json
{
  "interface_id": 456
}
```

**返回**: 包含请求/响应结构的完整接口定义

#### 3. `yapi_create_interface`

在 YApi 项目中创建新接口。

**参数**:
- `project_id` (int): 项目 ID
- `title` (string): 接口标题
- `path` (string): 接口路径(必须以 `/` 开头)
- `method` (string): HTTP 方法(GET、POST、PUT、DELETE 等)
- `req_body` (string, 可选): 请求参数(JSON 字符串)
- `res_body` (string, 可选): 响应结构(JSON 字符串)
- `desc` (string, 可选): 接口描述

**示例**:
```json
{
  "project_id": 123,
  "title": "用户登录",
  "path": "/api/user/login",
  "method": "POST",
  "req_body": "{\"username\": \"string\", \"password\": \"string\"}",
  "res_body": "{\"token\": \"string\"}",
  "desc": "用户认证接口"
}
```

**返回**: `{"interface_id": <新接口ID>}`

#### 4. `yapi_update_interface`

更新现有接口(增量更新)。

**参数**:
- `interface_id` (int): 要更新的接口 ID
- `title` (string, 可选): 新标题
- `path` (string, 可选): 新路径
- `method` (string, 可选): 新 HTTP 方法
- `req_body` (string, 可选): 新请求参数
- `res_body` (string, 可选): 新响应结构
- `desc` (string, 可选): 新描述

**示例**:
```json
{
  "interface_id": 456,
  "title": "用户登录 V2"
}
```

**返回**: `{"success": true, "message": "接口更新成功"}`

### 错误处理

服务器将 HTTP/YApi 错误映射到 MCP 错误码:

| HTTP 状态码 | MCP 错误码 | 描述 |
|-------------|-----------|------|
| 401 | -32001 | 认证失败(无效/过期的 cookies) |
| 404 | -32002 | 资源不存在 |
| 403 | -32003 | 权限不足 |
| 500+ | -32000 | YApi 服务器错误 |
| 400 | -32602 | 参数无效 |

## IDE 集成

### Claude Code

添加到你的 `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "yapi": {
      "command": "uvx",
      "args": ["--from", "/path/to/yapi-mcp", "yapi-mcp"],
      "env": {
        "YAPI_SERVER_URL": "https://your-yapi-instance.com",
        "YAPI_TOKEN": "your_token",
        "YAPI_UID": "your_uid"
      }
    }
  }
}
```

> **注意**: 如果你的 YApi 部署需要额外的 CAS 认证，添加 `"YAPI_CAS": "your_cas_value"` 到 `env` 中。

### Cursor / 其他 MCP 客户端

参考你的 IDE 的 MCP 服务器配置文档。服务器默认使用 stdio 传输。

## 开发

### 运行测试

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行所有测试
pytest

# 运行并显示覆盖率
pytest --cov=src --cov-report=term-missing

# 运行特定测试文件
pytest tests/test_config.py
```

### 代码质量

```bash
# 格式化代码
ruff format

# 代码检查
ruff check

# 自动修复检查问题
ruff check --fix
```

### 项目结构

```
yapi-mcp/
├── src/
│   ├── server.py          # MCP 服务器入口点
│   ├── config.py          # 配置模型
│   ├── yapi/
│   │   ├── client.py      # YApi API 客户端
│   │   ├── models.py      # Pydantic 数据模型
│   │   └── errors.py      # 错误映射
│   └── tools/             # MCP 工具(在 server.py 中注册)
├── tests/                 # 测试套件
├── specs/                 # 设计文档
├── pyproject.toml         # 项目配置
├── .env.example           # 环境变量模板
└── README.md              # 本文件
```

## 故障排除

### 服务器无法启动

**问题**: `uvx: command not found`

**解决方案**: 安装 uv: `pip install uv`

---

**问题**: 启动时出现 `ValidationError`

**解决方案**: 验证所有必需的环境变量已设置:
```bash
# 检查必需的变量
echo $YAPI_SERVER_URL
echo $YAPI_TOKEN
echo $YAPI_UID
```

### 认证错误

**问题**: 所有请求返回 `-32001`(认证失败)

**解决方案**:
1. 验证 cookies 是否正确(无多余空格,完整值)
2. 检查 cookies 是否过期(重新登录 YApi 并获取新 cookies)
3. 确保 `YAPI_SERVER_URL` 正确(无尾部斜杠)

### 搜索返回空结果

**问题**: 搜索返回 `[]`,即使接口存在

**解决方案**:
1. 验证你有访问该项目的权限
2. 检查 `project_id` 是否正确
3. 尝试不同的关键词(某些 YApi 配置中匹配区分大小写)

### 导入错误

**问题**: `ModuleNotFoundError: No module named 'fastmcp'`

**解决方案**:
- 使用 uvx: 无需操作(自动管理依赖)
- 使用 pip: 运行 `pip install -e .` 或 `pip install fastmcp httpx pydantic-settings`

## 贡献

欢迎贡献! 我们非常感谢各种形式的贡献,包括但不限于:

- 🐛 报告 Bug
- ✨ 建议新功能
- 📝 改进文档
- 💻 提交代码

在开始贡献之前,请阅读我们的[贡献指南](CONTRIBUTING.md)。

### 快速开始

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'feat: 添加惊人的功能'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

### 代码质量要求

- ✅ 所有测试通过: `pytest`
- ✅ 代码已格式化: `ruff format`
- ✅ 无检查错误: `ruff check`
- ✅ 新功能包含测试

详细信息请参阅 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 相关项目

- [YApi](https://github.com/YMFE/yapi) - API 管理平台
- [fastmcp](https://github.com/jlowin/fastmcp) - Python MCP 框架
- [Model Context Protocol](https://modelcontextprotocol.io/) - MCP 规范
