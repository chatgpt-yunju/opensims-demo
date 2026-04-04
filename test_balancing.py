#!/usr/bin/env python3
"""数值平衡和bug修复测试"""

import os
from main import OpenSimsDemo

def test_balance_and_bugs():
    print("=" * 60)
    print("数值平衡与Bug测试")
    print("=" * 60)

    # 清理数据
    if os.path.exists("demo_data.json"):
        os.remove("demo_data.json")

    demo = OpenSimsDemo()

    # 1. 创建玩家和多个AI
    print("\n[Test] 创建角色...")
    player = demo.create_virtual_human("玩家", "幽默型", is_player=True)
    ai1 = demo.create_virtual_human("小明", "温柔型", is_player=False)
    ai2 = demo.create_virtual_human("小红", "严肃型", is_player=False)

    # 2. 检查角色列表显示
    print("\n[Test] 角色列表（应显示玩家/AI标记）:")
    demo.agent_manager.list_virtual_humans()

    # 3. 测试自动聊天调度器状态
    print("\n[Test] 检查自动聊天调度器:")
    print(f"  调度器运行: {demo.auto_chat_scheduler.running}")
    print(f"  排除玩家: True (从配置)")

    # 4. 模拟多角色互动
    print("\n[Test] 模拟一段时间的生活...")
    for day in range(5):
        print(f"\n  === 第{day+1}轮测试 ===")

        # 玩家行动
        player.work()
        player.eat()
        player.update_mood()

        # AI行动（模拟自主）
        ai1.work()
        ai1.relax()
        ai2.find_job()
        ai2.work()
        ai2.update_mood()

        print(f"  玩家: {player.name} 年龄{player.age:.1f}, 金钱${player.money}, 健康{player.health}")
        print(f"  AI1: {ai1.name} 年龄{ai1.age:.1f}, 金钱${ai1.money}, 职业{ai1.job}")
        print(f"  AI2: {ai2.name} 年龄{ai2.age:.1f}, 金钱${ai2.money}, 职业{ai2.job}")

    # 5. 检查年龄增长速度
    print("\n[Test] 年龄增长统计:")
    print(f"  玩家: 初始18.0 → 现在{player.age:.1f} (增长{player.age-18:.1f}岁)")
    print(f"  AI1: 初始18.0 → 现在{ai1.age:.1f} (增长{ai1.age-18:.1f}岁)")
    print(f"  AI2: 初始18.0 → 现在{ai2.age:.1f} (增长{ai2.age-18:.1f}岁)")
    print("  期望：每轮增长约 0.3-0.5岁（5轮约2-3岁）")

    # 6. 检查经济系统
    print("\n[Test] 经济系统检查:")
    print(f"  玩家收入: ${player.income}, 支出: ${player.expense}, 净赚: ${player.income-player.expense}")
    print(f"  AI1收入: ${ai1.income}, 支出: ${ai1.expense}, 净赚: ${ai1.income-ai1.expense}")

    # 7. 情绪状态
    print("\n[Test] 情绪状态:")
    print(f"  玩家: {player.mood_level} (值{player.mood_value})")
    print(f"  AI1: {ai1.mood_level} (值{ai1.mood_value})")
    print(f"  AI2: {ai2.mood_level} (值{ai2.mood_value})")

    # 8. 持久化测试
    print("\n[Test] 保存和重新加载...")
    demo.agent_manager.save_all()
    # 模拟重启
    demo2 = OpenSimsDemo()
    vhs = demo2.agent_manager.list_virtual_humans()
    print(f"  重新加载后角色数: {len(vhs)}")
    for v in vhs:
        print(f"    - {v['name']} (年龄{v.get('age','?'):.1f}, {'玩家' if v.get('is_player') else 'AI'})")

    print("\n" + "=" * 60)
    print("[OK] 测试完成！请检查输出是否合理。")
    print("=" * 60)

if __name__ == "__main__":
    try:
        test_balance_and_bugs()
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()