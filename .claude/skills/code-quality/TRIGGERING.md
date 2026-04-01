# Skill 触发机制完整说明

## 🎯 核心问题：Skill 如何被触发？

### 简短回答

**Skill 必须通过命令显式调用（使用 `/` 前缀），不会自动触发。**

例如：
- ✅ `/quality-check` - 显式调用 skill
- ❌ "帮我检查代码质量" - 不会自动触发 skill

---

## 📖 详细说明

### 1. Skill 的触发方式：显式命令调用

Claude Code 的 Skills 采用**命令式触发**机制，用户必须使用 `/` 前缀显式调用。

#### 为什么不自动触发？

1. **明确性**: 用户清楚知道何时使用了 skill
2. **可控性**: 避免不必要的 skill 执行
3. **性能**: 不需要在每次对话时扫描和匹配 skills
4. **设计哲学**: Skills 是用户主动调用的工具，而不是后台自动运行的服务

---

### 2. 如何使用 Skill

#### 基本语法

```bash
/command-name [参数]
```

#### 示例

```bash
# 调用 code-quality skill 的 check 命令
/quality-check

# 带参数调用
/quality-check main.py

# 多个参数
/quality-check --file=main.py --severity=high
```

---

### 3. Skill 命令的定义

在 `manifest.json` 中定义的每个命令都会成为一个可用的斜杠命令：

```json
{
  "commands": [
    {
      "name": "quality-check",     // 用户输入: /quality-check
      "description": "检查代码质量",
      "params": [...]
    },
    {
      "name": "quality-fix",       // 用户输入: /quality-fix
      "description": "修复代码问题",
      "params": [...]
    }
  ]
}
```

**命令名规则**:
- 使用小写字母
- 用 `-` 分隔单词（kebab-case）
- 不要使用空格或特殊字符
- 保持简洁易记

---

### 4. 工作流程：从输入到执行

```
用户输入 ──────────────────────────────────────────┐
  │                                                │
  │ /quality-check main.py                         │
  └──────────────────────────────────────────────▼

Claude Code 解析输入
  │
  ├─ 识别 `/` 前缀 → 这是一个 skill 命令
  ├─ 提取命令名: quality-check
  ├─ 提取参数: main.py
  └─ 查找对应的 skill

加载 Skill 配置
  │
  ├─ 读取 manifest.json
  ├─ 找到 quality-check 命令
  └─ 加载对应的 prompt 文件: quality-check.prompt.md

构建 AI 提示
  │
  ├─ 系统提示: quality-check.prompt.md 的内容
  ├─ 用户输入: main.py
  └─ 上下文信息: 当前项目、文件路径等

执行 AI 处理
  │
  ├─ Claude AI 根据 prompt 理解任务
  ├─ 使用工具读取文件 (Read tool)
  ├─ 分析代码
  └─ 生成检查报告

返回结果给用户 ◀───────────────────────────────────┘
```

---

### 5. 与普通对话的区别

#### 普通对话（无 skill）

```
用户: "帮我检查 main.py 的代码质量"
Claude: 基于通用知识回答，可能不够专业或遗漏细节
```

#### 使用 Skill（显式调用）

```
用户: "/quality-check main.py"
Claude:
  1. 加载专门的 quality-check.prompt.md
  2. 按照预定义的检查规则执行
  3. 生成结构化的专业报告
```

**优势**:
- ✅ 更专业的检查规则
- ✅ 一致的输出格式
- ✅ 可配置的行为
- ✅ 可复用的流程

---

### 6. 如何让 Skill "看起来像自动触发"

虽然 skills 不能真正自动触发，但可以通过以下方式改善体验：

#### 方法 1: 在文档中提示用户

```markdown
# 项目 README.md

## 代码检查

在提交代码前，请运行：
\```bash
/quality-check
\```
```

#### 方法 2: 使用 Git Hooks 自动提示

创建 `.git/hooks/pre-commit`:

```bash
#!/bin/bash
echo ""
echo "💡 提示: 建议运行代码质量检查"
echo "   claude /quality-check"
echo ""
```

#### 方法 3: 在 CI/CD 中集成

```yaml
# .github/workflows/code-quality.yml
name: Code Quality Check

on: [push, pull_request]

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run quality check
        run: |
          claude /quality-check --format=json > report.json
          # 解析报告，如果有严重问题则失败
```

#### 方法 4: 创建包装脚本

```bash
# check-code.sh
#!/bin/bash
echo "🔍 运行代码质量检查..."
claude <<EOF
/quality-check $@
EOF
```

然后：
```bash
./check-code.sh main.py
```

---

### 7. Skill 的上下文感知

虽然 skill 需要显式调用，但它们**可以访问会话上下文**：

```
用户: "我正在开发一个 Python Flask API"
Claude: "好的，我了解了"

用户: "/quality-check"
Claude: [加载 quality-check.prompt.md]
        [可以看到之前的对话：这是一个 Flask API 项目]
        [针对 Flask API 进行特定检查：路由安全、错误处理等]
```

**这意味着**:
- ✅ Skill 能理解之前的对话
- ✅ 可以根据项目类型调整检查
- ✅ 不需要每次都重复说明上下文

---

### 8. 查看可用的 Skills

```bash
# 在 Claude Code 中输入
/help

# 或列出所有可用命令
/<TAB>  # 按 Tab 键自动补全

# 查看 skill 详情
/quality-check --help
```

---

### 9. Skill 的最佳实践

#### ✅ 好的命令名

- `/quality-check` - 清晰、专业
- `/fix-errors` - 动作明确
- `/security-scan` - 描述准确

#### ❌ 不好的命名

- `/qc` - 太简短，不直观
- `/check_code_quality` - 使用下划线，不符合规范
- `/do-stuff` - 不明确

#### ✅ 好的 Skill 设计

```json
{
  "commands": [
    {
      "name": "quality-check",
      "description": "检查代码质量问题",  // 清晰的描述
      "params": [
        {
          "name": "file",
          "description": "文件路径（可选）",  // 参数说明
          "required": false
        }
      ]
    }
  ]
}
```

---

### 10. 常见问题 FAQ

#### Q: 能否让 Claude 自动判断何时使用 skill？

**A**: 目前不支持。Skills 必须通过 `/command` 显式调用。

但你可以：
- 在项目 README 中提示用户使用 skill
- 在 CI/CD 中自动运行 skill
- 培养团队习惯：提交前运行 `/quality-check`

#### Q: 能否创建快捷键触发 skill？

**A**: 取决于你的编辑器。例如在 VSCode 中可以配置：

```json
{
  "key": "ctrl+shift+q",
  "command": "claudeCode.runSkill",
  "args": {
    "skill": "quality-check"
  }
}
```

#### Q: Skill 能否在后台持续运行？

**A**: 不能。Skills 是按需执行的命令，不是常驻服务。

如果需要持续监控，考虑：
- 使用文件监听工具（如 watchman）
- 配置编辑器的保存钩子
- 使用 LSP（Language Server Protocol）

#### Q: 全局 skill 和项目 skill 冲突怎么办？

**A**: 项目 skill 优先级更高。

```
项目 .claude/skills/my-skill  (优先)
  vs
全局 ~/.claude/skills/my-skill  (被覆盖)
```

---

### 11. 总结：Skill 触发机制

| 特性 | 说明 |
|------|------|
| **触发方式** | 显式命令（`/command`） |
| **自动触发** | ❌ 不支持 |
| **上下文感知** | ✅ 可以访问对话历史 |
| **参数传递** | ✅ 支持命令行参数 |
| **全局可用** | ✅ 用户级 skills 在所有项目可用 |
| **优先级** | 项目级 > 用户级 > Marketplace |

---

### 12. 实用技巧

#### 创建快速访问别名

在项目的 `.clauderc` 或说明中：

```markdown
## 常用命令

- 质量检查: `/quality-check`
- 修复问题: `/quality-fix`
- 查看配置: `/quality-config`

提示：可以简写参数，例如 `/quality-check main.py`
```

#### 结合 Hooks 使用

```bash
# .git/hooks/pre-commit
#!/bin/bash

echo "运行代码质量检查..."
if ! claude --print "/quality-check" | grep -q "0 严重问题"; then
    echo "❌ 发现代码质量问题，请先修复"
    exit 1
fi
```

---

希望这份文档解答了你关于 skill 触发机制的所有疑问！简单来说：**必须使用 `/command` 显式调用，但可以通过各种方式（文档、hooks、CI）来促进使用。**
