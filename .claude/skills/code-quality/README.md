# Code Quality Skill - 代码质量检查工具

这是一个专门为 Python 飞书机器人项目设计的代码质量检查和修复工具。

## 功能特性

### 🔍 检查能力

1. **代码规范问题**
   - 重复代码检测
   - 配置管理检查
   - 变量命名规范
   - 代码注释完整性
   - 函数复杂度分析

2. **异常处理**
   - try-catch 覆盖率检查
   - 异常信息完整性
   - 空值检查
   - 异常传播分析

3. **数据传输失败处理**
   - API 调用重试机制检查
   - 超时设置检查
   - 失败回退策略
   - 状态码处理
   - 网络异常处理

4. **日志记录**
   - 日志完整性检查
   - 日志级别使用
   - 日志内容质量
   - 敏感信息泄露检查
   - 日志格式统一性

5. **线程安全**
   - 全局变量使用检查
   - 锁机制检查
   - 竞态条件分析

### 🔧 修复能力

- **duplicate_code**: 自动删除重复代码，提取配置
- **exception_handling**: 增强异常处理，添加详细日志
- **logging**: 完善日志记录
- **api_retry**: 添加 API 重试机制

## 使用方法

### 检查代码质量

```bash
# 检查整个项目
/check

# 检查特定文件
/check main.py

# 检查特定文件（完整路径）
/check c:\Users\weichao13\PycharmProjects\PythonProject\alarm_service.py
```

### 修复代码问题

```bash
# 修复特定文件的所有问题
/fix alarm_service.py

# 只修复特定类型的问题
/fix alarm_service.py --issue_type=api_retry

# 可用的问题类型:
#   - duplicate_code: 重复代码
#   - exception_handling: 异常处理
#   - logging: 日志记录
#   - api_retry: API 重试
```

## 检查报告示例

```markdown
# 代码质量检查报告

生成时间: 2024-03-30 18:30:00
检查文件: alarm_service.py

## 摘要
- 检查文件数: 1
- 发现问题数: 8
- 严重问题: 2
- 中等问题: 4
- 轻微问题: 2

## 详细问题列表

### 🔴 严重问题

#### 1. [数据传输失败] 缺少 API 重试机制
**位置**: alarm_service.py:302
**描述**: push_feishu_card 函数调用飞书 API 时没有重试机制
**建议**: 添加 tenacity 重试装饰器
```

## 项目特定规则

针对飞书机器人项目，该 skill 特别关注：

1. **飞书 API 调用可靠性**
   - 所有 API 调用必须有重试机制
   - 必须设置合理的超时时间
   - 必须记录详细的失败日志

2. **数据写入可靠性**
   - 多维表格写入失败必须有日志
   - 文件写入必须处理 IO 异常
   - 关键数据必须有备份机制

3. **并发安全**
   - 全局缓存访问必须加锁
   - 防重复机制必须线程安全
   - 共享状态必须有保护

4. **日志完整性**
   - 每个用户操作必须记录
   - API 调用必须记录请求和响应
   - 异常必须记录完整堆栈

## 依赖要求

修复某些问题可能需要安装额外的依赖：

```bash
# API 重试机制
pip install tenacity

# 更好的日志记录
pip install python-json-logger
```

## 配置建议

### 推荐的日志配置

```python
import logging
from logging.handlers import RotatingFileHandler

# 创建 logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# 控制台处理器
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# 文件处理器（自动轮转）
file_handler = RotatingFileHandler(
    'app.log',
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5,
    encoding='utf-8'
)
file_handler.setLevel(logging.INFO)

# 格式化
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# 添加处理器
logger.addHandler(console_handler)
logger.addHandler(file_handler)
```

### 推荐的配置管理

```python
# config.py
import os
from dataclasses import dataclass

@dataclass
class Config:
    """应用配置"""
    app_id: str
    app_secret: str
    verification_token: str
    encrypt_key: str = ""

    @classmethod
    def from_env(cls):
        """从环境变量加载配置"""
        return cls(
            app_id=os.getenv("FEISHU_APP_ID"),
            app_secret=os.getenv("FEISHU_APP_SECRET"),
            verification_token=os.getenv("FEISHU_VERIFICATION_TOKEN"),
            encrypt_key=os.getenv("FEISHU_ENCRYPT_KEY", "")
        )

# 使用
config = Config.from_env()
```

## 最佳实践

1. **定期检查**: 建议在提交代码前运行 `/check`
2. **增量修复**: 优先修复严重问题，逐步改进代码质量
3. **测试验证**: 修复后运行测试确保功能正常
4. **代码审查**: 重要修复建议人工审查确认

## 问题反馈

如果发现 skill 的问题或有改进建议，请：
1. 记录问题详情和复现步骤
2. 提供问题代码片段
3. 说明期望的检查或修复行为

## 版本历史

- **v1.0.0** (2024-03-30)
  - 初始版本
  - 支持代码规范、异常处理、日志记录、数据传输失败检查
  - 支持自动修复常见问题

## 作者

weichao13

## 许可

MIT License
