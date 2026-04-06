#!/usr/bin/env python3
"""
GUI Integration Test - 测试GUI应用启动和基本交互
"""

import os
import sys
import time
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tkinter as tk
from gui_simple import MentorChatGUI
from main import OpenSimsDemo

def test_gui_startup():
    """测试GUI启动"""
    print("[Test] GUI Startup...")
    try:
        # 创建模拟根窗口（不显示）
        root = tk.Tk()
        root.withdraw()

        # 实例化GUI（但不用 run()）
        gui = MentorChatGUI.__new__(MentorChatGUI)
        gui.demo = OpenSimsDemo()

        # 手动初始化关键属性
        gui.root = root
        gui.auto_chat_thread = None
        gui.auto_chat_stop = threading.Event()
        gui.vh_monitor_window = None
        gui.vh_monitor_text = None

        # 执行__init__中的关键步骤
        gui.create_menu()
        gui.create_widgets()
        gui.setup_system()

        # 获取当前虚拟人
        vh = gui.demo.vh
        if vh:
            print(f"  Active mentor: {vh.name}")
        else:
            print("  Warning: No active mentor (expected if first run)")

        print("  PASS: GUI initialization succeeded")
        root.destroy()
        return True
    except Exception as e:
        print(f"  FAIL: {e}")
        import traceback
        traceback.print_exc()
        try:
            root.destroy()
        except:
            pass
        return False

def test_settings_dialog():
    """测试设置对话框打开"""
    print("[Test] Settings Dialog...")
    try:
        root = tk.Tk()
        root.withdraw()

        gui = MentorChatGUI.__new__(MentorChatGUI)
        gui.demo = OpenSimsDemo()
        gui.root = root
        gui.auto_chat_thread = None
        gui.auto_chat_stop = threading.Event()
        gui.vh_monitor_window = None
        gui.vh_monitor_text = None

        gui.create_menu()
        gui.create_widgets()
        gui.setup_system()

        # 尝试打开设置对话框（立即关闭）
        gui.show_settings_dialog()
        root.after(100, root.destroy)
        root.mainloop()

        print("  PASS: Settings dialog opened without error")
        return True
    except Exception as e:
        print(f"  FAIL: {e}")
        try:
            root.destroy()
        except:
            pass
        return False

def test_monitor_window():
    """测试虚拟人监控窗口"""
    print("[Test] Monitor Window...")
    try:
        root = tk.Tk()
        root.withdraw()

        gui = MentorChatGUI.__new__(MentorChatGUI)
        gui.demo = OpenSimsDemo()
        gui.root = root
        gui.auto_chat_thread = None
        gui.auto_chat_stop = threading.Event()
        gui.vh_monitor_window = None
        gui.vh_monitor_text = None

        gui.create_menu()
        gui.create_widgets()
        gui.setup_system()

        # 打开监控窗口
        gui.create_vh_monitor_window()
        if gui.vh_monitor_window:
            print("  Monitor window created")
        else:
            print("  FAIL: Monitor window not created")
            root.destroy()
            return False

        root.after(200, root.destroy)
        root.mainloop()

        print("  PASS: Monitor window works")
        return True
    except Exception as e:
        print(f"  FAIL: {e}")
        try:
            root.destroy()
        except:
            pass
        return False

def main():
    print("="*60)
    print("OpenSims GUI Integration Test")
    print("="*60)

    results = []
    tests = [
        test_gui_startup,
        test_settings_dialog,
        test_monitor_window,
    ]

    for test in tests:
        try:
            passed = test()
            results.append((test.__name__, passed))
        except Exception as e:
            results.append((test.__name__, False, str(e)))

    print("\n" + "="*60)
    print("SUMMARY")
    passed_count = sum(1 for _, p in results if p)
    total = len(results)
    print(f"Passed: {passed_count}/{total}")
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {name}")
    print("="*60)

    all_pass = all(passed for _, passed in results)
    return all_pass

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
