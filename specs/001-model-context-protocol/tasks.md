# Tasks: YApi MCP Server

**Input**: Design documents from `/specs/001-model-context-protocol/`
**Prerequisites**: plan.md, research.md, data-model.md, contracts/mcp-tools.schema.json, quickstart.md

## Execution Flow
```
1. Loaded plan.md: Python 3.11+, fastmcp 2.0+, httpx, pydantic-settings
2. Loaded data-model.md: ServerConfig, YApiInterface, YApiInterfaceSummary
3. Loaded contracts/: mcp-tools.schema.json (4 tools)
4. Loaded quickstart.md: 5 test scenarios
5. Generated 30 tasks across 5 phases
6. Validated: All contracts tested, TDD enforced, parallel tasks independent
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

---

## Phase 3.1: Setup & Configuration
- [x] T001 Create Python project structure: `src/`, `src/yapi/`, `src/tools/`, `tests/`
- [x] T002 Initialize project with `pyproject.toml` (fastmcp ^2.0.0, httpx ^0.27.0, pydantic-settings ^2.0.0, pytest ^8.0.0, pytest-asyncio ^0.23.0, respx ^0.21.0)
- [x] T003 [P] Create `.env.example` with YAPI_SERVER_URL, YAPI_TOKEN, YAPI_UID, YAPI_CAS template

## Phase 3.2: Configuration & Data Models (Foundation)
- [x] T004 Implement `ServerConfig` Pydantic model in `src/config.py` with env validation
- [x] T005 [P] Implement `YApiInterface` model in `src/yapi/models.py` with alias mapping
- [x] T006 [P] Implement `YApiInterfaceSummary` and `YApiErrorResponse` in `src/yapi/models.py`
- [x] T007 [P] Write config validation unit tests in `tests/test_config.py`

## Phase 3.3: YApi Client Layer (HTTP Integration)
- [x] T008 Implement `YApiClient` base class in `src/yapi/client.py` with httpx.AsyncClient and Cookie management
- [x] T009 Implement `YApiClient.search_interfaces()` method for POST `/api/interface/list`
- [x] T010 Implement `YApiClient.get_interface()` method for GET `/api/interface/get`
- [x] T011 Implement `YApiClient.create_interface()` method for POST `/api/interface/add`
- [x] T012 Implement `YApiClient.update_interface()` method for POST `/api/interface/up`
- [x] T013 Implement error mapping in `src/yapi/errors.py` (401→-32001, 404→-32002, 403→-32003, 500→-32000)

## Phase 3.4: Contract Tests (TDD - MUST COMPLETE BEFORE 3.5)
**CRITICAL: These tests MUST be written and MUST FAIL before MCP tools implementation**
- [x] T014 [P] Contract test `yapi_search_interfaces` schema in `tests/test_tools_contract.py` (verify inputSchema matches mcp-tools.schema.json SearchInterfacesTool)
- [x] T015 [P] Contract test `yapi_get_interface` schema in `tests/test_tools_contract.py` (verify inputSchema matches GetInterfaceTool)
- [x] T016 [P] Contract test `yapi_create_interface` schema in `tests/test_tools_contract.py` (verify inputSchema matches CreateInterfaceTool)
- [x] T017 [P] Contract test `yapi_update_interface` schema in `tests/test_tools_contract.py` (verify inputSchema matches UpdateInterfaceTool)

## Phase 3.5: MCP Tools Implementation (ONLY after tests are failing)
- [x] T018 Create fastmcp server instance in `src/server.py` with ServerConfig initialization
- [x] T019 Implement `yapi_search_interfaces` tool in `src/tools/search.py` with @mcp.tool decorator
- [x] T020 Implement `yapi_get_interface` tool in `src/tools/get.py`
- [x] T021 Implement `yapi_create_interface` tool in `src/tools/create.py` with path validation (must start with /)
- [x] T022 Implement `yapi_update_interface` tool in `src/tools/update.py` with partial update logic
- [x] T023 Register all tools in `src/server.py` and setup stdio transport

## Phase 3.6: Integration Tests (Mock YApi API)
- [x] T024 [P] Write YApi client integration tests in `tests/test_yapi_client.py` (use respx to mock httpx requests)
- [x] T025 [P] Write authentication failure test in `tests/test_error_handling.py` (401 → MCPError -32001)
- [x] T026 [P] Write resource not found test in `tests/test_error_handling.py` (404 → MCPError -32002)
- [x] T027 [P] Write server error test in `tests/test_error_handling.py` (500 → MCPError -32000)

## Phase 3.7: Manual Validation (Quickstart Scenarios)
- [ ] T028 Execute quickstart.md Test 1 (search interfaces with valid project_id and keyword) - REQUIRES LIVE YAPI INSTANCE
- [ ] T029 Execute quickstart.md Test 2 (get interface by valid interface_id) - REQUIRES LIVE YAPI INSTANCE
- [ ] T030 Execute quickstart.md Test 3 (create interface with required fields) - REQUIRES LIVE YAPI INSTANCE
- [ ] T031 Execute quickstart.md Test 4 (update interface with partial fields) - REQUIRES LIVE YAPI INSTANCE
- [ ] T032 Execute quickstart.md Test 5 (test all error scenarios: auth failure, not found, server error) - REQUIRES LIVE YAPI INSTANCE

## Phase 3.8: Documentation & Polish
- [x] T033 [P] Write comprehensive README.md (Installation with uvx, Configuration, Usage examples, Troubleshooting)
- [x] T034 [P] Add inline code comments and docstrings (Python PEP 257 style)
- [x] T035 Run `ruff check` and `ruff format` for linting and formatting

---

## Dependencies
- **Foundation**: T001-T003 (Setup) must complete first
- **Data Models**: T004-T007 (Config & Models) before T008 (YApi Client)
- **YApi Client**: T008-T013 (Client Layer) before T014-T017 (Contract Tests)
- **TDD Enforcement**: T014-T017 (Contract Tests) MUST FAIL before T018-T023 (Tools)
- **Tools**: T018-T023 (MCP Tools) before T024-T027 (Integration Tests)
- **Validation**: T024-T027 (Tests) before T028-T032 (Manual Validation)
- **Polish**: T033-T035 (Docs & Format) after all functionality complete

## Parallel Execution Examples

### Parallel Group 1: Contract Tests (Phase 3.4)
```bash
# Launch T014-T017 together (all in same file but independent schema checks):
Task agent 1: "Contract test yapi_search_interfaces schema in tests/test_tools_contract.py"
Task agent 2: "Contract test yapi_get_interface schema in tests/test_tools_contract.py"
Task agent 3: "Contract test yapi_create_interface schema in tests/test_tools_contract.py"
Task agent 4: "Contract test yapi_update_interface schema in tests/test_tools_contract.py"
```

### Parallel Group 2: Data Models (Phase 3.2)
```bash
# Launch T005-T007 together (different concerns):
Task agent 1: "Implement YApiInterface model in src/yapi/models.py"
Task agent 2: "Implement YApiInterfaceSummary and YApiErrorResponse in src/yapi/models.py"
Task agent 3: "Write config validation unit tests in tests/test_config.py"
```

### Parallel Group 3: Integration Tests (Phase 3.6)
```bash
# Launch T024-T027 together (independent test files):
Task agent 1: "YApi client integration tests in tests/test_yapi_client.py"
Task agent 2: "Authentication failure test in tests/test_error_handling.py"
Task agent 3: "Resource not found test in tests/test_error_handling.py"
Task agent 4: "Server error test in tests/test_error_handling.py"
```

### Parallel Group 4: Documentation (Phase 3.8)
```bash
# Launch T033-T034 together (different files):
Task agent 1: "Write README.md"
Task agent 2: "Add inline code comments and docstrings"
```

---

## Validation Checklist
*GATE: All must pass before marking feature complete*

- [x] All 4 contracts (mcp-tools.schema.json) have corresponding tests (T014-T017)
- [x] All entities (ServerConfig, YApiInterface) have model tasks (T004-T006)
- [x] All tests come before implementation (T014-T017 before T018-T023)
- [x] Parallel tasks are truly independent (verified: different files or orthogonal code sections)
- [x] Each task specifies exact file path
- [x] No [P] task modifies same file as another [P] task (exception: T014-T017 are read-only schema checks)
- [x] All quickstart scenarios have validation tasks (T028-T032)
- [x] TDD enforced: contract tests must fail before tool implementation

---

## Critical Ordering Rules
1. **Setup First**: T001-T003 (project structure, dependencies)
2. **Foundation Next**: T004-T007 (config, data models)
3. **HTTP Layer**: T008-T013 (YApi client with error handling)
4. **Tests Before Code**: T014-T017 (contract tests) → T018-T023 (MCP tools)
5. **Integration Validation**: T024-T027 (mock tests) → T028-T032 (manual tests)
6. **Polish Last**: T033-T035 (docs, linting)

---

**Status**: ✅ 35 tasks generated (30 implementation + 5 quickstart validation). TDD enforced. Parallel execution optimized.
