#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试引导日志查看功能"""

from main import OpenSimsDemo
import os

# 清理旧数据
if os.path.exists("demo_data.json"):
    os.remove("demo_data.json")

demo = OpenSimsDemo()

# 创建玩家
player = demo.create_virtual_human("测试玩家", "中立型", is_player=True)
print(f"创建玩家: {player.name}")

# 创建导师
teacher = demo.create_virtual_human("李老师", "严肃型", is_player=False)
teacher.job = "教师"
teacher._update_mentor_status_from_job()

mentor = demo.create_virtual_human("王贵人", "温柔型", is_player=False)
mentor.job = "贵人"
mentor._update_mentor_status_from_job()

print(f"创建导师: {teacher.name} (教师), {mentor.name} (贵人)")

# 模拟几次对话
print("\n=== 模拟对话 ===")
for i in range(3):
    reply = demo.chat(f"我最近在探索新的兴趣，有什么建议吗？", teacher)
    print(f"[对话{i+1}] 玩家 -> 李老师: 对话完成")

# 模拟完成挑战
demo.player_growth.complete_challenge("编程小项目", "完成了第一个Python脚本")

# 添加一些使命线索
demo.player_growth.add_mission_clue("我喜欢创造东西")
demo.player_growth.add_mission_clue("编程让我感到充实")
demo.player_growth.add_mission_clue("我想用技术帮助他人")

# 查看引导日志
print("\n" + "="*70)
print("查看引导日志...")
demo.show_guidance_log()

demo.auto_chat_scheduler.stop()
