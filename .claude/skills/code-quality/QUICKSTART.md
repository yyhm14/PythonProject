# 代码质量检查 Skill - 快速开始

## 安装说明

这个 skill 已经创建在你的项目目录中：
```
.claude/skills/code-quality/
```

Claude Code 会自动加载项目中的 skills。

## 快速体验

### 1. 检查整个项目的代码质量

在 Claude Code 中输入：
```
/check
```

这将扫描项目中的所有 Python 文件，并生成详细的代码质量报告。

### 2. 检查特定文件

```
/check main.py
```

或使用完整路径：
```
/check c:\Users\weichao13\PycharmProjects\PythonProject\alarm_service.py
```

### 3. 查看当前代码中的实际问题

让我演示一下，检查 `main.py` 文件会发现哪些问题：

**发现的问题示例**：

#### 🔴 严重问题 1: 重复的配置定义
- **位置**: main.py:3-6 和 main.py:27-30
- **问题**: APP_ID, APP_SECRET 等配置定义了两次
- **影响**: 容易导致配置不一致，修改时容易遗漏
- **建议**: 删除重复定义，或提取到 config.py

#### 🔴 严重问题 2: 缺少 API 重试机制
- **位置**: main.py:68 (API 调用)
- **问题**: 调用飞书 API 时没有重试机制
- **影响**: 网络波动会导致功能失败
- **建议**: 使用 tenacity 库添加重试

#### 🟡 中等问题 3: 异常处理不够详细
- **位置**: main.py:74
- **问题**: 只打印了错误信息，没有记录堆栈
- **影响**: 排查问题困难
- **建议**: 使用 logging.exception() 记录完整信息

#### 🟢 轻微问题 4: 缺少日志记录
- **位置**: main.py:45-75
- **问题**: write_to_bitable 函数缺少详细的操作日志
- **影响**: 难以追踪数据写入情况
- **建议**: 添加 INFO 级别的日志

## 修复代码问题

### 自动修复所有问题

```
/fix alarm_service.py
```

这将自动修复文件中检测到的所有问题。

### 只修复特定类型的问题

```
/fix alarm_service.py --issue_type=api_retry
```

可用的修复类型：
- `duplicate_code` - 重复代码
- `exception_handling` - 异常处理
- `logging` - 日志记录
- `api_retry` - API 重试机制

## 实战演练

### 演练 1: 修复 main.py 的重复配置

**步骤 1**: 检查问题
```
/check main.py
```

**步骤 2**: 修复重复代码
```
/fix main.py --issue_type=duplicate_code
```

**步骤 3**: 验证修复效果
```
/check main.py
```

### 演练 2: 为 alarm_service.py 添加 API 重试

**步骤 1**: 检查 API 调用
```
/check alarm_service.py
```

**步骤 2**: 添加重试机制
```
/fix alarm_service.py --issue_type=api_retry
```

**步骤 3**: 安装依赖
```bash
pip install tenacity
```

**步骤 4**: 测试修复后的代码
```bash
python alarm_service.py
```

### 演练 3: 增强异常处理

**步骤 1**: 检查异常处理
```
/check alarm_service.py
```

查看报告中关于异常处理的部分。

**步骤 2**: 修复异常处理
```
/fix alarm_service.py --issue_type=exception_handling
```

**步骤 3**: 查看修改内容
修复工具会显示修改前后的对比。

## 预期的检查报告示例

运行 `/check main.py` 后，你会看到类似这样的报告：

```markdown
# 代码质量检查报告

生成时间: 2024-04-01 15:30:00
检查文件: main.py

## 摘要
- 检查文件数: 1
- 发现问题数: 6
- 严重问题: 2
- 中等问题: 3
- 轻微问题: 1

## 详细问题列表

### 🔴 严重问题

#### 1. [代码规范] 重复的配置定义
**位置**: main.py:3-6, 27-30
**描述**: APP_ID、APP_SECRET、VERIFICATION_TOKEN 等配置重复定义
**影响**: 配置不一致风险，维护困难
**建议**: 删除其中一处，或提取到 config.py

**示例修复**:
\```python
# config.py
class Config:
    APP_ID = "cli_a9fbc96b89389bc4"
    APP_SECRET = "srtnI073jIR8zhSqCDbBRI1fyumJRgOz"
    VERIFICATION_TOKEN = "FP4qqknpMjAEitbLAIIyzhAewFo4Rp7m"

# main.py
from config import Config
\```

#### 2. [数据传输失败] 缺少 API 重试机制
**位置**: main.py:68 (bitable.v1.app_table_record.create)
**描述**: 调用飞书多维表格 API 没有重试机制
**影响**: 网络波动导致数据写入失败
**优先级**: 高
**建议**: 添加 tenacity 重试装饰器

**示例修复**:
\```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
def write_to_bitable(...):
    # 原有代码
\```

### 🟡 中等问题

#### 3. [异常处理] 异常日志不完整
**位置**: main.py:74
**描述**: 捕获异常后只打印了简单的错误信息
**影响**: 排查问题困难，缺少堆栈信息
**建议**: 使用 logging.exception()

**示例修复**:
\```python
import logging
except Exception as e:
    logging.exception("多维表格操作异常")
\```

#### 4. [日志记录] 缺少关键操作日志
**位置**: main.py:45-75 (write_to_bitable 函数)
**描述**: 函数缺少入口和成功的日志记录
**影响**: 难以追踪数据写入情况
**建议**: 添加 INFO 级别日志

**示例修复**:
\```python
def write_to_bitable(...):
    logging.info(f"开始写入多维表格: linear={linear}, device={device}")
    # ... 原有代码
    logging.info(f"多维表格写入成功: record_id={record_id}")
\```

### 🟢 轻微问题

#### 5. [代码规范] 函数参数过多
**位置**: main.py:45
**描述**: write_to_bitable 函数有 10 个参数
**影响**: 函数调用复杂，容易出错
**建议**: 考虑使用数据类或字典封装参数
```

## 进阶使用

### 自定义检查规则

你可以编辑 `.claude/skills/code-quality/check.prompt.md` 文件来自定义检查规则。

例如，添加项目特定的检查：

```markdown
## 6. 项目特定检查

### 飞书 API 调用规范
- 所有飞书 API 调用必须有超时设置
- 必须检查 response.success()
- 必须记录 response.code 和 response.msg
```

### 集成到 CI/CD

你可以将代码检查集成到 CI/CD 流程中：

```bash
# .github/workflows/code-quality.yml
name: Code Quality Check

on: [push, pull_request]

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run code quality check
        run: claude /check --format=json > report.json
```

## 常见问题

### Q: Skill 没有被识别？
A: 确保文件在 `.claude/skills/code-quality/` 目录中，并且 manifest.json 格式正确。

### Q: 修复会破坏代码吗？
A: 修复前会显示详细的修改内容，你可以选择是否应用。建议先提交当前代码，再应用修复。

### Q: 如何只检查不修复？
A: 使用 `/check` 命令只会生成报告，不会修改代码。

### Q: 可以跳过某些检查吗？
A: 暂时不支持，但你可以编辑 prompt 文件来调整检查规则。

## 下一步

1. 运行 `/check` 查看你项目的代码质量报告
2. 从严重问题开始，逐步修复
3. 定期运行检查，保持代码质量
4. 根据项目需求自定义检查规则

## 反馈和改进

如有问题或建议，欢迎反馈！
