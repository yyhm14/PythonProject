# Code Quality Skill - 升级和部署完整指南

## 🎉 恭喜！你的 Skill 已升级完成

### 升级内容总结

| 项目 | 原版本 | 新版本 |
|------|--------|--------|
| **语言支持** | 仅 Python | Python, JavaScript, TypeScript, Java, Go, Rust, C#, PHP, Ruby |
| **命令系统** | `/check`, `/fix` | `/quality-check`, `/quality-fix`, `/quality-config` |
| **检查规则** | 飞书项目专用 | 通用 + 语言特定规则 |
| **配置支持** | 无 | 支持 `.code-quality.json` 配置文件 |
| **部署方式** | 手动 | 自动化脚本（PowerShell + Bash） |
| **文档** | 基础 | 完整（部署、触发机制、发布指南） |

---

## 📂 新的文件结构

```
.claude/skills/
├── code-quality/                      # 原版本（项目特定）
│   ├── manifest.json
│   ├── check.prompt.md
│   ├── fix.prompt.md
│   ├── README.md
│   ├── QUICKSTART.md
│   │
│   ├── manifest-v2.json               # 🆕 通用化配置
│   ├── quality-check.prompt.md        # 🆕 通用检查规则
│   ├── DEPLOYMENT.md                  # 🆕 部署指南
│   ├── TRIGGERING.md                  # 🆕 触发机制说明
│   └── QUICKSTART.md
│
├── deploy.ps1                         # 🆕 Windows 部署脚本
└── deploy.sh                          # 🆕 Linux/macOS 部署脚本
```

---

## 🚀 立即开始使用

### 选项 1: 快速部署到全局（推荐）

#### Windows:

```powershell
# 切换到 skills 目录
cd .claude\skills

# 运行部署脚本
.\deploy.ps1

# 或强制覆盖已存在的安装
.\deploy.ps1 -Force
```

#### macOS/Linux:

```bash
# 切换到 skills 目录
cd .claude/skills

# 添加执行权限
chmod +x deploy.sh

# 运行部署脚本
./deploy.sh

# 或强制覆盖
./deploy.sh --force
```

### 选项 2: 手动部署

#### Windows (PowerShell):

```powershell
$source = ".claude\skills\code-quality"
$target = "$env:USERPROFILE\.claude\skills\code-quality"

# 创建目录
New-Item -ItemType Directory -Force -Path $target

# 复制文件
Copy-Item "$source\*" $target -Recurse -Force

Write-Host "✅ 部署完成！"
```

#### macOS/Linux:

```bash
# 创建目录
mkdir -p ~/.claude/skills/code-quality

# 复制文件
cp -r .claude/skills/code-quality/* ~/.claude/skills/code-quality/

echo "✅ 部署完成！"
```

---

## 🎯 验证部署

### 步骤 1: 切换到任意项目

```bash
cd /path/to/another/project
```

### 步骤 2: 启动 Claude Code

```bash
claude
```

### 步骤 3: 测试 Skill

```bash
# 在 Claude Code 中输入
/quality-check

# 或检查特定文件
/quality-check src/main.py
```

如果看到代码质量检查报告，说明部署成功！

---

## 📖 核心概念回顾

### 1. Skill 触发机制

**重要**: Skills 必须使用 `/` 命令显式调用，**不会自动触发**。

```bash
✅ /quality-check               # 正确：显式调用
❌ "帮我检查代码质量"           # 错误：不会触发 skill
```

**为什么不自动触发？**
- 明确性：用户清楚知道何时使用了 skill
- 可控性：避免不必要的执行
- 性能：不需要每次对话都扫描 skills

详见：[TRIGGERING.md](.claude/skills/code-quality/TRIGGERING.md)

---

### 2. Skill 的三种部署方式

| 方式 | 位置 | 作用域 | 使用场景 |
|------|------|--------|----------|
| **项目级** | `.claude/skills/` | 仅当前项目 | 项目特定规则 |
| **用户级** | `~/.claude/skills/` | 所有项目 | 个人常用工具 |
| **Marketplace** | 远程仓库 | 社区共享 | 公开发布 |

详见：[DEPLOYMENT.md](.claude/skills/code-quality/DEPLOYMENT.md)

---

### 3. 如何发布你的 Skill

#### 步骤 1: 创建 GitHub 仓库

```bash
# 创建新仓库
mkdir code-quality-checker
cd code-quality-checker

# 初始化
git init
```

#### 步骤 2: 组织目录结构

```
code-quality-checker/
├── .claude-plugin/
│   └── plugin.json          # Marketplace 元数据
├── skills/
│   └── code-quality/
│       ├── manifest.json
│       ├── *.prompt.md
│       └── README.md
├── README.md
└── LICENSE
```

#### 步骤 3: 创建 `.claude-plugin/plugin.json`

```json
{
  "name": "code-quality-checker",
  "version": "2.0.0",
  "description": "通用代码质量检查工具",
  "author": "weichao13",
  "skills": [
    {
      "name": "code-quality",
      "path": "skills/code-quality",
      "version": "2.0.0"
    }
  ]
}
```

#### 步骤 4: 推送到 GitHub

```bash
git add .
git commit -m "Initial release v2.0.0"
git tag v2.0.0
git push origin main --tags
```

#### 步骤 5: 发布到 Marketplace

**选项 A: 创建自己的 Marketplace**

```bash
# 添加你的 marketplace
claude plugin marketplace add my-skills https://github.com/weichao13/my-marketplace

# 安装 skill
claude plugin install code-quality-checker@my-skills
```

**选项 B: 贡献到官方 Marketplace**

1. Fork `anthropics/skills` 仓库
2. 添加你的 skill 到 `plugins/` 目录
3. 提交 Pull Request
4. 等待审核通过

详见：[DEPLOYMENT.md](.claude/skills/code-quality/DEPLOYMENT.md) 的完整发布指南

---

## 🎓 关键知识点

### Q1: Skill 能自动识别和触发吗？

**A**: ❌ 不能。必须使用 `/command` 显式调用。

但可以通过以下方式改善体验：
- 在 README 中提示使用
- Git hooks 自动提醒
- CI/CD 自动运行
- 创建快捷键（编辑器配置）

### Q2: 全局 skill 在所有项目都生效吗？

**A**: ✅ 是的。部署到 `~/.claude/skills/` 的 skill 在所有项目中都可用。

### Q3: 项目 skill 和全局 skill 冲突怎么办？

**A**: 项目级 skill 优先级更高，会覆盖全局同名 skill。

```
优先级: 项目级 > 用户级 > Marketplace
```

### Q4: 如何分享 skill 给团队？

**A**: 三种方式：

1. **项目级部署**（推荐新手）
   ```bash
   # 将 .claude/skills/ 提交到 Git
   git add .claude/skills/
   git commit -m "Add code quality skill"
   git push
   ```

2. **内部 Marketplace**
   - 创建团队 GitHub 仓库
   - 团队成员添加 marketplace
   - 统一安装和更新

3. **公开发布**
   - 发布到 GitHub
   - 贡献到官方 marketplace
   - 社区共享

---

## 📊 使用统计和最佳实践

### 推荐工作流

1. **开发阶段**: 在项目 `.claude/skills/` 中开发和测试
2. **个人使用**: 部署到 `~/.claude/skills/` 全局使用
3. **团队分享**: 提交到项目 Git 或创建 marketplace
4. **公开发布**: 贡献到官方 marketplace

### 常用命令速查

```bash
# 检查代码质量
/quality-check                    # 整个项目
/quality-check main.py            # 特定文件
/quality-check --severity=high    # 只显示严重问题

# 修复代码问题
/quality-fix main.py              # 修复所有问题
/quality-fix main.py --issue_type=logging  # 只修复日志问题

# 配置 skill
/quality-config                   # 查看当前配置
/quality-config --action=init     # 生成配置文件
```

### 性能优化

- 大项目建议指定文件而非全项目扫描
- 使用 `.code-quality.json` 排除不需要检查的目录
- 调整严重级别过滤器减少输出

---

## 📚 完整文档索引

| 文档 | 内容 | 位置 |
|------|------|------|
| **README.md** | Skill 功能和使用方法 | `.claude/skills/code-quality/` |
| **QUICKSTART.md** | 快速开始和实战演练 | `.claude/skills/code-quality/` |
| **DEPLOYMENT.md** | 部署、发布、安装完整指南 | `.claude/skills/code-quality/` |
| **TRIGGERING.md** | Skill 触发机制详解 | `.claude/skills/code-quality/` |
| **manifest-v2.json** | 通用化配置文件 | `.claude/skills/code-quality/` |
| **quality-check.prompt.md** | 多语言检查规则 | `.claude/skills/code-quality/` |

---

## 🎯 下一步行动

1. **立即部署到全局**
   ```bash
   cd .claude/skills
   ./deploy.sh  # 或 .\deploy.ps1 (Windows)
   ```

2. **验证部署**
   ```bash
   cd /path/to/another/project
   claude
   # 输入: /quality-check
   ```

3. **阅读完整文档**
   - [DEPLOYMENT.md](.claude/skills/code-quality/DEPLOYMENT.md) - 了解发布流程
   - [TRIGGERING.md](.claude/skills/code-quality/TRIGGERING.md) - 深入理解触发机制

4. **（可选）发布到 GitHub**
   - 创建公开仓库
   - 分享给社区

---

## 🙏 学习成果

通过这次实践，你学会了：

✅ Claude Code Skill 的完整开发流程
✅ 项目级、用户级、Marketplace 三种部署方式
✅ Skill 的触发机制和限制
✅ 如何发布和分享 skill
✅ 通用化 skill 的设计（支持多语言）
✅ 自动化部署脚本的编写

---

## 💬 反馈和改进

如有问题或建议：
- 在项目中创建 issue
- 或提交 pull request

祝你使用愉快！🚀
