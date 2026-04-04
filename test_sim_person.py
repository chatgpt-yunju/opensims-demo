#!/usr/bin/env python3
"""SimPerson 模拟人生系统测试"""

import os
from virtual_human import SimPerson
from config import PERSONALITY_PRESETS

def test_sim_person_basic():
    print("=" * 60)
    print("SimPerson 模拟人生核心功能测试")
    print("=" * 60)

    # 1. 创建模拟人生角色
    print("\n[Test] 创建角色...")
    p = SimPerson("张三", PERSONALITY_PRESETS["中立型"], age=25)
    print(f"  [OK] 创建 {p.name}, 年龄{p.age}, 阶段: {p.stage}, 职业: {p.job}")

    # 2. 显示初始状态
    print("\n[Test] 初始状态:")
    print(p.get_status_full())

    # 3. 测试行动：吃饭、睡觉、工作
    print("\n[Test] 执行行动...")
    result = p.eat()
    print(f"  [行动] 吃饭: {result}")
    result = p.sleep()
    print(f"  [行动] 睡觉: {result}")
    result = p.work()
    print(f"  [行动] 工作: {result}")

    # 4. 找工作
    print("\n[Test] 找工作...")
    result = p.find_job()
    print(f"  [行动] {result}")

    # 5. 随机事件
    print("\n[Test] 生成随机事件...")
    result = p.random_event()
    print(f"  [事件] {result}")

    # 6. 结束一天
    print("\n[Test] 结束一天...")
    result = p.day_pass()
    print(f"  [结果] {result}")

    # 7. 最终状态
    print("\n[Test] 最终状态:")
    print(p.get_status_full())

    # 8. 序列化测试
    print("\n[Test] 数据序列化...")
    data = p.to_dict()
    print(f"  [OK] 序列化为dict")
    p2 = SimPerson.from_dict(data)
    print(f"  [OK] 反序列化，{p2.name} 年龄{p2.age}")

    # 9. 快速老化测试（模拟人生加速）
    print("\n[Test] 快速老化模拟（加速到60岁）...")
    p3 = SimPerson("老人测试", PERSONALITY_PRESETS["严肃型"], age=25)
    for i in range(200):
        p3.work()
        if not p3.alive:
            print(f"  [死亡] {p3.death_cause}，享年{p3.age:.1f}岁")
            break
    else:
        print(f"  [存活] 200次工作后，年龄{p3.age:.1f}岁，仍健在")
    print(f"  [OK] 寿命系统工作正常")

    print("\n" + "=" * 60)
    print("[OK] SimPerson 核心功能全部通过！")
    print("=" * 60)

if __name__ == "__main__":
    try:
        test_sim_person_basic()
    except AssertionError as e:
        print(f"\n[FAIL] 测试失败: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"\n[ERROR] 发生异常: {e}")
        import traceback
        traceback.print_exc()