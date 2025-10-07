# GitHub Actions 工作流

本目录包含项目的 CI/CD 配置。

## 工作流说明

### CI 工作流 (ci.yml)

**触发条件**: 推送到 main/master/develop 分支，或针对这些分支的 Pull Request

**包含三个作业**:

#### 1. Test (测试)
- **矩阵策略**:
  - Python 版本: 3.11, 3.12, 3.13
  - 操作系统: Ubuntu, Windows, macOS
- **步骤**:
  - 检出代码
  - 设置 Python 环境
  - 安装依赖
  - 运行测试套件（pytest）
  - 生成覆盖率报告
  - 上传到 Codecov（仅 Ubuntu + Python 3.11）

#### 2. Lint (代码质量检查)
- **运行环境**: Ubuntu + Python 3.11
- **步骤**:
  - 代码格式检查 (`ruff format --check`)
  - 代码质量检查 (`ruff check`)

#### 3. Validate (服务器验证)
- **运行环境**: Ubuntu + Python 3.11
- **步骤**:
  - 验证 MCP 服务器可以正确导入和初始化
  - 确认所有 4 个 MCP 工具已注册

### Release 工作流 (release.yml)

**触发条件**: 创建 GitHub Release

**包含作业**:

#### 1. Build (构建分发包)
- 构建 wheel 和 sdist 包
- 上传构建产物到 GitHub

#### 2. Publish to PyPI (发布到 PyPI)
- **状态**: 当前已注释（需配置后启用）
- **要求**:
  - 配置 PyPI Trusted Publisher
  - 设置 GitHub Environment

**启用 PyPI 发布的步骤**:
1. 在 PyPI 上创建项目
2. 配置 GitHub Actions 作为 Trusted Publisher
3. 取消注释 release.yml 中的 publish-pypi 作业

## Dependabot

**配置文件**: `dependabot.yml`

自动检查并创建 PR 更新依赖：
- **Python 依赖**: 每周检查
- **GitHub Actions**: 每周检查

## 状态徽章

在 README.md 中添加以下徽章显示 CI 状态：

```markdown
[![CI](https://github.com/YOUR_USERNAME/yapi-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR_USERNAME/yapi-mcp/actions/workflows/ci.yml)
```

**注意**: 将 `YOUR_USERNAME` 替换为实际的 GitHub 用户名或组织名。

## 本地运行 CI 检查

在提交前，你可以在本地运行相同的检查：

```bash
# 运行测试
pytest tests/ -v --cov=src --cov-report=term-missing

# 代码格式检查
ruff format --check src/ tests/

# 代码质量检查
ruff check src/ tests/

# 验证服务器
python validate_server.py
```

## 配置 Codecov (可选)

1. 访问 [codecov.io](https://codecov.io/)
2. 授权 GitHub 并添加仓库
3. 复制 Codecov token
4. 在 GitHub 仓库设置中添加 Secret: `CODECOV_TOKEN`
5. 在 README 中添加覆盖率徽章:
   ```markdown
   [![codecov](https://codecov.io/gh/YOUR_USERNAME/yapi-mcp/branch/main/graph/badge.svg)](https://codecov.io/gh/YOUR_USERNAME/yapi-mcp)
   ```

## 故障排除

### CI 失败常见原因

1. **测试失败**
   - 本地运行 `pytest` 确认测试通过
   - 检查是否有环境相关的依赖问题

2. **格式检查失败**
   - 运行 `ruff format src/ tests/` 修复格式问题

3. **代码检查失败**
   - 运行 `ruff check --fix src/ tests/` 自动修复部分问题
   - 手动修复剩余问题

4. **服务器验证失败**
   - 确保所有导入路径正确
   - 检查 MCP 工具装饰器是否正确应用

### Windows 特定问题

如果 Windows 测试失败而其他平台通过：
- 检查路径分隔符（使用 `pathlib` 而非字符串拼接）
- 确保文本文件使用 `\r\n` 换行符

### macOS 特定问题

如果 macOS 测试失败：
- 可能是依赖安装问题
- 检查是否需要额外的系统依赖

## 性能优化

当前配置已经过优化：
- ✅ 使用 pip 缓存加速依赖安装
- ✅ fail-fast: false 允许所有矩阵作业完成
- ✅ 并行运行测试矩阵

如果 CI 运行时间过长，考虑：
- 减少测试矩阵维度
- 使用更快的测试运行器
- 缓存更多构建产物
