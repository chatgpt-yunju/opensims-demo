#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""验证完整的角色对话+引导系统"""

from main import OpenSimsDemo
import os

# 清理测试数据
if os.path.exists("demo_data.json"):
    os.remove("demo_data.json")

print("=== OpenSims 角色对话系统测试 ===\n")

# 初始化
demo = OpenSimsDemo()
print(f"[初始化] 自动聊天调度器: {'ON' if demo.auto_chat_scheduler.running else 'OFF'}")
print(f"[初始化] 导师触发引擎: {'ON' if demo.mentor_trigger_engine else 'OFF'}")

# 创建玩家
player = demo.create_virtual_human("小明", "中立型", is_player=True)
print(f"[创建] 玩家角色: {player.name}, ID: {player.id}")

# 创建AI角色（其中1个是教师，1个是贵人）
v1 = demo.create_virtual_human("李老师", "严肃型", is_player=False)
v1.job = "教师"
v1._update_mentor_status_from_job()
print(f"[创建] AI角色: {v1.name}, 职业: {v1.job}, is_mentor: {v1.is_mentor}")

v2 = demo.create_virtual_human("王贵人", "温柔型", is_player=False)
v2.job = "贵人"
v2._update_mentor_status_from_job()
print(f"[创建] AI角色: {v2.name}, 职业: {v2.job}, is_mentor: {v2.is_mentor}")

v3 = demo.create_virtual_human("小张", "幽默型", is_player=False)
print(f"[创建] AI角色: {v3.name}, 职业: {v3.job}")

print(f"\n=== 当前角色 ===")
for vh in demo.agent_manager.virtual_humans.values():
    mentor_mark = "[导师]" if getattr(vh, 'is_mentor', False) else ""
    print(f"  {vh.name} ({vh.job}) {mentor_mark}")

print(f"\n=== 测试 1: 玩家与教师对话 ===")
reply = demo.chat("我想找到人生使命，有什么建议吗？", v1)
print(f"李老师: {reply[:80]}...")

print(f"\n=== 玩家成长状态 ===")
if demo.player_growth:
    summary = demo.player_growth.get_growth_summary()
    print(f"  已发现兴趣: {summary['discovered_interests']}")
    print(f"  使命状态: {summary['current_status']}")
    print(f"  引导次数: {summary['total_guidance_sessions']}")

print(f"\n=== 测试 2: 个人对话触发（玩家情绪低落）===")
# 模拟玩家情绪低落：添加一个“失败”事件到life_events
demo.player_growth.life_events.append({
    "type": "challenge_completed",
    "content": "完成了一个 coding 挑战",
    "timestamp": "2025-04-05T10:00:00"
})
demo.player_growth.challenges_completed += 1

# 触发检查
print("执行 _check_mentor_triggers()...")
demo._check_mentor_triggers()

print(f"\n=== 测试 3: 自动聊天（虚拟人间） ===")
print("等待自动聊天调度...")
import time
time.sleep(2)

print(f"\n=== 所有测试完成 ===")
print(f"数据保存至: demo_data.json")

demo.auto_chat_scheduler.stop()
