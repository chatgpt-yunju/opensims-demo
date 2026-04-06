#!/usr/bin/env python3
"""
OpenSims GUI Simple 打包脚本
生成单文件exe：OpenSims_GUI_Simple_vX.X.X.exe
"""

import os
import sys
import subprocess
import json
from datetime import datetime

def load_version():
    """从version.json加载版本"""
    version_file = 'version.json'
    if os.path.exists(version_file):
        with open(version_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    return {
        "major": 1,
        "minor": 0,
        "patch": 3,
        "build": 0,
        "last_updated": datetime.now().isoformat()
    }

def increment_build():
    """递增build号并保存"""
    ver = load_version()
    ver['build'] += 1
    ver['last_updated'] = datetime.now().isoformat()
    with open('version.json', 'w', encoding='utf-8') as f:
        json.dump(ver, f, ensure_ascii=False, indent=2)
    return ver

version_data = increment_build()
VERSION = f"{version_data['major']}.{version_data['minor']}.{version_data['patch']}.{version_data['build']}"
BUILD_DATE = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

print(f"[Build] GUI Simple 版本: {VERSION}  Build: {version_data['build']}")

def run_command(cmd, description):
    """运行命令并打印"""
    print(f"\n[{'*' * 60}]")
    print(f"执行: {description}")
    print(f"命令: {' '.join(cmd)}")
    print(f"[{'*' * 60}]")
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print(f"[错误] {description} 失败")
        sys.exit(1)

def build_exe():
    """使用PyInstaller打包gui_simple.py"""
    exe_name = f"OpenSims_GUI_Simple_{VERSION}"

    cmd = [
        'pyinstaller',
        '--onefile',
        '--console',
        f'--name={exe_name}',
        '--icon=static/icon.ico',
        '--add-data=static;static',
        '--hidden-import=uvicorn.loops.auto',
        '--hidden-import=uvicorn.loops.asyncio',
        '--hidden-import=uvicorn.protocols.http.auto',
        '--hidden-import=uvicorn.protocols.http.h11_impl',
        '--hidden-import=uvicorn.lifespan.on',
        '--hidden-import=playwright.async_api',
        '--hidden-import=playwright.sync_api',
        '--hidden-import=mcp',
        '--hidden-import=mcp.server',
        '--hidden-import=mcp.types',
        '--hidden-import=mcp.server.models',
        '--hidden-import=mcp.server.stdio',
        '--exclude-module=matplotlib',
        '--exclude-module=test',
        '--exclude-module=pytest',
        '--exclude-module=mcp.cli',
        '--noconfirm',
        'gui_simple.py'
    ]

    if not os.path.exists('static/icon.ico'):
        cmd = [arg for arg in cmd if not arg.startswith('--icon')]
        print("[注意] 未找到图标文件，使用默认图标")

    run_command(cmd, f"PyInstaller打包 GUI Simple v{VERSION}")

def create_start_script():
    """创建启动脚本"""
    print("\n[创建] 生成启动脚本...")

    bat_content = f"""@echo off
chcp 65001 >nul
echo ========================================
echo OpenSims GUI Simple v{VERSION} - 导师对话模式
echo 构建日期: {BUILD_DATE}
echo ========================================
echo.
OpenSims_GUI_Simple_{VERSION}.exe
pause
"""
    bat_path = f'dist/start_opensims_gui_simple_v{VERSION}.bat'
    with open(bat_path, 'w', encoding='utf-8') as f:
        f.write(bat_content)
    print(f"  已创建: {os.path.basename(bat_path)}")

    latest_bat = 'dist/start_opensims_gui_simple_latest.bat'
    with open(latest_bat, 'w', encoding='utf-8') as f:
        f.write(bat_content.replace(f'OpenSims_GUI_Simple_{VERSION}.exe', 'OpenSims_GUI_Simple_latest.exe'))
    print(f"  已创建: start_opensims_gui_simple_latest.bat")

def copy_additional_files():
    """复制额外文件到dist目录"""
    print("\n[复制] 复制配置和依赖文件...")
    dist_dir = 'dist'

    files_to_copy = [
        'config.py',
        'requirements.txt',
        'README.md',
        'human_like_chat.py',
        'settings.json',
        'settings.py'
    ]

    for f in files_to_copy:
        if os.path.exists(f):
            shutil.copy2(f, os.path.join(dist_dir, f))
            print(f"  已复制: {f}")

    # 创建空数据文件
    data_files = ['demo_data.json']
    for f in data_files:
        target = os.path.join(dist_dir, f)
        if not os.path.exists(target):
            with open(target, 'w', encoding='utf-8') as fp:
                fp.write('{}')
            print(f"  已创建: {f}")

def create_version_file():
    """创建版本信息文件"""
    print("\n[创建] 版本信息文件...")
    version_info = f"""OpenSims GUI Simple Version: {VERSION}
Build Date: {BUILD_DATE}
Features:
  - 导师对话模式（极简GUI）
  - Human-like Chat System
  - Multi-Agent协作引导

Created by: OpenSims Team
"""
    with open(f'dist/VERSION_GUI_Simple_{VERSION}.txt', 'w', encoding='utf-8') as f:
        f.write(version_info)
    print(f"  已创建: VERSION_GUI_Simple_{VERSION}.txt")

def main():
    print("=" * 60)
    print(f"OpenSims GUI Simple 打包工具 v{VERSION}")
    print("=" * 60)

    if not os.path.exists('gui_simple.py'):
        print("[错误] 请在OpenSims项目根目录运行此脚本")
        sys.exit(1)

    # 1. 打包
    build_exe()

    # 2. 复制额外文件
    copy_additional_files()

    # 3. 创建启动脚本
    create_start_script()

    # 4. 创建版本文件
    create_version_file()

    print("\n" + "=" * 60)
    print(f"[OK] 打包完成！版本: {VERSION}")
    print("=" * 60)
    print("\n输出文件:")
    print(f"  dist/OpenSims_GUI_Simple_{VERSION}.exe - 主程序")
    print("\n使用方式:")
    print(f"  1. 运行 dist/OpenSims_GUI_Simple_{VERSION}.exe")
    print(f"  2. 或运行 start_opensims_gui_simple_v{VERSION}.bat")
    print("\n注意:")
    print("  - 保留旧版本exe（不会自动删除）")
    print("  - 每次打包生成新版本文件")
    print("=" * 60)

if __name__ == "__main__":
    import shutil
    main()
