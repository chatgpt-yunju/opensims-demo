#!/usr/bin/env python3
"""多虚拟人管理测试"""

import os
from main import OpenSimsDemo
from config import PERSONALITY_PRESETS

def test_multi_virtual_humans():
    print("=" * 60)
    print("多虚拟人管理测试")
    print("=" * 60)

    # 清理数据
    if os.path.exists("demo_data.json"):
        os.remove("demo_data.json")

    demo = OpenSimsDemo()

    # 1. 创建两个虚拟人
    print("\n[Test] 创建虚拟人...")
    vh1 = demo.create_virtual_human("小美", "温柔型")
    print(f"  [OK] 创建 {vh1.name} (ID: {vh1.id})")
    vh2 = demo.create_virtual_human("小王", "幽默型")
    print(f"  [OK] 创建 {vh2.name} (ID: {vh2.id})")

    # 2. 检查活跃虚拟人
    active = demo.agent_manager.get_active()
    assert active is not None, "应有活跃虚拟人"
    assert active.name == "小王", "最后创建的应为活跃"
    print(f"  [OK] 活跃虚拟人: {active.name}")

    # 3. 切换虚拟人
    print("\n[Test] 切换虚拟人...")
    demo.select_virtual_human(vh1.id)
    active = demo.agent_manager.get_active()
    assert active.name == "小美", "切换应成功"
    print(f"  [OK] 切换至 {active.name}")

    # 4. 发送消息（Mock模式）
    print("\n[Test] 发送消息...")
    reply = demo.chat("你好，小美！")
    assert reply, "应有回复"
    print(f"  [OK] 收到回复 (长度: {len(reply)})")

    # 5. 验证记忆和状态
    vh = demo.agent_manager.get_active()
    assert len(vh.memory) >= 2, "应有对话记忆"
    print(f"  [OK] 记忆条数: {len(vh.memory)}")
    status = vh.get_status_text()
    print(f"  [OK] 当前状态: {status}")

    # 6. 列出所有虚拟人
    print("\n[Test] 列出所有虚拟人...")
    demo.list_virtual_humans()

    # 7. 测试持久化
    print("\n[Test] 测试保存和加载...")
    demo.agent_manager.save_all()
    # 创建新的 Manager 验证加载
    from storage import Storage
    new_storage = Storage()
    from agents.manager import AgentManager
    new_manager = AgentManager(new_storage)
    loaded_vhs = new_manager.list_virtual_humans()
    assert len(loaded_vhs) == 2, "应加载2个虚拟人"
    print(f"  [OK] 加载 {len(loaded_vhs)} 个虚拟人")

    print("\n" + "=" * 60)
    print("[OK] 多虚拟人管理测试通过！")
    print("=" * 60)

if __name__ == "__main__":
    try:
        test_multi_virtual_humans()
    except AssertionError as e:
        print(f"\n[FAIL] 测试失败: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"\n[ERROR] 发生异常: {e}")
        import traceback
        traceback.print_exc()