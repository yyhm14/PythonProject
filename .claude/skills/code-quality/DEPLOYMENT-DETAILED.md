# Skill 全局部署详细指南

## 📍 什么是全局部署？

### 部署位置对比

| 部署方式 | 路径 | 作用范围 |
|---------|------|---------|
| **项目级** | `项目目录/.claude/skills/` | ❌ 仅当前项目可用 |
| **全局级** | `~/.claude/skills/` 或 `C:\Users\你的用户名\.claude\skills\` | ✅ **所有项目都可用** |

### 为什么要全局部署？

```
部署前：
项目A/.claude/skills/code-quality  ✅ 可用
项目B/                              ❌ 不可用
项目C/                              ❌ 不可用

部署后：
~/.claude/skills/code-quality       ← 全局安装
  ├─ 项目A/                         ✅ 可用
  ├─ 项目B/                         ✅ 可用
  └─ 项目C/                         ✅ 可用
```

---

## 🗂️ 全局 Skill 的具体位置

### Windows 系统

Claude Code 会在以下位置查找全局 skills（按优先级）：

1. **优先位置**（推荐）：
   ```
   C:\Users\你的用户名\.claude\skills\
   ```

2. **备选位置**：
   ```
   C:\Users\你的用户名\AppData\Local\claude-code\skills\
   ```

3. **另一个备选位置**：
   ```
   C:\Users\你的用户名\AppData\Roaming\claude-code\skills\
   ```

**推荐使用第 1 个位置**（`~/.claude/skills/`），因为：
- ✅ 路径简短，易于管理
- ✅ 符合 Unix 风格，跨平台一致
- ✅ 官方文档推荐

### macOS/Linux 系统

```
/Users/你的用户名/.claude/skills/           (macOS)
/home/你的用户名/.claude/skills/             (Linux)
```

简写为：`~/.claude/skills/`

---

## 🚀 部署方法详解

### 方法 1: 自动化脚本部署（⭐ 最推荐）

这是最简单、最安全的方法！

#### Windows 用户

**步骤 1: 打开 PowerShell**

- 按 `Win + X`，选择 "Windows PowerShell" 或 "终端"
- 或在开始菜单搜索 "PowerShell"

**步骤 2: 切换到项目目录**

```powershell
# 切换到你的项目目录
cd C:\Users\weichao13\PycharmProjects\PythonProject

# 验证当前目录
pwd
# 输出应该是: C:\Users\weichao13\PycharmProjects\PythonProject
```

**步骤 3: 进入 skills 目录**

```powershell
cd .claude\skills

# 验证 deploy.ps1 存在
ls deploy.ps1
```

**步骤 4: 运行部署脚本**

```powershell
# 运行部署脚本
.\deploy.ps1

# 如果已经部署过，想要覆盖，使用：
.\deploy.ps1 -Force
```

**步骤 5: 查看输出**

你会看到类似这样的输出：

```
================================================
   Code Quality Skill - 全局部署工具
================================================

ℹ️  检查源目录...
✅ 源文件检查通过
ℹ️  创建目标目录...
✅ 目录创建成功: C:\Users\weichao13\.claude\skills\code-quality
ℹ️  复制 skill 文件...
✅ 文件复制完成
ℹ️  验证部署...
  已部署 8 个文件:
    - manifest.json
    - quality-check.prompt.md
    - quality-fix.prompt.md
    - README.md
    ...

================================================
✅ 部署成功！
================================================

ℹ️  Skill 已部署到全局目录，现在可以在任何项目中使用：

  /quality-check          # 检查代码质量
  /quality-fix <file>     # 修复代码问题
  /quality-config         # 配置检查规则

ℹ️  测试部署:
  1. 打开任意项目
  2. 运行 claude
  3. 输入 /quality-check

需要卸载时，运行:
  .\deploy.ps1 -Uninstall
```

---

#### macOS/Linux 用户

**步骤 1: 打开终端**

- macOS: `Cmd + Space`，输入 "Terminal"
- Linux: `Ctrl + Alt + T`

**步骤 2: 切换到项目目录**

```bash
# 切换到你的项目目录
cd /c/Users/weichao13/PycharmProjects/PythonProject

# 验证当前目录
pwd
```

**步骤 3: 进入 skills 目录**

```bash
cd .claude/skills

# 验证 deploy.sh 存在
ls -l deploy.sh
```

**步骤 4: 添加执行权限（首次需要）**

```bash
chmod +x deploy.sh

# 验证权限
ls -l deploy.sh
# 应该看到 -rwxr-xr-x（带 x 表示可执行）
```

**步骤 5: 运行部署脚本**

```bash
# 运行部署脚本
./deploy.sh

# 如果已经部署过，想要覆盖，使用：
./deploy.sh --force
```

**输出示例**：

```
================================================
   Code Quality Skill - 全局部署工具
================================================

ℹ️  检查源目录...
✅ 源文件检查通过
ℹ️  创建目标目录...
✅ 目录创建成功: /home/weichao13/.claude/skills/code-quality
ℹ️  复制 skill 文件...
✅ 文件复制完成
ℹ️  验证部署...
  已部署 8 个文件:
    - manifest.json
    - quality-check.prompt.md
    ...

================================================
✅ 部署成功！
================================================
```

---

### 方法 2: 手动部署（备用方案）

如果自动脚本不工作，可以手动复制文件。

#### Windows 手动部署

**步骤 1: 打开文件资源管理器**

- 按 `Win + E`

**步骤 2: 定位源文件夹**

在地址栏输入：
```
C:\Users\weichao13\PycharmProjects\PythonProject\.claude\skills\code-quality
```

**步骤 3: 复制整个 code-quality 文件夹**

- 右键点击 `code-quality` 文件夹
- 选择 "复制"

**步骤 4: 创建目标目录**

在地址栏输入：
```
%USERPROFILE%\.claude\skills
```

如果 `.claude` 文件夹不存在：
- 右键空白处 → 新建 → 文件夹
- 命名为 `.claude`（注意有点号）
- 进入 `.claude` 文件夹
- 创建 `skills` 文件夹

**步骤 5: 粘贴**

- 在 `skills` 文件夹中右键 → 粘贴
- 现在应该有：`C:\Users\weichao13\.claude\skills\code-quality\`

**步骤 6: 验证**

在 PowerShell 中运行：
```powershell
ls $env:USERPROFILE\.claude\skills\code-quality

# 应该看到：
# manifest.json
# quality-check.prompt.md
# ...
```

---

#### macOS/Linux 手动部署

**使用命令行**：

```bash
# 步骤 1: 创建目标目录
mkdir -p ~/.claude/skills

# 步骤 2: 复制文件
cp -r .claude/skills/code-quality ~/.claude/skills/

# 步骤 3: 验证
ls -la ~/.claude/skills/code-quality

# 应该看到：
# manifest.json
# quality-check.prompt.md
# ...
```

---

## ✅ 验证部署成功

### 方法 1: 检查文件是否存在

**Windows (PowerShell)**:
```powershell
# 检查目录
Test-Path "$env:USERPROFILE\.claude\skills\code-quality"
# 应该输出: True

# 列出文件
ls $env:USERPROFILE\.claude\skills\code-quality

# 应该看到：
# manifest.json
# quality-check.prompt.md
# quality-fix.prompt.md
# README.md
# ...
```

**macOS/Linux (Bash)**:
```bash
# 检查目录
ls -la ~/.claude/skills/code-quality

# 应该看到所有文件
```

---

### 方法 2: 在任意项目中测试

**步骤 1: 切换到不同的项目**

```bash
# 切换到完全不同的目录
cd /d D:\other-project      # Windows
cd ~/other-project           # macOS/Linux
```

**步骤 2: 启动 Claude Code**

```bash
claude
```

**步骤 3: 测试 Skill**

在 Claude Code 中输入：
```
/quality-check
```

**预期结果**：

如果部署成功，Claude 会：
1. 识别 `/quality-check` 命令
2. 加载 skill 的 prompt
3. 开始检查代码质量

**如果失败**：
```
❌ Unknown command: /quality-check
```

说明部署未成功，继续查看下面的故障排除。

---

## 🔍 故障排除

### 问题 1: 脚本执行被阻止（Windows）

**错误信息**：
```
.\deploy.ps1 : 无法加载文件，因为在此系统上禁止运行脚本
```

**解决方案**：

```powershell
# 临时允许运行脚本（推荐）
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# 然后再运行
.\deploy.ps1
```

或者直接绕过：
```powershell
powershell -ExecutionPolicy Bypass -File .\deploy.ps1
```

---

### 问题 2: 目录已存在

**错误信息**：
```
⚠️  目标目录已存在: ...
是否覆盖？(y/N)
```

**解决方案**：

输入 `y` 覆盖，或使用 `-Force` 参数：
```powershell
.\deploy.ps1 -Force           # Windows
./deploy.sh --force           # macOS/Linux
```

---

### 问题 3: 找不到源文件

**错误信息**：
```
❌ 源目录不存在
```

**解决方案**：

确保你在正确的目录：
```powershell
# 检查当前目录
pwd

# 应该在 .claude/skills 目录
# 例如: C:\...\PythonProject\.claude\skills
```

如果不在，切换到正确目录：
```powershell
cd C:\Users\weichao13\PycharmProjects\PythonProject\.claude\skills
```

---

### 问题 4: Skill 部署了但识别不到

**检查步骤**：

1. **确认文件位置正确**：
   ```powershell
   # Windows
   ls $env:USERPROFILE\.claude\skills\code-quality\manifest.json

   # macOS/Linux
   ls ~/.claude/skills/code-quality/manifest.json
   ```

2. **检查 manifest.json 格式**：
   ```powershell
   # 查看内容
   cat $env:USERPROFILE\.claude\skills\code-quality\manifest.json
   ```

   确保是有效的 JSON 格式。

3. **重启 Claude Code**：
   ```bash
   # 退出当前会话
   exit

   # 重新启动
   claude
   ```

4. **检查 Claude Code 版本**：
   ```bash
   claude --version

   # 确保版本 >= 0.2.0
   ```

---

### 问题 5: 权限问题（Linux/macOS）

**错误信息**：
```
Permission denied
```

**解决方案**：

```bash
# 添加写权限
chmod -R u+w ~/.claude/skills/

# 或使用 sudo（不推荐，除非必要）
sudo cp -r .claude/skills/code-quality ~/.claude/skills/
```

---

## 🗑️ 卸载全局 Skill

### 使用脚本卸载（推荐）

**Windows**:
```powershell
cd .claude\skills
.\deploy.ps1 -Uninstall
```

**macOS/Linux**:
```bash
cd .claude/skills
./deploy.sh --uninstall
```

---

### 手动卸载

**Windows (PowerShell)**:
```powershell
# 删除整个 skill 目录
Remove-Item -Recurse -Force "$env:USERPROFILE\.claude\skills\code-quality"

# 验证已删除
Test-Path "$env:USERPROFILE\.claude\skills\code-quality"
# 应该输出: False
```

**macOS/Linux**:
```bash
# 删除整个 skill 目录
rm -rf ~/.claude/skills/code-quality

# 验证已删除
ls ~/.claude/skills/code-quality
# 应该输出: No such file or directory
```

---

## 📊 部署前后对比

### 部署前

```
当前项目 ✅
  └─ .claude/skills/code-quality/
      ├─ manifest.json
      ├─ *.prompt.md
      └─ README.md

其他项目 ❌
  (没有 code-quality skill)
```

**使用情况**：
- 在当前项目：`/quality-check` ✅ 可用
- 在其他项目：`/quality-check` ❌ 不可用

---

### 部署后

```
全局位置 🌍
  ~/.claude/skills/code-quality/
      ├─ manifest.json
      ├─ *.prompt.md
      └─ README.md

任意项目A ✅
任意项目B ✅
任意项目C ✅
```

**使用情况**：
- 在任意项目：`/quality-check` ✅ **全部可用**

---

## 🎯 实际操作演示

让我为你演示完整的部署和测试流程：

### 完整演示脚本（Windows）

```powershell
# ===== 第 1 步: 准备 =====
Write-Host "📍 第 1 步: 进入项目目录" -ForegroundColor Cyan
cd C:\Users\weichao13\PycharmProjects\PythonProject\.claude\skills
pwd

# ===== 第 2 步: 部署 =====
Write-Host "`n🚀 第 2 步: 运行部署脚本" -ForegroundColor Cyan
.\deploy.ps1

# ===== 第 3 步: 验证部署 =====
Write-Host "`n✅ 第 3 步: 验证部署" -ForegroundColor Cyan
$deployed = Test-Path "$env:USERPROFILE\.claude\skills\code-quality\manifest.json"
if ($deployed) {
    Write-Host "✅ 部署成功！文件已复制到全局目录" -ForegroundColor Green
    ls "$env:USERPROFILE\.claude\skills\code-quality"
} else {
    Write-Host "❌ 部署失败！请检查错误信息" -ForegroundColor Red
}

# ===== 第 4 步: 测试 =====
Write-Host "`n🧪 第 4 步: 切换到其他项目测试" -ForegroundColor Cyan
cd C:\Users\weichao13\Documents  # 切换到不同目录
Write-Host "当前目录: $(pwd)"
Write-Host "`n现在运行: claude" -ForegroundColor Yellow
Write-Host "然后输入: /quality-check" -ForegroundColor Yellow
```

### 完整演示脚本（macOS/Linux）

```bash
#!/bin/bash

# 颜色定义
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# ===== 第 1 步: 准备 =====
echo -e "${CYAN}📍 第 1 步: 进入项目目录${NC}"
cd /c/Users/weichao13/PycharmProjects/PythonProject/.claude/skills
pwd

# ===== 第 2 步: 部署 =====
echo -e "\n${CYAN}🚀 第 2 步: 运行部署脚本${NC}"
./deploy.sh

# ===== 第 3 步: 验证部署 =====
echo -e "\n${CYAN}✅ 第 3 步: 验证部署${NC}"
if [ -f ~/.claude/skills/code-quality/manifest.json ]; then
    echo -e "${GREEN}✅ 部署成功！文件已复制到全局目录${NC}"
    ls -la ~/.claude/skills/code-quality
else
    echo -e "${RED}❌ 部署失败！请检查错误信息${NC}"
fi

# ===== 第 4 步: 测试 =====
echo -e "\n${CYAN}🧪 第 4 步: 切换到其他项目测试${NC}"
cd ~/Documents
echo "当前目录: $(pwd)"
echo -e "\n${YELLOW}现在运行: claude${NC}"
echo -e "${YELLOW}然后输入: /quality-check${NC}"
```

---

## 📋 快速参考卡片

```
┌─────────────────────────────────────────────────┐
│  Skill 全局部署 - 快速参考                      │
├─────────────────────────────────────────────────┤
│                                                 │
│  📍 全局位置:                                   │
│     ~/.claude/skills/                           │
│     或 C:\Users\你\.claude\skills\              │
│                                                 │
│  🚀 部署命令:                                   │
│     Windows: .\deploy.ps1                       │
│     Linux:   ./deploy.sh                        │
│                                                 │
│  ✅ 验证:                                       │
│     切换到任意项目 → 运行 /quality-check        │
│                                                 │
│  🗑️ 卸载:                                       │
│     .\deploy.ps1 -Uninstall                     │
│     ./deploy.sh --uninstall                     │
│                                                 │
└─────────────────────────────────────────────────┘
```

---

## 💡 下一步

部署成功后，你可以：

1. **立即测试**：切换到任意项目，运行 `/quality-check`
2. **阅读使用文档**：[QUICKSTART.md](QUICKSTART.md)
3. **自定义配置**：编辑 `.code-quality.json`
4. **分享给团队**：参考 [DEPLOYMENT.md](DEPLOYMENT.md)

---

需要帮助？随时问我！😊
