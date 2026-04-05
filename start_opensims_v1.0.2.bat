@echo off
cd /d "%~dp0"
echo 启动 OpenSims v1.0.2 - Multi-Agent导师引导系统
echo.
if exist "dist\OpenSims_v1.0.2.exe" (
    start "" "dist\OpenSims_v1.0.2.exe"
    echo 已启动游戏
) else (
    echo [错误] 未找到 dist\OpenSims_v1.0.2.exe
    echo 请先运行 build_exe.bat 打包
)
pause
