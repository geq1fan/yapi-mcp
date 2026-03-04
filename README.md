# YApi MCP Server

[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

基于 [YApi 1.12.0](https://github.com/YMFE/yapi) 接口管理平台的 Model Context Protocol (MCP) 服务器。

使开发者能够在支持 MCP 的 IDE 和编辑器(Claude Code、Cursor 等)中直接搜索、查看、创建和更新 YApi 接口定义,无需离开开发环境。

## 功能特性

- 🔍 **搜索接口**: 通过标题、路径或描述查找 API 端点
- 📖 **查看定义**: 获取完整的接口规范,包括请求/响应结构
- ➕ **创建接口**: 向 YApi 项目添加新的 API 定义
- ✏️ **更新接口**: 增量更新现有接口配置(先读后写,仅修改传入字段)
- 🔐 **Cookie 认证**: 基于会话的安全认证
- ⚡ **异步性能**: 基于 httpx 实现高效的并发操作
- 🛡️ **启动验证**: 服务启动时自动校验 Cookie 有效性,失效时立即报错退出
- 📝 **Markdown 支持**: 接口描述支持 Markdown 格式,自动转换为 HTML

## MCP 工具

### `yapi_search_interfaces` — 搜索接口

在指定项目中通过关键词搜索接口(匹配标题/路径/描述)。

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `project_id` | int | ✅ | YApi 项目 ID |
| `keyword` | str | ✅ | 搜索关键词 |

返回: 接口摘要数组 JSON(`_id`, `title`, `path`, `method`)

---

### `yapi_get_interface` — 获取接口详情

获取单个接口的完整定义,包括请求/响应结构、描述等。

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `interface_id` | int | ✅ | 接口 ID |

返回: 完整接口对象 JSON

---

### `yapi_create_interface` — 创建接口

在 YApi 项目中创建新接口。

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `project_id` | int | ✅ | 项目 ID |
| `catid` | int | ✅ | 分类 ID |
| `title` | str | ✅ | 接口标题 |
| `path` | str | ✅ | 接口路径(以 `/` 开头) |
| `method` | str | ✅ | HTTP 方法(GET/POST/PUT/DELETE/PATCH/HEAD/OPTIONS) |
| `req_body` | str | — | 请求体(JSON Schema 字符串) |
| `req_body_type` | str | — | 请求体类型(`form`/`json`/`raw`/`file`) |
| `req_body_is_json_schema` | bool | — | 请求体是否为 JSON Schema 格式 |
| `req_body_form` | str | — | 表单字段(JSON 数组),示例: `[{"name":"x","type":"text","required":"1","desc":"说明"}]` |
| `req_query` | str | — | Query 参数(JSON 数组),示例: `[{"name":"page","required":"1","desc":"页码"}]` |
| `req_headers` | str | — | 请求头(JSON 数组),示例: `[{"name":"Authorization","value":"Bearer token","required":"1"}]` |
| `req_params` | str | — | 路径参数(JSON 数组),示例: `[{"name":"id","example":"123","desc":"用户ID"}]` |
| `res_body` | str | — | 响应体(JSON Schema 字符串) |
| `res_body_type` | str | — | 响应体类型(`json`/`raw`) |
| `res_body_is_json_schema` | bool | — | 响应体是否为 JSON Schema 格式 |
| `markdown` | str | — | 接口描述(Markdown 格式,自动转 HTML) |
| `status` | str | — | 接口状态(`undone`/`done`) |
| `tag` | str | — | 标签(JSON 数组) |
| `api_opened` | bool | — | 是否公开 API |

返回: `{"action": "created", "interface_id": <id>}`

---

### `yapi_update_interface` — 更新接口

增量更新接口定义。**仅需传入要修改的字段**,其余字段自动保留原值(先读后写)。

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `interface_id` | int | ✅ | 接口 ID |
| `title` | str | — | 新标题 |
| `path` | str | — | 新路径(以 `/` 开头) |
| `method` | str | — | 新 HTTP 方法 |
| `catid` | int | — | 新分类 ID |
| `req_body` | str | — | 请求体(JSON Schema) |
| `req_body_type` | str | — | 请求体类型 |
| `req_body_is_json_schema` | bool | — | 请求体是否为 JSON Schema 格式 |
| `req_body_form` | str | — | 表单字段(JSON 数组),示例: `[{"name":"x","type":"text","required":"1","desc":"说明"}]` |
| `req_query` | str | — | Query 参数(JSON 数组),示例: `[{"name":"page","required":"1","desc":"页码"}]` |
| `req_headers` | str | — | 请求头(JSON 数组),示例: `[{"name":"Authorization","value":"Bearer token","required":"1"}]` |
| `req_params` | str | — | 路径参数(JSON 数组),示例: `[{"name":"id","example":"123","desc":"用户ID"}]` |
| `res_body` | str | — | 响应体(JSON Schema) |
| `res_body_type` | str | — | 响应体类型 |
| `res_body_is_json_schema` | bool | — | 响应体是否为 JSON Schema 格式 |
| `markdown` | str | — | 接口描述(Markdown 格式) |
| `status` | str | — | 接口状态 |
| `tag` | str | — | 标签(JSON 数组) |
| `api_opened` | bool | — | 是否公开 API |
| `switch_notice` | bool | — | 是否通知团队成员 |
| `message` | str | — | 变更说明 |

返回: `{"action": "updated", "interface_id": <id>}`

## 环境要求

- Python 3.11 或更高版本
- YApi 1.12.0 实例(可通过 HTTP/HTTPS 访问)
- 有效的 YApi 认证 cookies

## 配置

### 1. 获取 YApi Cookies

1. 在浏览器中登录 YApi 实例
2. 打开开发者工具(F12)
3. 导航到 **Application** → **Cookies**(Chrome) 或 **Storage** → **Cookies**(Firefox)
4. 复制以下 cookie 值:
   - `_yapi_token` (必需)
   - `_yapi_uid` (必需)
   - `ZYBIPSCAS` (可选，仅某些自定义部署需要)

### 2. 配置 MCP

```json
{
  "mcpServers": {
    "yapi": {
      "command": "uvx",
      "args": ["yapi-mcp"],
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
│   └── yapi_mcp/          # Python 包
│       ├── server.py      # MCP 服务器入口 + 工具定义
│       ├── config.py      # 配置模型
│       └── yapi/
│           ├── client.py  # YApi API 客户端
│           ├── models.py  # Pydantic 数据模型
│           └── errors.py  # 错误映射
├── tests/                 # 测试套件
├── pyproject.toml         # 项目配置
├── .env.example           # 环境变量模板
└── README.md              # 本文件
```

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
