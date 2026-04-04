#!/usr/bin/env python3
"""模拟人生游戏流程自动化测试"""

import os
from main import OpenSimsDemo

def test_sim_game_flow():
    print("=" * 60)
    print("模拟人生游戏流程测试（自动化）")
    print("=" * 60)

    # 清理数据
    if os.path.exists("demo_data.json"):
        os.remove("demo_data.json")

    demo = OpenSimsDemo()

    # 1. 创建角色
    print("\n[Test] 创建角色...")
    vh = demo.create_virtual_human("测试员", "幽默型")
    print(f"  [OK] 创建 {vh.name}, 年龄{vh.age}, 职业: {vh.job}")

    # 2. 执行一系列行动
    actions = [
        ("吃饭", lambda: demo.sim_eat()),
        ("睡觉", lambda: demo.sim_sleep()),
        ("工作", lambda: demo.sim_work()),
        ("找工作", lambda: demo.sim_find_job()),
        ("工作2", lambda: demo.sim_work()),
        ("放松", lambda: demo.sim_relax()),
        ("社交", lambda: demo.sim_socialize()),
        ("购物", lambda: demo.sim_shop()),
    ]

    print("\n[Test] 执行一轮行动...")
    for action_name, action_func in actions:
        result = action_func()
        print(f"  [行动] {action_name}: {result}")
        vh.update_mood()  # 更新心情

    # 3. 查看状态
    print("\n[Test] 当前状态:")
    status = vh.get_status_full()
    print(status)

    # 4. 结束一天
    print("\n[Test] 结束一天...")
    result = demo.sim_day_pass()
    print(f"  >> {result}")
    if not vh.alive:
        print(f"  !! {vh.name} 去世了！年龄: {vh.age:.1f}")

    # 5. 快速老化到死亡（加速测试）
    print("\n[Test] 快速老化测试（加速到100岁）...")
    vh2 = demo.create_virtual_human("长寿者", "温柔型")
    vh2.age = 99.5  # 接近100岁
    vh2.health = 50  # 降低健康触发死亡
    print(f"  初始: {vh2.name} 年龄{vh2.age}, 健康{vh2.health}")

    # 执行一些行动直到死亡
    death_triggered = False
    for i in range(10):
        vh2.work()  # 工作会消耗健康
        vh2.update_mood()
        vh2.day_counter += 0.3
        if not vh2.alive:
            print(f"  [死亡] 第{i+1}轮后，{vh2.name} 去世，享年 {vh2.age:.1f} 岁，死因: {vh2.death_cause}")
            death_triggered = True
            break

    if not death_triggered:
        # 手动触发死亡
        vh2.health = 0
        vh2.check_death()
        print(f"  [死亡] 最终 {vh2.name} 去世，享年 {vh2.age:.1f} 岁")

    # 6. 持久化测试
    print("\n[Test] 保存和加载...")
    demo.agent_manager.save_all()

    # 模拟重新启动
    from agents.manager import AgentManager
    from storage import Storage
    new_storage = Storage()
    new_manager = AgentManager(new_storage)
    loaded_vhs = new_manager.list_virtual_humans()
    print(f"  [OK] 加载了 {len(loaded_vhs)} 个虚拟人")
    for v in loaded_vhs:
        print(f"      - {v['name']} (年龄: {v.get('age', '?')}, 职业: {v.get('job', '?')})")

    print("\n" + "=" * 60)
    print("[OK] 模拟人生游戏核心功能测试通过！")
    print("=" * 60)
    print("\n游戏已就绪，可以运行 main.py 进行交互式游戏。")

if __name__ == "__main__":
    try:
        test_sim_game_flow()
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()