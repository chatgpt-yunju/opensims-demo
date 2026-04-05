@echo off
echo ========================================
echo OpenSims - 打包为可执行文件
echo ========================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到Python，请先安装Python 3.10+
    pause
    exit /b 1
)

REM 检查是否安装PyInstaller
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo [提示] 正在安装PyInstaller...
    pip install pyinstaller
)

echo [1/3] 清理构建目录...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM 获取版本号
for /f "tokens=2 delims=." %%a in ('python version_manager.py show') do set VERSION=%%a
echo [2/3] 开始打包版本 v%VERSION%...

pyinstaller --onefile ^
    --name "OpenSims_v%VERSION%" ^
    --icon "NONE" ^
    --add-data "config.py;." ^
    --add-data "personality.py;." ^
    --add-data "storage.py;." ^
    --add-data "build_info.py;." ^
    gui.py

if errorlevel 1 (
    echo [错误] 打包失败
    pause
    exit /b 1
)

echo [3/3] 完成！
echo 可执行文件位置: dist/OpenSims.exe
echo.
pause
