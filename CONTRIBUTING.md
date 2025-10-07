# 贡献指南

感谢你对 YApi MCP Server 项目的关注！我们欢迎各种形式的贡献。

## 行为准则

本项目采用了[贡献者行为准则](.github/CODE_OF_CONDUCT.md)。参与此项目即表示你同意遵守其条款。

## 如何贡献

### 报告 Bug

在提交 bug 报告之前：

1. 检查[现有 issues](https://github.com/YOUR_USERNAME/yapi-mcp/issues) 确保该问题尚未被报告
2. 确保你使用的是最新版本
3. 收集相关信息：Python 版本、操作系统、错误消息等

使用我们的 [Bug 报告模板](.github/ISSUE_TEMPLATE/bug_report.yml) 创建 issue。

### 建议新功能

使用我们的[功能请求模板](.github/ISSUE_TEMPLATE/feature_request.yml)提交功能建议。

### 提交代码

#### 开发环境设置

```bash
# 克隆仓库
git clone https://github.com/YOUR_USERNAME/yapi-mcp.git
cd yapi-mcp

# 安装开发依赖
pip install -e ".[dev]"

# 运行测试验证环境
pytest
```

#### 开发流程

1. **Fork 仓库**并克隆到本地
2. **创建功能分支**: `git checkout -b feature/amazing-feature`
3. **进行更改**:
   - 遵循现有代码风格
   - 添加必要的测试
   - 更新相关文档
4. **运行测试和检查**:
   ```bash
   # 运行所有测试
   pytest

   # 代码格式化
   ruff format src/ tests/

   # 代码检查
   ruff check src/ tests/
   ```
5. **提交更改**: `git commit -m "feat: 添加惊人的功能"`
6. **推送到 Fork**: `git push origin feature/amazing-feature`
7. **创建 Pull Request**

#### 提交消息规范

我们使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

```
<类型>(<范围>): <描述>

[可选的正文]

[可选的脚注]
```

类型包括：
- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式调整
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建/工具配置

示例：
```
feat(tools): 添加批量更新接口功能

实现了一次性更新多个接口的能力，提高操作效率。

Closes #123
```

#### 代码风格

- 遵循 PEP 8
- 使用 `ruff` 进行格式化和检查
- 函数和类必须有文档字符串
- 类型提示优先
- 保持函数简短（通常 < 50 行）

#### 测试要求

- 所有新功能必须包含测试
- Bug 修复应包含回归测试
- 保持测试覆盖率 > 80%
- 测试应该快速且独立

```bash
# 运行测试
pytest

# 运行特定测试
pytest tests/test_config.py

# 查看覆盖率
pytest --cov=src --cov-report=html
```

## 项目结构

```
yapi-mcp/
├── src/
│   ├── server.py          # MCP 服务器入口
│   ├── config.py          # 配置管理
│   ├── yapi/              # YApi API 客户端
│   └── tools/             # MCP 工具实现
├── tests/                 # 测试套件
├── specs/                 # 功能规范文档
└── .github/               # GitHub 配置
```

## Pull Request 流程

1. PR 应该针对单一目的（一个功能或一个 bug）
2. 确保 CI 检查全部通过
3. 更新相关文档
4. 请求代码审查
5. 响应审查意见
6. 等待维护者合并

## Pull Request 检查清单

在提交 PR 前，确认以下各项：

- [ ] 代码遵循项目风格指南
- [ ] 添加了必要的测试
- [ ] 所有测试通过
- [ ] 更新了相关文档
- [ ] 提交消息符合规范
- [ ] 代码已格式化（`ruff format`）
- [ ] 代码检查通过（`ruff check`）
- [ ] 没有破坏现有功能
- [ ] PR 描述清晰完整

## 开发工具

### 推荐的 IDE 配置

**VS Code**:
```json
{
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.formatting.provider": "none",
  "editor.formatOnSave": true,
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff"
  }
}
```

### 有用的命令

```bash
# 格式化所有代码
ruff format .

# 检查代码问题
ruff check .

# 自动修复可修复的问题
ruff check --fix .

# 运行测试并生成覆盖率报告
pytest --cov=src --cov-report=html

# 验证服务器配置
python validate_server.py
```

## 获取帮助

如果你在贡献过程中遇到问题：

1. 查看[文档](README.md)
2. 搜索[现有 issues](https://github.com/YOUR_USERNAME/yapi-mcp/issues)
3. 在[讨论区](https://github.com/YOUR_USERNAME/yapi-mcp/discussions)提问
4. 联系维护者

## 许可

提交代码即表示你同意你的贡献将按照项目的许可证进行授权。

---

再次感谢你的贡献！🎉
