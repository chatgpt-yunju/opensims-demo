#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""OpenSims Demo 自动化测试（不依赖GUI）"""

from main import OpenSimsDemo
from virtual_human import VirtualHuman
import os

def test_basic_flow():
    """测试基本流程"""
    print("=" * 50)
    print("开始自动化测试")
    print("=" * 50)

    # 清理旧数据
    if os.path.exists("demo_data.json"):
        os.remove("demo_data.json")

    # 1. 创建虚拟人
    demo = OpenSimsDemo()
    demo.create_virtual_human("测试员", "幽默型")
    print(f"[Test] 虚拟人创建成功: {demo.vh}")

    # 2. 发送消息
    reply1 = demo.chat("你好")
    print(f"[Test] 回复1: {reply1}")
    assert reply1, "回复不能为空"

    # 3. 再次发送
    reply2 = demo.chat("你叫什么名字？")
    print(f"[Test] 回复2: {reply2}")
    assert reply2, "第二次回复不能为空"

    # 4. 检查记忆
    assert len(demo.vh.memory) == 4, f"记忆条数应为4，实际为{len(demo.vh.memory)}"  # user+assistant x2
    print(f"[Test] 记忆保存成功，共{len(demo.vh.memory)}条")

    # 5. 检查状态更新
    assert demo.vh.state["energy"] < 100, "能量应消耗"
    print(f"[Test] 状态更新成功: {demo.vh.get_status_text()}")

    # 6. 保存和加载
    demo.storage.save_virtual_human(demo.vh)
    print("[Test] 保存成功")

    # 清空再加载
    demo2 = OpenSimsDemo()
    loaded = demo2.storage.load_virtual_human()
    assert loaded is not None, "加载失败"
    assert loaded.name == "测试员", "名称不一致"
    assert len(loaded.memory) == 4, "记忆条数不一致"
    print(f"[Test] 加载成功: {loaded.name}, 记忆{len(loaded.memory)}条")

    print("\n" + "=" * 50)
    print("[OK] 所有测试通过！")
    print("=" * 50)
    return True

if __name__ == "__main__":
    try:
        test_basic_flow()
    except AssertionError as e:
        print(f"\n[FAIL] 测试失败: {e}")
    except Exception as e:
        print(f"\n[ERROR] 发生错误: {e}")
        import traceback
        traceback.print_exc()