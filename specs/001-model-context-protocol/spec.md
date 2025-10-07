# Feature Specification: YApi MCP Server

**Feature Branch**: `001-model-context-protocol`
**Created**: 2025-10-06
**Status**: Draft
**Input**: User description: "开发一个基于 Model Context Protocol 的服务器,专为 YApi 接口管理平台(版本: 1.12.0)设计,它可以搜索和查看 YApi 项目中的接口文档,创建和更新 接口定义。鉴权方式需要配置cookie(包括_yapi_token,_yapi_uid,ZYBIPSCAS)。"

## Execution Flow (main)
```
1. Parse user description from Input
   → Completed: MCP server for YApi interface management
2. Extract key concepts from description
   → Actors: Developers using IDE/editor with MCP support
   → Actions: Search interfaces, view interface docs, create/update interface definitions
   → Data: YApi interface specifications (requests, responses, parameters)
   → Constraints: YApi 1.12.0 compatibility, Cookie authentication
3. For each unclear aspect:
   → Marked in Functional Requirements section
4. Fill User Scenarios & Testing section
   → Completed: Primary developer workflow defined
5. Generate Functional Requirements
   → Completed: All requirements testable
6. Identify Key Entities (if data involved)
   → Completed: Interface, Project, Cookie Configuration
7. Run Review Checklist
   → Pending: Contains [NEEDS CLARIFICATION] markers
8. Return: WARN "Spec has uncertainties - clarification needed"
```

---

## ⚡ Quick Guidelines
- ✅ Focus on WHAT users need and WHY
- ❌ Avoid HOW to implement (no tech stack, APIs, code structure)
- 👥 Written for business stakeholders, not developers

---

## Clarifications

### Session 2025-10-06
- Q: YApi 服务器地址和项目 ID 如何配置? → A: 选项 B - 单个 YApi 实例,服务器地址配置在启动参数,项目 ID 由用户在请求时指定
- Q: 接口搜索需要支持哪些搜索条件和匹配方式? → A: 选项 C - 支持按接口标题、路径、描述进行模糊匹配
- Q: 搜索结果应包含哪些字段?是否需要限制返回数量? → A: 选项 C - 返回接口 ID、标题、路径、HTTP 方法,最多返回 50 条结果
- Q: 创建接口时的最小必填字段是什么? → A: 选项 C - 项目 ID、接口标题、路径、HTTP 方法、请求参数定义、响应定义
- Q: 接口更新操作支持全量更新还是增量更新? → A: 选项 B - 仅支持增量更新,可以只更新部分字段

---

## User Scenarios & Testing *(mandatory)*

### Primary User Story
开发人员在使用支持 MCP 的 IDE 或编辑器时,需要快速查找和查看 YApi 项目中的接口文档,无需离开编辑环境打开浏览器。当需要新增或修改接口定义时,可以直接在编辑器中完成这些操作,并同步到 YApi 平台。

### Acceptance Scenarios
1. **Given** 用户已配置 YApi 认证信息(cookie),**When** 用户在编辑器中搜索"用户登录接口"并指定项目 ID,**Then** 系统返回该项目中所有匹配的接口列表(最多 50 条),每条包含接口 ID、标题、路径、HTTP 方法
2. **Given** 用户选择了某个接口,**When** 用户请求查看完整接口文档,**Then** 系统显示该接口的完整定义(包括请求参数、响应结构、备注等)
3. **Given** 用户需要创建新接口,**When** 用户提供必填信息(项目 ID、标题、路径、HTTP 方法、请求参数结构、响应结构),**Then** 系统在 YApi 中创建该接口定义
4. **Given** 现有接口需要修改,**When** 用户提供接口 ID 和需要更新的字段(如修改标题或添加一个请求参数),**Then** 系统仅更新指定字段,其他字段保持不变

### Edge Cases
- 当用户的认证 cookie 过期或无效时,系统应当如何提示?
- 当 YApi 服务器无法访问时,系统应返回什么错误信息?
- 当搜索关键词匹配超过 50 个接口时,用户如何获取剩余结果?
- 当多个用户同时更新同一接口时,如何处理冲突?
- 当创建或更新接口的必填字段缺失时,系统应如何响应?

## Requirements *(mandatory)*

### Functional Requirements
- **FR-001**: 系统必须支持通过 Model Context Protocol 与客户端通信
- **FR-002**: 系统必须能够使用配置的 cookie 信息(_yapi_token, _yapi_uid, ZYBIPSCAS)与 YApi 1.12.0 进行认证
- **FR-003**: 用户必须能够在指定项目中搜索接口,搜索关键词对接口标题(title)、路径(path)、描述(desc)三个字段进行模糊匹配,返回任一字段包含关键词的接口列表
- **FR-004**: 用户必须能够查看接口的完整文档,包括请求方法、路径、请求参数、响应结构、状态码、接口描述等信息
- **FR-005**: 用户必须能够创建新的接口定义,最小必填字段包括:项目 ID、接口标题、路径、HTTP 方法、请求参数定义(可为空结构)、响应定义(可为空结构)
- **FR-006**: 用户必须能够增量更新现有接口定义,仅需提供接口 ID 和待修改的字段,未提供的字段保持原有值不变
- **FR-007**: 系统必须在认证失败时返回明确的错误信息
- **FR-008**: 系统必须处理 YApi 服务器不可用的情况并返回合适的错误提示
- **FR-009**: 系统必须验证接口操作的权限 [NEEDS CLARIFICATION: YApi 中是否有项目级别或接口级别的权限控制?如何判断用户是否有权限创建/更新接口?]
- **FR-010**: 系统必须在启动时接受单个 YApi 服务器地址配置,并在整个运行期间连接到该服务器
- **FR-011**: 用户必须在每次搜索、查看、创建或更新接口操作时指定目标项目 ID,系统不支持跨项目搜索
- **FR-012**: 搜索结果必须包含接口 ID、标题、路径、HTTP 方法四个字段,当匹配接口超过 50 条时仅返回前 50 条结果

### Key Entities

- **Interface (接口)**: YApi 中的 API 接口定义,必填属性包括接口 ID、标题、路径、HTTP 方法、请求参数定义(structure)、响应定义(structure)。可选属性包括描述、状态码、备注等。接口归属于特定项目。

- **Project (项目)**: YApi 中的项目概念,用于组织和管理一组相关的接口。包含项目 ID、项目名称等基本信息。

- **Cookie Configuration (Cookie 配置)**: 用户认证所需的 cookie 信息,包含三个必需字段:_yapi_token(认证令牌)、_yapi_uid(用户 ID)、ZYBIPSCAS(额外的认证标识)。

- **YApi Server (YApi 服务器)**: YApi 平台实例,包含服务器地址、版本信息等。系统在启动时配置单个服务器地址,运行期间不可更换。

- **Server Configuration (服务器配置)**: MCP 服务器的启动配置,包含 YApi 服务器地址和认证 cookie 信息。在启动参数或配置文件中定义。

---

## Review & Acceptance Checklist
*GATE: Automated checks run during main() execution*

### Content Quality
- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

### Requirement Completeness
- [ ] No [NEEDS CLARIFICATION] markers remain (1 clarification point remains: FR-009 权限验证机制)
- [x] Requirements are testable and unambiguous (除 FR-009 外)
- [ ] Success criteria are measurable (需补充具体的性能指标和可用性标准)
- [x] Scope is clearly bounded (限定在 YApi 接口的搜索、查看、创建、更新功能)
- [ ] Dependencies and assumptions identified (需补充 MCP 协议版本、YApi API 稳定性等假设)

---

## Execution Status
*Updated by main() during processing*

- [x] User description parsed
- [x] Key concepts extracted
- [x] Ambiguities marked (1 clarification point remaining)
- [x] User scenarios defined
- [x] Requirements generated
- [x] Entities identified
- [x] 5 critical clarifications resolved (2025-10-06 session)
- [ ] Review checklist passed (1 low-priority clarification deferred to planning phase)

---
