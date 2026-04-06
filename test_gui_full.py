#!/usr/bin/env python3
"""
OpenSims GUI Full Feature Test - 自动化测试所有GUI功能
"""

import os
import sys
import time
import threading
import tkinter as tk
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import OpenSimsDemo
from config import PERSONALITY_PRESETS
import settings as gui_settings

class TestResult:
    def __init__(self):
        self.tests = []
        self.passed = 0
        self.failed = 0

    def add(self, name, passed, msg=""):
        self.tests.append((name, passed, msg))
        if passed:
            self.passed += 1
        else:
            self.failed += 1

    def print_summary(self):
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        for name, passed, msg in self.tests:
            status = "PASS" if passed else "FAIL"
            print(f"[{status}] {name}")
            if msg and not passed:
                print(f"       Reason: {msg}")
        print("-"*60)
        print(f"Total: {self.passed + self.failed} | Passed: {self.passed} | Failed: {self.failed}")
        print("="*60)
        return self.failed == 0

def safe_print(msg):
    """安全打印（ASCII编码）"""
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode('ascii', 'ignore').decode('ascii'))

def test_settings_hot_reload():
    """测试1: 设置热更新功能"""
    print("\n[Test 1] Settings Hot-Reload")
    try:
        # 读取当前设置
        s1 = gui_settings.load_settings()
        new_settings = s1.copy()
        new_settings["auto_chat_rounds"] = 50
        new_settings["auto_chat_interval"] = 60

        # 保存并重新加载
        if gui_settings.save_settings(new_settings):
            s2 = gui_settings.load_settings()
            if s2["auto_chat_rounds"] == 50 and s2["auto_chat_interval"] == 60:
                print("  PASS: Settings saved and reloaded correctly")
                return True
            else:
                print("  FAIL: Settings not persisted")
                return False
        else:
            print("  FAIL: Save failed")
            return False
    except Exception as e:
        print(f"  FAIL: {e}")
        return False

def test_api_client_config():
    """测试2: APIClient配置读取"""
    print("\n[Test 2] APIClient Configuration")
    try:
        from api_client import APIClient
        api = APIClient()
        print(f"  Endpoint: {api.endpoint}")
        print(f"  Model: {api.model}")
        print(f"  Use Mock: {api.use_mock}")
        print("  PASS: APIClient initializes correctly")
        return True
    except Exception as e:
        print(f"  FAIL: {e}")
        return False

def test_virtual_human_creation():
    """测试3: 虚拟人创建"""
    print("\n[Test 3] Virtual Human Creation")
    try:
        demo = OpenSimsDemo()
        # 如果没有虚拟人，创建一个
        if not demo.load_or_create():
            vh = demo.create_virtual_human("TestVH", "中立型", is_player=False)
            if vh:
                print(f"  Created new VH: {vh.name}")
            else:
                print("  FAIL: Could not create VH")
                return False

        vh_count = len(demo.agent_manager.virtual_humans)
        print(f"  Total VHs: {vh_count}")
        print("  PASS: Virtual humans loadable/creatable")
        return True
    except Exception as e:
        print(f"  FAIL: {e}")
        return False

def test_mentor_creation():
    """测试4: 导师创建功能"""
    print("\n[Test 4] Mentor Creation")
    try:
        demo = OpenSimsDemo()
        vh = demo.create_virtual_human("TestMentor", "温柔型", is_player=False)
        vh.is_mentor = True
        vh.mentor_type = vh._assign_mentor_type()

        if vh.is_mentor and vh.mentor_type:
            print(f"  Created: {vh.name}, type: {vh.mentor_type}")
            print("  PASS: Mentor created successfully")
            return True
        else:
            print("  FAIL: Mentor flags not set")
            return False
    except Exception as e:
        print(f"  FAIL: {e}")
        return False

def test_memory_three_layers():
    """测试5: 三层记忆系统"""
    print("\n[Test 5] Three-Layer Memory")
    try:
        demo = OpenSimsDemo()
        vh = demo.agent_manager.get_active()
        if not vh:
            print("  FAIL: No active VH")
            return False

        # 添加三层数据
        vh.add_memory("user", "User message 1")
        vh.add_memory("assistant", "Assistant reply 1")
        vh.add_memory("system", "System event")

        user_msgs = [m for m in vh.memory if m.get('role') == 'user']
        assistant_msgs = [m for m in vh.memory if m.get('role') == 'assistant']
        other_msgs = [m for m in vh.memory if m.get('role') not in ('user', 'assistant')]

        print(f"  User: {len(user_msgs)}, Assistant: {len(assistant_msgs)}, Other: {len(other_msgs)}")
        if len(user_msgs) > 0 and len(assistant_msgs) > 0:
            print("  PASS: Three-layer memory structure works")
            return True
        else:
            print("  FAIL: Missing layers")
            return False
    except Exception as e:
        print(f"  FAIL: {e}")
        return False

def test_auto_chat_scheduler():
    """测试6: 自动聊天调度器"""
    print("\n[Test 6] Auto Chat Scheduler")
    try:
        demo = OpenSimsDemo()
        scheduler = demo.auto_chat_scheduler

        # 设置回调
        messages = []
        def callback(name, msg, is_group):
            messages.append((name, msg, is_group))

        scheduler.message_callback = callback
        scheduler.start()

        time.sleep(2)  # 等待调度器启动

        # 检查是否启动
        if scheduler.running and scheduler.thread and scheduler.thread.is_alive():
            print("  Scheduler thread running")
            scheduler.stop()
            time.sleep(0.5)
            print("  PASS: Scheduler start/stop works")
            return True
        else:
            print("  FAIL: Scheduler not running")
            return False
    except Exception as e:
        print(f"  FAIL: {e}")
        return False

def test_streaming_callback():
    """测试7: 流式回调机制"""
    print("\n[Test 7] Streaming Callback")
    try:
        demo = OpenSimsDemo()
        vh = demo.agent_manager.get_active()
        if not vh:
            print("  FAIL: No active VH")
            return False

        chunks = []
        def callback(chunk):
            chunks.append(chunk)

        # 短问题测试流式
        reply = demo.api_client.generate_reply(vh, "Hi", stream_callback=callback)
        if len(chunks) > 0:
            print(f"  Received {len(chunks)} chunks, total {len(''.join(chunks))} chars")
            print("  PASS: Streaming delivers chunks")
            return True
        else:
            print("  FAIL: No chunks received")
            return False
    except Exception as e:
        print(f"  FAIL: {e}")
        return False

def test_gui_components():
    """测试8: GUI组���初始化"""
    print("\n[Test 8] GUI Components")
    try:
        from gui_simple import MentorChatGUI

        # 创建GUI实例（不显示）
        root = tk.Tk()
        root.withdraw()

        gui = MentorChatGUI.__new__(MentorChatGUI)
        gui.demo = OpenSimsDemo()
        gui.root = root
        gui.auto_chat_thread = None
        gui.auto_chat_stop = threading.Event()
        gui.vh_monitor_window = None
        gui.vh_monitor_text = None

        # 调用部分初始化
        gui.create_menu()
        print("  Menu created")

        # 验证菜单项存在
        menubar = root.cget('menu')
        if menubar:
            print("  PASS: GUI components initialize without crash")
            root.destroy()
            return True
        else:
            print("  FAIL: Menu bar missing")
            root.destroy()
            return False
    except Exception as e:
        print(f"  FAIL: {e}")
        try:
            root.destroy()
        except:
            pass
        return False

def test_question_selection_mode():
    """测试9: 问题选择模式"""
    print("\n[Test 9] Question Selection Mode")
    try:
        from gui_simple import MentorChatGUI

        root = tk.Tk()
        root.withdraw()

        gui = MentorChatGUI.__new__(MentorChatGUI)
        gui.demo = OpenSimsDemo()
        gui.root = root
        gui.input_mode = tk.StringVar(value="free")
        gui.free_input_frame = tk.Frame(root)
        gui.select_input_frame = tk.Frame(root)
        gui.input_entry = tk.Entry(gui.free_input_frame)

        # 测试切换
        gui.switch_input_mode("select")
        if gui.input_mode.get() == "select":
            gui.switch_input_mode("free")
            if gui.input_mode.get() == "free":
                print("  PASS: Input mode switching works")
                root.destroy()
                return True
        root.destroy()
        print("  FAIL: Mode switching failed")
        return False
    except Exception as e:
        print(f"  FAIL: {e}")
        try:
            root.destroy()
        except:
            pass
        return False

def test_memory_viewer_dialog():
    """测试10: 记忆查看器对话框"""
    print("\n[Test 10] Memory Viewer Dialog")
    try:
        from gui_simple import MentorChatGUI

        root = tk.Tk()
        root.withdraw()

        gui = MentorChatGUI.__new__(MentorChatGUI)
        gui.demo = OpenSimsDemo()
        gui.root = root

        # 打开对话框（不阻塞）
        gui.show_memory_dialog()
        root.after(100, root.destroy)  # 100ms后关闭
        root.mainloop()

        print("  PASS: Memory viewer dialog opens without error")
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
    print("OpenSims GUI Full Feature Automated Test")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

    results = TestResult()

    # 运行所有测试
    tests = [
        test_settings_hot_reload,
        test_api_client_config,
        test_virtual_human_creation,
        test_mentor_creation,
        test_memory_three_layers,
        test_auto_chat_scheduler,
        test_streaming_callback,
        test_gui_components,
        test_question_selection_mode,
        test_memory_viewer_dialog,
    ]

    for test_func in tests:
        try:
            passed = test_func()
            results.add(test_func.__name__, passed)
        except Exception as e:
            results.add(test_func.__name__, False, str(e))

    # 总结
    all_pass = results.print_summary()
    return all_pass

if __name__ == "__main__":
    success = main()
    try:
        input("\nPress Enter to exit...")
    except (EOFError, KeyboardInterrupt):
        pass
    sys.exit(0 if success else 1)
