# 沐梧AI解题系统 - 数据库版本启动脚本 (PowerShell)

Write-Host ""
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host "  沐梧AI解题系统 - 数据库版本 V25.2" -ForegroundColor Yellow
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host ""

# 获取脚本所在目录
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

Write-Host "[1/3] 启动后端服务（FastAPI + MySQL）..." -ForegroundColor Green
Write-Host ""

# 启动后端
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$scriptPath\backend'; .\venv\Scripts\Activate.ps1; python main_db.py"

Start-Sleep -Seconds 3

Write-Host ""
Write-Host "[2/3] 启动前端服务（React + Vite）..." -ForegroundColor Green
Write-Host ""

# 启动前端
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$scriptPath\frontend\vite-project'; npm run dev"

Start-Sleep -Seconds 3

Write-Host ""
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host "  ✅ 数据库版本系统已启动！" -ForegroundColor Green
Write-Host ""
Write-Host "  📌 前端访问地址:" -ForegroundColor Yellow
Write-Host "     http://localhost:5173/?mode=db" -ForegroundColor White
Write-Host ""
Write-Host "  💡 首次使用:" -ForegroundColor Yellow
Write-Host "     1. 点击`"注册`"创建账号" -ForegroundColor White
Write-Host "     2. 登录后选择功能模式" -ForegroundColor White
Write-Host "     3. 开始使用！" -ForegroundColor White
Write-Host ""
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "按任意键关闭本窗口（前后端将继续运行）..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

