# VS Build Tools 安装脚本
# 需要以管理员身份运行

Write-Host "=== 安装 Visual Studio Build Tools 2022 ===" -ForegroundColor Cyan
Write-Host "这将安装 C++ 编译工具链，约 6-7GB，需要 10-20 分钟" -ForegroundColor Yellow
Write-Host ""

# 下载安装程序
$installerUrl = "https://aka.ms/vs/17/release/vs_BuildTools.exe"
$installerPath = "$env:TEMP\vs_BuildTools.exe"

Write-Host "正在下载安装程序..." -ForegroundColor Green
try {
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    Invoke-WebRequest -Uri $installerUrl -OutFile $installerPath -UseBasicParsing
    Write-Host "下载完成" -ForegroundColor Green
} catch {
    Write-Host "下载失败: $_" -ForegroundColor Red
    Write-Host "请手动下载: $installerUrl" -ForegroundColor Yellow
    exit 1
}

# 运行安装程序
Write-Host ""
Write-Host "正在安装 Visual Studio Build Tools..." -ForegroundColor Green
Write-Host "请等待安装完成，不要关闭窗口..." -ForegroundColor Yellow
Write-Host ""

$arguments = @(
    "--add", "Microsoft.VisualStudio.Workload.VCTools",
    "--includeRecommended",
    "--quiet",
    "--wait",
    "--norestart"
)

try {
    $process = Start-Process -FilePath $installerPath -ArgumentList $arguments -Wait -PassThru -NoNewWindow
    
    if ($process.ExitCode -eq 0) {
        Write-Host ""
        Write-Host "=== 安装成功 ===" -ForegroundColor Green
        Write-Host "请重启终端以使环境变量生效" -ForegroundColor Yellow
    } else {
        Write-Host ""
        Write-Host "安装失败，退出代码: $($process.ExitCode)" -ForegroundColor Red
        Write-Host "可能需要以管理员身份运行此脚本" -ForegroundColor Yellow
    }
} catch {
    Write-Host "安装过程出错: $_" -ForegroundColor Red
}

# 清理
Remove-Item -Path $installerPath -Force -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "按任意键退出..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
