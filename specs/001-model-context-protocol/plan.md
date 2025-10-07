
# Implementation Plan: YApi MCP Server

**Branch**: `001-model-context-protocol` | **Date**: 2025-10-06 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `C:\Users\Ge\Documents\github\yapi-mcp\specs\001-model-context-protocol\spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → If not found: ERROR "No feature spec at {path}"
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → Detect Project Type from file system structure or context (web=frontend+backend, mobile=app+api)
   → Set Structure Decision based on project type
3. Fill the Constitution Check section based on the content of the constitution document.
4. Evaluate Constitution Check section below
   → If violations exist: Document in Complexity Tracking
   → If no justification possible: ERROR "Simplify approach first"
   → Update Progress Tracking: Initial Constitution Check
5. Execute Phase 0 → research.md
   → If NEEDS CLARIFICATION remain: ERROR "Resolve unknowns"
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, agent-specific template file (e.g., `CLAUDE.md` for Claude Code, `.github/copilot-instructions.md` for GitHub Copilot, `GEMINI.md` for Gemini CLI, `QWEN.md` for Qwen Code, or `AGENTS.md` for all other agents).
7. Re-evaluate Constitution Check section
   → If new violations: Refactor design, return to Phase 1
   → Update Progress Tracking: Post-Design Constitution Check
8. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)
9. STOP - Ready for /tasks command
```

**IMPORTANT**: The /plan command STOPS at step 7. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary
构建一个基于 Model Context Protocol (MCP) 的服务器,为 YApi 1.12.0 接口管理平台提供编程访问能力。开发者可在支持 MCP 的 IDE/编辑器中直接搜索、查看、创建和更新 YApi 接口定义,无需离开编辑环境。服务器通过 Cookie 鉴权(_yapi_token, _yapi_uid, ZYBIPSCAS)与 YApi 通信,支持单服务器实例配置,用户操作时指定项目 ID。

## Technical Context
**Language/Version**: Python 3.11+
**Primary Dependencies**: fastmcp 2.0+, httpx 0.27+, pydantic-settings 2.0+
**Storage**: N/A (无状态服务器,仅转发请求到 YApi API)
**Testing**: pytest + pytest-asyncio + respx (HTTP mocking)
**Target Platform**: 跨平台 (Windows/macOS/Linux),通过 uvx 运行
**Project Type**: single (单体 Python MCP 服务器)
**Performance Goals**: <500ms 响应延迟(受 YApi API 性能限制), 支持 10 个并发请求(httpx 异步)
**Constraints**:
- 必须符合 MCP 协议规范
- YApi 1.12.0 API 兼容性
- Cookie 会话管理(无自动刷新,依赖外部配置)
- 使用 uvx 部署,无需虚拟环境
**Scale/Scope**:
- 4 个核心操作(搜索、查看、创建、更新接口)
- 单用户使用场景(每个服务器实例绑定一个 Cookie 配置)
- 搜索结果最多 50 条(规格限制)

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

由于项目 constitution 文件为空模板,基于通用软件工程原则进行检查:

| 原则 | 检查项 | 状态 |
|------|--------|------|
| **简单性** | MCP 协议本身定义清晰,无需额外抽象层 | ✅ PASS |
| **单一职责** | 服务器职责明确:MCP 协议适配器 + YApi API 客户端 | ✅ PASS |
| **无状态设计** | 服务器不维护会话状态,Cookie 由配置提供 | ✅ PASS |
| **测试先行** | 需在 Phase 1 生成合约测试框架 | ⚠️ PENDING |
| **错误处理** | 需明确定义 YApi API 错误到 MCP 错误的映射 | ⚠️ PENDING |
| **文档完整性** | 需生成 quickstart.md 和 API contracts | ⚠️ PENDING |

**初步结论**: ✅ 通过初始检查,无架构级别违规。待 Phase 1 设计完成后重新评估。

## Project Structure

### Documentation (this feature)
```
specs/[###-feature]/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
src/
├── server.py              # MCP 服务器入口(fastmcp)
├── config.py              # 配置模型(Pydantic)
├── yapi/                  # YApi API 客户端
│   ├── client.py         # httpx 异步客户端
│   ├── models.py         # Pydantic 数据模型
│   └── errors.py         # 错误映射
└── tools/                 # MCP tools 实现
    ├── search.py
    ├── get.py
    ├── create.py
    └── update.py

tests/
├── test_tools.py          # MCP tools 测试(fastmcp Client)
├── test_yapi_client.py    # YApi 客户端测试(respx mock)
└── test_config.py         # 配置验证测试

pyproject.toml             # Python 项目配置(或 requirements.txt)
.env.example               # 环境变量示例
README.md                  # 项目文档
```

**Structure Decision**: 选择单体 Python 项目结构。fastmcp 服务器本质是独立进程,无 frontend/backend 分离需求。按职责分层:MCP tools 层、YApi 客户端层、配置层。使用 uvx 运行,无需传统虚拟环境。

## Phase 0: Outline & Research
1. **Extract unknowns from Technical Context** above:
   - For each NEEDS CLARIFICATION → research task
   - For each dependency → best practices task
   - For each integration → patterns task

2. **Generate and dispatch research agents**:
   ```
   For each unknown in Technical Context:
     Task: "Research {unknown} for {feature context}"
   For each technology choice:
     Task: "Find best practices for {tech} in {domain}"
   ```

3. **Consolidate findings** in `research.md` using format:
   - Decision: [what was chosen]
   - Rationale: [why chosen]
   - Alternatives considered: [what else evaluated]

**Output**: research.md with all NEEDS CLARIFICATION resolved

## Phase 1: Design & Contracts
*Prerequisites: research.md complete*

1. **Extract entities from feature spec** → `data-model.md`:
   - Entity name, fields, relationships
   - Validation rules from requirements
   - State transitions if applicable

2. **Generate API contracts** from functional requirements:
   - For each user action → endpoint
   - Use standard REST/GraphQL patterns
   - Output OpenAPI/GraphQL schema to `/contracts/`

3. **Generate contract tests** from contracts:
   - One test file per endpoint
   - Assert request/response schemas
   - Tests must fail (no implementation yet)

4. **Extract test scenarios** from user stories:
   - Each story → integration test scenario
   - Quickstart test = story validation steps

5. **Update agent file incrementally** (O(1) operation):
   - Run `.specify/scripts/powershell/update-agent-context.ps1 -AgentType claude`
     **IMPORTANT**: Execute it exactly as specified above. Do not add or remove any arguments.
   - If exists: Add only NEW tech from current plan
   - Preserve manual additions between markers
   - Update recent changes (keep last 3)
   - Keep under 150 lines for token efficiency
   - Output to repository root

**Output**: data-model.md, /contracts/*, failing tests, quickstart.md, agent-specific file

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
1. **Load base template**: `.specify/templates/tasks-template.md`
2. **Generate from Phase 1 artifacts**:
   - `data-model.md` → 配置管理任务
   - `contracts/mcp-tools.schema.json` → 4 个 MCP Tool 合约测试任务
   - `quickstart.md` → 集成测试场景任务
   - `research.md` → YApi API 客户端任务

**Task Breakdown** (预览):

### Setup & Configuration (Tasks 1-3)
1. 初始化 TypeScript 项目结构(`package.json`, `tsconfig.json`)
2. 实现配置加载模块(`src/config/schema.ts`)
3. 编写配置验证单元测试 [P]

### Contract Tests (Tasks 4-7) [TDD Phase 1]
4. 编写 `yapi_search_interfaces` 合约测试 [P]
5. 编写 `yapi_get_interface` 合约测试 [P]
6. 编写 `yapi_create_interface` 合约测试 [P]
7. 编写 `yapi_update_interface` 合约测试 [P]

### YApi Client Layer (Tasks 8-11) [Implementation Phase 1]
8. 实现 YApi HTTP 客户端基础类(`src/yapi/client.ts`)
9. 实现搜索接口 API 调用
10. 实现获取/创建/更新接口 API 调用
11. 实现错误映射逻辑(`src/yapi/errors.ts`)

### Integration Tests (Tasks 12-15) [TDD Phase 2]
12. 编写 YApi 客户端集成测试(Mock HTTP) [P]
13. 编写认证失败场景测试 [P]
14. 编写资源不存在场景测试 [P]
15. 编写服务器错误场景测试 [P]

### MCP Server Layer (Tasks 16-20) [Implementation Phase 2]
16. 初始化 MCP Server 实例(`src/mcp/server.ts`)
17. 注册 4 个 MCP Tools 并绑定 handlers
18. 实现 Tool handlers(调用 YApi 客户端)
19. 实现 MCP 错误响应封装
20. 实现 StdioServerTransport 连接

### Quickstart Validation (Tasks 21-25) [TDD Phase 3]
21. 手动执行 quickstart.md Test 1(搜索接口)
22. 手动执行 quickstart.md Test 2(获取详情)
23. 手动执行 quickstart.md Test 3(创建接口)
24. 手动执行 quickstart.md Test 4(更新接口)
25. 手动执行 quickstart.md Test 5(错误处理)

### Documentation & Polish (Tasks 26-28)
26. 编写 README.md(安装、配置、使用说明)
27. 生成 API 文档(TypeDoc)
28. 代码 linting 和格式化(ESLint + Prettier)

**Ordering Strategy**:
- **TDD 顺序**: 先写测试(Tasks 4-7, 12-15),再写实现(Tasks 8-11, 16-20)
- **依赖顺序**: 配置 → YApi 客户端 → MCP 服务器
- **并行标记 [P]**: 合约测试(4-7)和集成测试(12-15)可并行编写
- **Quickstart 测试**: 在所有实现完成后手动执行

**Estimated Output**: 28 个任务,按 TDD 循环组织

**Critical Path**:
```
Config (1-3) → Contract Tests (4-7) → YApi Client (8-11) →
Integration Tests (12-15) → MCP Server (16-20) → Quickstart (21-25)
```

**IMPORTANT**: Phase 2 由 `/tasks` 命令执行,当前 `/plan` 命令仅描述策略,不生成 tasks.md

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)  
**Phase 4**: Implementation (execute tasks.md following constitutional principles)  
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking
*Fill ONLY if Constitution Check has violations that must be justified*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |


## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command) - ✅ research.md generated
- [x] Phase 1: Design complete (/plan command) - ✅ data-model.md, contracts/, quickstart.md, CLAUDE.md generated
- [x] Phase 2: Task planning complete (/plan command - describe approach only) - ✅ 28-task strategy documented
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS (简单性、单一职责、无状态设计)
- [x] Post-Design Constitution Check: PASS (无架构违规)
- [x] All NEEDS CLARIFICATION resolved (语言选择 TypeScript,依赖确定,YApi API 细节留待实现时确认)
- [x] Complexity deviations documented (无,架构简单)

---
*Based on Constitution v2.1.1 - See `/memory/constitution.md`*
