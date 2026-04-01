# Skill 部署、发布和安装完整指南

## 📍 Skill 的三种部署方式

### 1. 项目级别部署（Project-scoped）

**位置**: `.claude/skills/` 目录中

**特点**:
- ✅ 只在当前项目中生效
- ✅ 可以针对项目特点定制
- ✅ 与项目代码一起版本控制

**使用场景**: 项目特定的检查规则

```bash
YourProject/
├── .claude/
│   └── skills/
│       └── code-quality/
│           ├── manifest.json
│           ├── quality-check.prompt.md
│           └── README.md
├── src/
└── README.md
```

**创建方式**:
```bash
cd YourProject
mkdir -p .claude/skills/my-skill
# 创建 manifest.json 和 prompt 文件
```

---

### 2. 用户级别部署（User-scoped）- **推荐用于全局使用**

**位置**: Claude Code 的用户配置目录

**Windows**:
```
C:\Users\{username}\AppData\Local\claude-code\skills\
或
C:\Users\{username}\.claude\skills\
```

**macOS/Linux**:
```
~/.config/claude-code/skills/
或
~/.claude/skills/
```

**特点**:
- ✅ 所有项目都可以使用
- ✅ 不随项目移动
- ✅ 适合通用工具

**创建方式**:

#### Windows (PowerShell):
```powershell
# 方法 1: 使用 AppData
$skillDir = "$env:LOCALAPPDATA\claude-code\skills\code-quality"
New-Item -ItemType Directory -Force -Path $skillDir

# 方法 2: 使用 .claude
$skillDir = "$env:USERPROFILE\.claude\skills\code-quality"
New-Item -ItemType Directory -Force -Path $skillDir

# 复制 skill 文件
Copy-Item .\code-quality\* $skillDir -Recurse
```

#### macOS/Linux (Bash):
```bash
# 创建目录
mkdir -p ~/.config/claude-code/skills/code-quality

# 或者
mkdir -p ~/.claude/skills/code-quality

# 复制 skill 文件
cp -r ./code-quality/* ~/.claude/skills/code-quality/
```

---

### 3. 通过 Marketplace 发布和安装（推荐的分享方式）

**特点**:
- ✅ 一行命令安装
- ✅ 自动更新
- ✅ 版本管理
- ✅ 社区分享

---

## 🚀 如何发布你的 Skill 到 Marketplace

### 步骤 1: 准备 Skill 的 GitHub 仓库

1. **创建 GitHub 仓库**

```bash
# 在 GitHub 上创建新仓库 code-quality-checker
# 然后克隆到本地
git clone https://github.com/your-username/code-quality-checker.git
cd code-quality-checker
```

2. **组织目录结构**

Marketplace skill 需要特定的目录结构：

```
code-quality-checker/
├── .claude-plugin/
│   └── plugin.json         # 插件元数据（必需）
├── skills/
│   └── code-quality/
│       ├── manifest.json
│       ├── quality-check.prompt.md
│       ├── quality-fix.prompt.md
│       └── quality-config.prompt.md
├── README.md
├── LICENSE
└── CHANGELOG.md
```

3. **创建 `.claude-plugin/plugin.json`**

这是 Marketplace 识别插件的关键文件：

```json
{
  "name": "code-quality-checker",
  "version": "2.0.0",
  "description": "通用代码质量检查工具 - 支持多种编程语言",
  "author": "weichao13",
  "homepage": "https://github.com/weichao13/code-quality-checker",
  "repository": {
    "type": "git",
    "url": "https://github.com/weichao13/code-quality-checker.git"
  },
  "license": "MIT",
  "keywords": [
    "code-quality",
    "linter",
    "error-handling",
    "logging",
    "best-practices"
  ],
  "skills": [
    {
      "name": "code-quality",
      "path": "skills/code-quality",
      "version": "2.0.0"
    }
  ],
  "dependencies": {},
  "compatibleWith": {
    "claudeCode": ">=0.2.0"
  }
}
```

4. **编写好的 README.md**

```markdown
# Code Quality Checker - Claude Code Skill

A comprehensive code quality checking tool for multiple programming languages.

## Features

- ✅ Multi-language support (Python, JavaScript, TypeScript, Java, Go, etc.)
- ✅ Error handling checks
- ✅ Logging completeness
- ✅ Code duplication detection
- ✅ Auto-fix capabilities

## Installation

\```bash
claude plugin install code-quality-checker@your-marketplace
\```

## Usage

\```bash
# Check code quality
/quality-check

# Check specific file
/quality-check main.py

# Auto-fix issues
/quality-fix main.py
\```

## Configuration

Create `.code-quality.json` in your project root...

## License

MIT
```

5. **提交到 GitHub**

```bash
git add .
git commit -m "Initial release v2.0.0"
git tag v2.0.0
git push origin main --tags
```

---

### 步骤 2: 创建自己的 Marketplace 或贡献到官方 Marketplace

#### 选项 A: 创建自己的 Marketplace（推荐学习）

1. **创建 Marketplace 仓库**

```bash
# 创建名为 my-claude-skills 的仓库
mkdir my-claude-skills
cd my-claude-skills
```

2. **创建 Marketplace 配置**

创建 `.claude-plugin/marketplace.json`:

```json
{
  "name": "weichao13-skills",
  "version": "1.0.0",
  "description": "weichao13's custom Claude Code skills",
  "author": "weichao13",
  "homepage": "https://github.com/weichao13/my-claude-skills",
  "plugins": [
    {
      "name": "code-quality-checker",
      "description": "Code quality checking tool",
      "repository": "https://github.com/weichao13/code-quality-checker",
      "version": "2.0.0",
      "author": "weichao13"
    },
    {
      "name": "another-skill",
      "description": "Another awesome skill",
      "repository": "https://github.com/weichao13/another-skill",
      "version": "1.0.0",
      "author": "weichao13"
    }
  ]
}
```

3. **推送到 GitHub**

```bash
git init
git add .
git commit -m "Create marketplace"
git remote add origin https://github.com/weichao13/my-claude-skills.git
git push -u origin main
```

4. **添加到 Claude Code**

```bash
# 添加你的 marketplace
claude plugin marketplace add weichao13-skills https://github.com/weichao13/my-claude-skills

# 查看 marketplace
claude plugin marketplace list

# 从你的 marketplace 安装 skill
claude plugin install code-quality-checker@weichao13-skills
```

---

#### 选项 B: 贡献到官方 Marketplace（推荐分享）

1. **Fork 官方仓库**

```bash
# Fork anthropics/skills 或 anthropics/claude-plugins-official
# 然后克隆你的 fork
git clone https://github.com/your-username/skills.git
cd skills
```

2. **添加你的 skill**

在 `plugins/` 目录下添加你的 skill 信息：

```bash
# 编辑或创建 plugins/code-quality-checker.json
{
  "name": "code-quality-checker",
  "description": "Code quality checking tool",
  "repository": "https://github.com/weichao13/code-quality-checker",
  "version": "2.0.0",
  "author": "weichao13",
  "homepage": "https://github.com/weichao13/code-quality-checker",
  "keywords": ["code-quality", "linter"]
}
```

3. **提交 Pull Request**

```bash
git checkout -b add-code-quality-checker
git add .
git commit -m "Add code-quality-checker skill"
git push origin add-code-quality-checker

# 在 GitHub 上创建 PR
```

4. **等待审核**

Anthropic 团队会审核你的 PR，通过后，其他用户就可以通过官方 marketplace 安装你的 skill！

---

## 📥 如何安装他人的 Skill

### 方法 1: 从 Marketplace 安装（推荐）

```bash
# 列出所有可用的 skills
claude plugin list --available

# 从默认 marketplace 安装
claude plugin install code-quality-checker

# 从指定 marketplace 安装
claude plugin install code-quality-checker@anthropic-agent-skills

# 安装特定版本
claude plugin install code-quality-checker@2.0.0
```

### 方法 2: 从 GitHub 直接安装

```bash
# 使用 GitHub URL 安装
claude plugin install https://github.com/weichao13/code-quality-checker

# 或指定分支/标签
claude plugin install https://github.com/weichao13/code-quality-checker#v2.0.0
```

### 方法 3: 手动安装（本地开发）

```bash
# 克隆仓库
git clone https://github.com/someone/awesome-skill.git

# 复制到用户 skill 目录
cp -r awesome-skill/skills/* ~/.claude/skills/

# 或使用符号链接（开发时方便）
ln -s /path/to/awesome-skill/skills/awesome ~/.claude/skills/awesome
```

---

## 🔧 管理已安装的 Skills

```bash
# 列出已安装的 skills
claude plugin list

# 查看 skill 详情
claude plugin info code-quality-checker

# 更新 skill
claude plugin update code-quality-checker

# 禁用 skill（不卸载）
claude plugin disable code-quality-checker

# 启用 skill
claude plugin enable code-quality-checker

# 卸载 skill
claude plugin uninstall code-quality-checker
```

---

## 🎯 实战：部署你的 code-quality skill 到全局

### 快速部署（仅本地使用）

**Windows (PowerShell)**:
```powershell
# 创建全局 skill 目录
$globalSkillDir = "$env:USERPROFILE\.claude\skills\code-quality"
New-Item -ItemType Directory -Force -Path $globalSkillDir

# 复制当前项目的 skill 文件到全局目录
$projectSkillDir = ".claude\skills\code-quality"
Copy-Item "$projectSkillDir\*" $globalSkillDir -Recurse -Force

Write-Host "✅ Skill 已部署到全局: $globalSkillDir"
Write-Host "现在可以在任何项目中使用 /quality-check 命令了！"
```

**macOS/Linux**:
```bash
# 创建全局 skill 目录
mkdir -p ~/.claude/skills/code-quality

# 复制 skill 文件
cp -r .claude/skills/code-quality/* ~/.claude/skills/code-quality/

echo "✅ Skill 已部署到全局: ~/.claude/skills/code-quality"
echo "现在可以在任何项目中使用 /quality-check 命令了！"
```

### 验证部署

```bash
# 切换到另一个项目目录
cd /path/to/another/project

# 运行 Claude Code
claude

# 在 Claude Code 中测试
/quality-check
```

---

## 📚 推荐的项目结构（用于发布）

```
code-quality-checker/                # 仓库根目录
├── .claude-plugin/
│   └── plugin.json                  # Marketplace 元数据
├── skills/
│   └── code-quality/                # Skill 目录
│       ├── manifest.json            # Skill 配置
│       ├── quality-check.prompt.md  # 检查命令
│       ├── quality-fix.prompt.md    # 修复命令
│       └── quality-config.prompt.md # 配置命令
├── docs/
│   ├── usage.md                     # 使用文档
│   └── configuration.md             # 配置文档
├── examples/
│   ├── python-example/              # 示例项目
│   └── javascript-example/
├── tests/
│   └── test-files/                  # 测试用例
├── .gitignore
├── README.md                        # 主文档
├── CHANGELOG.md                     # 版本历史
├── LICENSE                          # 许可证（MIT 推荐）
└── CONTRIBUTING.md                  # 贡献指南
```

---

## 🔍 总结

| 部署方式 | 位置 | 适用场景 | 命令 |
|---------|------|---------|------|
| **项目级别** | `.claude/skills/` | 项目特定规则 | 直接在项目中创建 |
| **用户级别** | `~/.claude/skills/` | 个人全局使用 | 复制到用户目录 |
| **Marketplace** | 远程仓库 | 公开分享 | `claude plugin install` |

### 推荐工作流

1. **开发阶段**: 在项目的 `.claude/skills/` 中开发和测试
2. **个人使用**: 复制到 `~/.claude/skills/` 全局使用
3. **分享阶段**: 发布到 GitHub + 创建 marketplace

---

下一步，我会为你创建一个自动化部署脚本和 skill 触发机制说明！
