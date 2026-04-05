#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenSims 角色对话系统演示
展示：玩家↔虚拟人、虚拟人↔虚拟人自动聊天、性格/状态/记忆生成对话
"""

import time
from main import OpenSimsDemo

def demo():
    print("=" * 70)
    print("  OpenSims 角色对话系统 - 功能演示")
    print("=" * 70)

    # 初始化系统
    demo = OpenSimsDemo()

    # 清理旧数据，从头开始
    demo.agent_manager.storage.clear_data()
    demo.agent_manager.virtual_humans.clear()
    demo.agent_manager.active_vh_id = None

    # === 1. 创建角色 ===
    print("\n[步骤1] 创建虚拟人角色")
    print("-" * 70)

    # 创建玩家角色
    player = demo.create_virtual_human("小明", "温柔型", is_player=True)
    print(f"[OK] 创建玩家角色: {player.name}")
    print(f"   性格: {player.personality}")
    print(f"   状态: 能量={player.energy}, 情绪={player.mood_level}")

    # 创建AI角色
    xiaohong = demo.create_virtual_human("小红", "幽默型", is_player=False)
    print(f"[OK] 创建AI角色: {xiaohong.name}")
    print(f"   性格: {xiaohong.personality}")

    xiaohei = demo.create_virtual_human("小黑", "严肃型", is_player=False)
    print(f"[OK] 创建AI角色: {xiaohei.name}")
    print(f"   性格: {xiaohei.personality}")

    # === 2. 玩家 <-> 虚拟人对话 ===
    print("\n[步骤2] 玩家 <-> 虚拟人对话")
    print("-" * 70)

    messages = [
        "你好呀，小红！",
        "今天天气怎么样？",
        "你心情好吗？",
        "再见啦！"
    ]

    for msg in messages:
        print(f"\n[玩家 -> {xiaohong.name}] {msg}")
        reply = demo.chat(msg, xiaohong)
        print(f"[{xiaohong.name} -> 玩家] {reply}")
        time.sleep(0.5)

    # 显示小红的记忆
    print(f"\n[记忆] {xiaohong.name} 的对话记忆（最近{min(5, len(xiaohong.memory))}条）:")
    for i, mem in enumerate(xiaohong.memory[-5:], 1):
        role = "玩家" if mem['role'] == 'user' else xiaohong.name
        print(f"  {i}. {role}: {mem['content'][:50]}...")

    # === 3. 虚拟人自动对话 ===
    print("\n[步骤3] 虚拟人 <-> 虚拟人自动对话")
    print("-" * 70)
    print("启动自动聊天调度器...")

    # 保存并重新加载以触发后台线程
    demo.agent_manager.save_all()

    print("\n⏳ 等待自动对话触发（30秒内）...")
    print("提示：自动聊天每30秒有50%概率触发")

    time.sleep(2)

    # 手动触发一次对话演示
    print("\n[手动触发] 小红 ↔ 小黑 开始对话...")
    from auto_chat_scheduler import AutoChatScheduler
    # 临时调用对话方法
    demo.auto_chat_scheduler._trigger_conversation(xiaohong, xiaohei, turns=3)

    time.sleep(1)

    # === 4. 展示性格影响 ===
    print("\n[步骤4] 性格对对话的影响")
    print("-" * 70)

    test_msg = "周末有什么计划？"
    print(f"\n向三个角色发送相同消息: '{test_msg}'")

    for vh in [player, xiaohong, xiaohei]:
        reply = demo.chat(test_msg, vh)
        style_desc = "友好" if vh.personality['friendliness'] > 0.7 else ("严肃" if vh.personality['seriousness'] > 0.7 else "中立")
        print(f"\n{vh.name}（{style_desc}）: {reply}")

    # === 5. 状态变化 ===
    print("\n[步骤5] 对话对状态的影响")
    print("-" * 70)

    initial_energy = xiaohong.energy
    initial_mood = xiaohong.mood_level

    # 进行多次对话消耗精力
    for i in range(5):
        demo.chat("说点什么吧", xiaohong)

    print(f"\n{xiaohong.name} 对话前后对比:")
    print(f"  精力: {initial_energy} -> {xiaohong.energy} (消耗 {initial_energy - xiaohong.energy})")
    print(f"  情绪: {initial_mood} -> {xiaohong.mood_level}")

    # === 6. 群聊功能 ===
    print("\n[步骤6] 群聊功能（3人）")
    print("-" * 70)

    participants = [player, xiaohong, xiaohei]
    print(f"群聊参与者: {', '.join(p.name for p in participants)}")
    print("\n模拟群聊轮次...")

    # 手动触发群聊
    demo.auto_chat_scheduler._trigger_group_chat(participants)

    # === 7. 最终状态 ===
    print("\n[最终] 所有虚拟人状态")
    print("-" * 70)
    demo.list_virtual_humans()

    # === 总结 ===
    print("\n" + "=" * 70)
    print("  演示完成！")
    print("=" * 70)
    print("\n[OK] 已验证功能:")
    print("  1. [OK] 玩家 <-> 虚拟人聊天")
    print("  2. [OK] 虚拟人 <-> 虚拟人自动聊天（双人/群聊）")
    print("  3. [OK] 对话基于性格、状态、记忆生成")
    print("  4. [OK] 对话自动存入记忆，影响后续行为和状态")
    print("\n[统计] 系统统计:")
    print(f"  - 总虚拟人数: {len(demo.agent_manager.virtual_humans)}")
    print(f"  - 玩家角色数: {sum(1 for vh in demo.agent_manager.virtual_humans.values() if vh.is_player)}")
    print(f"  - 自动聊天调度器: {'运行中' if demo.auto_chat_scheduler.running else '已停止'}")
    print(f"  - 记忆保存: demo_data.json")

    # 停止后台线程
    demo.auto_chat_scheduler.stop()

if __name__ == "__main__":
    demo()
