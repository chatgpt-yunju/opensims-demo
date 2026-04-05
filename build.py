#!/usr/bin/env python3
"""
OpenSims 打包脚本
生成单个exe文件（主程序 + API服务器），带版本号
自动递增build号
"""

import os
import sys
import shutil
import subprocess
import json
from datetime import datetime

# 加载版本信息
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
        "patch": 0,
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

# 获取当前版本
version_data = increment_build()
VERSION = f"{version_data['major']}.{version_data['minor']}.{version_data['patch']}.{version_data['build']}"
BUILD_DATE = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

print(f"[Build] 版本: {VERSION}  Build: {version_data['build']}")

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
    """使用PyInstaller打包（版本化命名）"""
    # 输出文件名（带版本号）
    exe_name = f"OpenSims_{VERSION}"

    # 基本命令 - 使用hidden-import替代collect-all（避免mcp cli依赖）
    cmd = [
        'pyinstaller',
        '--onefile',                    # 单个exe
        '--console',                   # 使用控制台窗口（便于调试）
        f'--name={exe_name}',           # exe名称（带版本）
        '--icon=static/icon.ico',       # 图标（如果存在）
        '--add-data=static;static',    # 静态资源
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
        '--exclude-module=tkinter',
        '--exclude-module=test',
        '--exclude-module=pytest',
        '--exclude-module=mcp.cli',  # 排除CLI（需要typer）
        '--noconfirm',
        'main.py'
    ]

    # 检查图标是否存在
    if not os.path.exists('static/icon.ico'):
        # 移除图标参数
        cmd = [arg for arg in cmd if not arg.startswith('--icon')]
        print("[注意] 未找到图标文件，使用默认图标")

    # 处理hidden-import的路径分隔符（Windows用分号，Linux用冒号）
    if os.name == 'nt':  # Windows
        for i, arg in enumerate(cmd):
            if arg.startswith('--add-data'):
                cmd[i] = arg.replace(';', ';')

    run_command(cmd, f"PyInstaller打包 v{VERSION}")

def copy_additional_files():
    """复制额外文件到dist目录"""
    print("\n[复制] 复制配置和依赖文件...")
    dist_dir = 'dist'

    files_to_copy = [
        'config.py',
        'requirements.txt',
        'README.md',
        'quick_start_demo.bat',
        'start.bat',
        'XIAOHONGSHU_IMPLEMENTATION.md',
        'MCP_README.md',
        'JUEJIN_EXTRACTOR.md'
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

def create_start_script():
    """创建启动脚本（带版本信息）"""
    print("\n[创建] 生成启动脚本...")

    # Windows批处理
    bat_content = f"""@echo off
chcp 65001 >nul
echo ========================================
echo OpenSims v{VERSION} - 模拟人生
echo 构建日期: {BUILD_DATE}
echo ========================================
echo.
OpenSims_{VERSION}.exe
pause
"""
    bat_path = f'dist/start_opensims_v{VERSION}.bat'
    with open(bat_path, 'w', encoding='utf-8') as f:
        f.write(bat_content)
    print(f"  已创建: {os.path.basename(bat_path)}")

    # 通用启动脚本（不带版本，指向最新版本）
    latest_bat = 'dist/start_opensims_latest.bat'
    with open(latest_bat, 'w', encoding='utf-8') as f:
        f.write(bat_content.replace(f'OpenSims_{VERSION}.exe', 'OpenSims_latest.exe'))
    print(f"  已创建: start_opensims_latest.bat")

def create_portable_package():
    """创建便携包（zip）"""
    print("\n[打包] 创建便携包...")
    import zipfile

    dist_dir = 'dist'
    zip_name = f'OpenSims_v{VERSION}_{datetime.now().strftime("%Y%m%d")}.zip'

    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(dist_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, dist_dir)
                zf.write(file_path, arcname)
        # 添加启动脚本
        zf.write(f'dist/start_opensims_v{VERSION}.bat', f'start_opensims_v{VERSION}.bat')

    print(f"  已创建: {zip_name}")

def create_version_file():
    """创建版本信息文件"""
    print("\n[创建] 版本信息文件...")
    version_info = f"""OpenSims Version: {VERSION}
Build Date: {BUILD_DATE}
Features:
  - 虚拟人生模拟
  - 自动聊天系统
  - 小红书发布（模拟/API/Playwright）
  - 掘金文章提取
  - OpenClaw Skill接口
  - MCP插件支持

Created by: OpenSims Team
"""
    with open(f'dist/VERSION_{VERSION}.txt', 'w', encoding='utf-8') as f:
        f.write(version_info)
    print(f"  已创建: VERSION_{VERSION}.txt")

def main():
    print("=" * 60)
    print(f"OpenSims 打包工具 v{VERSION}")
    print("=" * 60)

    if not os.path.exists('main.py'):
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

    # 5. 创建便携包
    create_portable_package()

    print("\n" + "=" * 60)
    print(f"[OK] 打包完成！版本: {VERSION}")
    print("=" * 60)
    print("\n输出文件:")
    print(f"  dist/OpenSims_{VERSION}.exe - 主程序")
    print(f"  OpenSims_v{VERSION}_*.zip - 便携包")
    print("\n使用方式:")
    print(f"  1. 运行 dist/OpenSims_{VERSION}.exe")
    print(f"  2. 或解压便携包后运行 start_opensims_v{VERSION}.bat")
    print("\n注意:")
    print("  - 保留旧版本exe（不会自动删除）")
    print("  - 每次打包生成新版本文件")
    print("=" * 60)

if __name__ == "__main__":
    main()
