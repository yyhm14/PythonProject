# Deploy Code Quality Skill to Global
# 将 code-quality skill 部署到全局用户目录

param(
    [Parameter(Mandatory=$false)]
    [switch]$Uninstall,

    [Parameter(Mandatory=$false)]
    [switch]$Force
)

$ErrorActionPreference = "Stop"

# 配置
$SkillName = "code-quality"
$SourceDir = Join-Path $PSScriptRoot $SkillName
$TargetDir = Join-Path $env:USERPROFILE ".claude\skills\$SkillName"

# 颜色输出
function Write-Success { param($Message) Write-Host "✅ $Message" -ForegroundColor Green }
function Write-Info { param($Message) Write-Host "ℹ️  $Message" -ForegroundColor Cyan }
function Write-Warning { param($Message) Write-Host "⚠️  $Message" -ForegroundColor Yellow }
function Write-Error { param($Message) Write-Host "❌ $Message" -ForegroundColor Red }

# Banner
Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "   Code Quality Skill - 全局部署工具" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# 卸载模式
if ($Uninstall) {
    Write-Info "开始卸载 skill..."

    if (Test-Path $TargetDir) {
        Remove-Item -Path $TargetDir -Recurse -Force
        Write-Success "已从全局目录移除: $TargetDir"
    } else {
        Write-Warning "Skill 未安装在全局目录"
    }

    Write-Host ""
    Write-Info "卸载完成"
    exit 0
}

# 安装模式
Write-Info "检查源目录..."

if (-not (Test-Path $SourceDir)) {
    Write-Error "源目录不存在: $SourceDir"
    Write-Host ""
    Write-Host "请确保在项目根目录运行此脚本" -ForegroundColor Yellow
    exit 1
}

# 检查必需文件
$RequiredFiles = @("manifest.json", "quality-check.prompt.md", "README.md")
$MissingFiles = @()

foreach ($File in $RequiredFiles) {
    $FilePath = Join-Path $SourceDir $File
    if (-not (Test-Path $FilePath)) {
        $MissingFiles += $File
    }
}

if ($MissingFiles.Count -gt 0) {
    Write-Error "缺少必需文件:"
    foreach ($File in $MissingFiles) {
        Write-Host "  - $File" -ForegroundColor Red
    }
    exit 1
}

Write-Success "源文件检查通过"

# 检查目标目录
if (Test-Path $TargetDir) {
    if ($Force) {
        Write-Warning "目标目录已存在，将被覆盖"
        Remove-Item -Path $TargetDir -Recurse -Force
    } else {
        Write-Warning "目标目录已存在: $TargetDir"
        $Response = Read-Host "是否覆盖？(y/N)"

        if ($Response -ne "y" -and $Response -ne "Y") {
            Write-Info "部署已取消"
            exit 0
        }

        Remove-Item -Path $TargetDir -Recurse -Force
    }
}

# 创建目标目录
Write-Info "创建目标目录..."
New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null
Write-Success "目录创建成功: $TargetDir"

# 复制文件
Write-Info "复制 skill 文件..."
Copy-Item -Path "$SourceDir\*" -Destination $TargetDir -Recurse -Force
Write-Success "文件复制完成"

# 验证部署
Write-Info "验证部署..."
$DeployedFiles = Get-ChildItem -Path $TargetDir -File -Recurse
Write-Host "  已部署 $($DeployedFiles.Count) 个文件:" -ForegroundColor Gray
foreach ($File in $DeployedFiles) {
    $RelativePath = $File.FullName.Replace($TargetDir, "").TrimStart("\")
    Write-Host "    - $RelativePath" -ForegroundColor Gray
}

# 完成
Write-Host ""
Write-Host "================================================" -ForegroundColor Green
Write-Success "部署成功！"
Write-Host "================================================" -ForegroundColor Green
Write-Host ""
Write-Info "Skill 已部署到全局目录，现在可以在任何项目中使用："
Write-Host ""
Write-Host "  /quality-check          # 检查代码质量" -ForegroundColor Yellow
Write-Host "  /quality-fix <file>     # 修复代码问题" -ForegroundColor Yellow
Write-Host "  /quality-config         # 配置检查规则" -ForegroundColor Yellow
Write-Host ""
Write-Info "测试部署:"
Write-Host "  1. 打开任意项目" -ForegroundColor Gray
Write-Host "  2. 运行 claude" -ForegroundColor Gray
Write-Host "  3. 输入 /quality-check" -ForegroundColor Gray
Write-Host ""

# 提供卸载说明
Write-Host "需要卸载时，运行:" -ForegroundColor Gray
Write-Host "  .\deploy.ps1 -Uninstall" -ForegroundColor Gray
Write-Host ""
