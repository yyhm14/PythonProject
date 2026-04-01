#!/bin/bash

# Deploy Code Quality Skill to Global
# 将 code-quality skill 部署到全局用户目录

set -e

# 配置
SKILL_NAME="code-quality"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_DIR="$SCRIPT_DIR/$SKILL_NAME"
TARGET_DIR="$HOME/.claude/skills/$SKILL_NAME"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
GRAY='\033[0;90m'
NC='\033[0m' # No Color

success() { echo -e "${GREEN}✅ $1${NC}"; }
info() { echo -e "${CYAN}ℹ️  $1${NC}"; }
warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
error() { echo -e "${RED}❌ $1${NC}"; }

# 解析参数
UNINSTALL=false
FORCE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --uninstall|-u)
            UNINSTALL=true
            shift
            ;;
        --force|-f)
            FORCE=true
            shift
            ;;
        --help|-h)
            echo "用法: $0 [选项]"
            echo ""
            echo "选项:"
            echo "  --uninstall, -u    卸载 skill"
            echo "  --force, -f        强制覆盖已存在的文件"
            echo "  --help, -h         显示帮助信息"
            exit 0
            ;;
        *)
            error "未知参数: $1"
            echo "运行 '$0 --help' 查看帮助"
            exit 1
            ;;
    esac
done

# Banner
echo ""
echo -e "${CYAN}================================================${NC}"
echo -e "${CYAN}   Code Quality Skill - 全局部署工具${NC}"
echo -e "${CYAN}================================================${NC}"
echo ""

# 卸载模式
if [ "$UNINSTALL" = true ]; then
    info "开始卸载 skill..."

    if [ -d "$TARGET_DIR" ]; then
        rm -rf "$TARGET_DIR"
        success "已从全局目录移除: $TARGET_DIR"
    else
        warning "Skill 未安装在全局目录"
    fi

    echo ""
    info "卸载完成"
    exit 0
fi

# 安装模式
info "检查源目录..."

if [ ! -d "$SOURCE_DIR" ]; then
    error "源目录不存在: $SOURCE_DIR"
    echo ""
    echo -e "${YELLOW}请确保在项目根目录运行此脚本${NC}"
    exit 1
fi

# 检查必需文件
REQUIRED_FILES=("manifest.json" "quality-check.prompt.md" "README.md")
MISSING_FILES=()

for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$SOURCE_DIR/$file" ]; then
        MISSING_FILES+=("$file")
    fi
done

if [ ${#MISSING_FILES[@]} -gt 0 ]; then
    error "缺少必需文件:"
    for file in "${MISSING_FILES[@]}"; do
        echo -e "  ${RED}- $file${NC}"
    done
    exit 1
fi

success "源文件检查通过"

# 检查目标目录
if [ -d "$TARGET_DIR" ]; then
    if [ "$FORCE" = true ]; then
        warning "目标目录已存在，将被覆盖"
        rm -rf "$TARGET_DIR"
    else
        warning "目标目录已存在: $TARGET_DIR"
        read -p "是否覆盖？(y/N) " -n 1 -r
        echo

        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            info "部署已取消"
            exit 0
        fi

        rm -rf "$TARGET_DIR"
    fi
fi

# 创建目标目录
info "创建目标目录..."
mkdir -p "$TARGET_DIR"
success "目录创建成功: $TARGET_DIR"

# 复制文件
info "复制 skill 文件..."
cp -r "$SOURCE_DIR"/* "$TARGET_DIR/"
success "文件复制完成"

# 验证部署
info "验证部署..."
FILE_COUNT=$(find "$TARGET_DIR" -type f | wc -l)
echo -e "  ${GRAY}已部署 $FILE_COUNT 个文件:${NC}"
find "$TARGET_DIR" -type f | while read file; do
    relative_path="${file#$TARGET_DIR/}"
    echo -e "    ${GRAY}- $relative_path${NC}"
done

# 完成
echo ""
echo -e "${GREEN}================================================${NC}"
success "部署成功！"
echo -e "${GREEN}================================================${NC}"
echo ""
info "Skill 已部署到全局目录，现在可以在任何项目中使用："
echo ""
echo -e "  ${YELLOW}/quality-check${NC}          # 检查代码质量"
echo -e "  ${YELLOW}/quality-fix <file>${NC}     # 修复代码问题"
echo -e "  ${YELLOW}/quality-config${NC}         # 配置检查规则"
echo ""
info "测试部署:"
echo -e "  ${GRAY}1. 打开任意项目${NC}"
echo -e "  ${GRAY}2. 运行 claude${NC}"
echo -e "  ${GRAY}3. 输入 /quality-check${NC}"
echo ""

# 提供卸载说明
echo -e "${GRAY}需要卸载时，运行:${NC}"
echo -e "  ${GRAY}$0 --uninstall${NC}"
echo ""
