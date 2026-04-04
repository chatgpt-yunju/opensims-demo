#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
OpenSims Demo - 主程序入口
功能：虚拟人聊天Demo（支持多虚拟人）
"""

import sys
import time
import uuid
from virtual_human import SimPerson
from api_client import APIClient
from storage import Storage
from config import PERSONALITY_PRESETS, AUTO_CHAT_ENABLED
from agents.manager import AgentManager
from auto_chat_scheduler import AutoChatScheduler

class OpenSimsDemo:
    def __init__(self):
        self.storage = Storage()
        self.agent_manager = AgentManager(self.storage)
        self.api_client = APIClient()
        self.auto_chat_scheduler = AutoChatScheduler(
            self.agent_manager,
            self.api_client
        )
        self.auto_chat_scheduler.start()  # 自动聊天调度

    def create_virtual_human(self, name: str, personality_type: str = "中立型", is_player: bool = False) -> SimPerson:
        """创建新虚拟人"""
        personality = PERSONALITY_PRESETS.get(personality_type, PERSONALITY_PRESETS["中立型"])
        vh = self.agent_manager.create_virtual_human(name, personality_type, personality, is_player)
        return vh

    def chat(self, user_input: str, target_vh: SimPerson = None) -> str:
        """单次对话流程（可指定目标虚拟人）"""
        vh = target_vh or self.agent_manager.get_active()
        if not vh:
            return "错误：未选择虚拟人"

        # 1. 添加用户消息到记忆
        vh.add_memory("user", user_input)

        # 2. 调用API生成回复
        print(f"[System] 正在请求AI回复...")
        response = self.api_client.generate_reply(vh, user_input)
        reply = response.get("reply", "（沉默）")

        # 3. 添加助手回复到记忆
        vh.add_memory("assistant", reply)

        # 4. 更新状态（聊天也会消耗精力）
        vh.update_state_after_chat(user_input, response)
        vh.energy = max(0, vh.energy - 5)  # 聊天消耗少量精力
        vh.actions_today += 1

        # 5. 保存所有虚拟人
        self.agent_manager.save_all()

        return reply

    def chat_with_vh(self, vh_id: str, message: str) -> str:
        """与指定ID的虚拟人对话"""
        vh = self.agent_manager.get_virtual_human(vh_id)
        if not vh:
            return f"错误：找不到虚拟人 {vh_id}"
        return self.chat(message, vh)

    def show_status(self, vh: SimPerson = None):
        """显示状态"""
        vh = vh or self.agent_manager.get_active()
        if vh:
            print(f"\n[{vh.name}] {vh.get_status_text()}")
            if hasattr(vh, 'age'):
                # 模拟人生详细状态
                print(vh.get_status_full())
            else:
                print(f"记忆条数: {len(vh.memory)}")
        else:
            print("[System] 未选择虚拟人")

    def list_virtual_humans(self):
        """列出所有虚拟人"""
        vhs = self.agent_manager.list_virtual_humans()
        print("\n" + "=" * 50)
        print(f"虚拟人列表 (共{len(vhs)}个):")
        for vh in vhs:
            active_mark = " [当前]" if vh["is_active"] else ""
            print(f"  {vh['name']} (ID: {vh['id']}){active_mark}")
            print(f"    年龄: {vh.get('age', '?')}, 职业: {vh.get('job', '?')}")
            print(f"    情绪: {vh['state']['mood']}, 健康: {vh['state'].get('health', '?')}/100")
            print(f"    金钱: ${vh.get('money', '?')}")
        print("=" * 50)

    def select_virtual_human(self, vh_id: str):
        """选择虚拟人"""
        self.agent_manager.set_active(vh_id)
        vh = self.agent_manager.get_active()
        if vh:
            print(f"[System] 已切换至虚拟人: {vh.name}")
        else:
            print("[System] 切换失败")

    # ========== 模拟人生行动方法 ==========
    def sim_eat(self):
        vh = self.agent_manager.get_active()
        if not vh or not hasattr(vh, 'eat'):
            return "当前虚拟人无法吃饭"
        return vh.eat()

    def sim_sleep(self):
        vh = self.agent_manager.get_active()
        if not vh or not hasattr(vh, 'sleep'):
            return "当前虚拟人无法睡觉"
        return vh.sleep()

    def sim_work(self):
        vh = self.agent_manager.get_active()
        if not vh or not hasattr(vh, 'work'):
            return "当前虚拟人无法工作"
        return vh.work()

    def sim_find_job(self):
        vh = self.agent_manager.get_active()
        if not vh or not hasattr(vh, 'find_job'):
            return "当前虚拟人无法找工作"
        return vh.find_job()

    def sim_relax(self):
        vh = self.agent_manager.get_active()
        if not vh or not hasattr(vh, 'relax'):
            return "当前虚拟人无法放松"
        return vh.relax()

    def sim_socialize(self):
        vh = self.agent_manager.get_active()
        if not vh or not hasattr(vh, 'socialize'):
            return "当前虚拟人无法社交"
        return vh.socialize()

    def sim_shop(self):
        vh = self.agent_manager.get_active()
        if not vh or not hasattr(vh, 'shop'):
            return "当前虚拟人无法购物"
        return vh.shop()

    def sim_day_pass(self):
        vh = self.agent_manager.get_active()
        if not vh or not hasattr(vh, 'day_pass'):
            return "当前虚拟人无法结束一天"
        return vh.day_pass()

    def run_cli(self):
        """命令行模式（模拟人生游戏）"""
        print("=" * 60)
        print("OpenSims - 模拟人生 (文字版)")
        print("=" * 60)

        # 加载或创建虚拟人
        vhs = self.agent_manager.list_virtual_humans()
        if not vhs:
            print("\n[系统] 欢迎来到模拟人生！请创建角色...")
            print("  提示：你可以创建'自己'来亲自控制，或其他AI角色自动生活")
            name = input("角色昵称: ").strip() or "玩家1"
            types = list(PERSONALITY_PRESETS.keys())
            print(f"可选性格: {', '.join(types)}")
            ptype = input(f"选择性格 [{types[0]}]: ").strip() or types[0]
            is_player = input("这是你要控制的角色吗？(y/N): ").strip().lower() == 'y'
            self.create_virtual_human(name, ptype, is_player)
            print(f"✅ 角色创建成功！{name} {'(你的化身)' if is_player else '(AI自动)'} 开始了人生旅程。")

        # 主游戏循环
        while True:
            vh = self.agent_manager.get_active()
            if not vh:
                print("[系统] 没有活跃角色，请先创建")
                break

            if not vh.alive:
                print(f"\n{'='*60}")
                print(f"⚠️  {vh.name} 已经去世！")
                print(f"   享年 {vh.age:.1f} 岁")
                if vh.death_cause:
                    print(f"   死因: {vh.death_cause}")
                print(f"   累计活了 {vh.day_counter:.0f} 天")
                print(f"{'='*60}")
                print("\n1. 查看遗言（状态）  2. 复活（作弊）  3. 退出")
                choice = input("请选择: ").strip()
                if choice == "1":
                    self.show_status(vh)
                elif choice == "2":
                    vh.alive = True
                    vh.health = 100
                    vh.age = max(0, vh.age - 10)  # 年轻10岁
                    print(f"✨ {vh.name} 复活了！年龄重置为 {vh.age:.1f} 岁")
                else:
                    break
                continue

            # 显示状态
            print("\n" + "=" * 60)
            print(f"    第 {vh.day_counter:.0f} 天   {vh.name}  [{vh.stage}]")
            print("=" * 60)
            print(vh.get_status_full())
            print("-" * 60)

            # 显示选项
            print("行动选项（灵魂永生模式）:")
            print("  1. 吃饭   2. 睡觉   3. 工作   4. 找工作")
            print("  5. 娱乐   6. 社交   7. 购物   8. 聊天（当前）")
            print("  9. 聊天（指定其他人） 10. 结束今天")
            print("  11. 查看所有角色 12. 切换角色 13. 创建AI角色 14. 退出")
            choice = input("请选择行动: ").strip()

            if choice == "1":
                print(f"  >> {vh.name} {self.sim_eat()}")
            elif choice == "2":
                print(f"  >> {vh.name} {self.sim_sleep()}")
            elif choice == "3":
                print(f"  >> {vh.name} {self.sim_work()}")
            elif choice == "4":
                print(f"  >> {vh.name} {self.sim_find_job()}")
            elif choice == "5":
                print(f"  >> {vh.name} {self.sim_relax()}")
            elif choice == "6":
                target = input("  和谁社交？（留空随机）: ").strip()
                if target:
                    print(f"  >> {vh.name} {self.sim_socialize()} {target}")
                else:
                    print(f"  >> {vh.name} {self.sim_socialize()}")
            elif choice == "7":
                print(f"  >> {vh.name} {self.sim_shop()}")
            elif choice == "8":
                # 聊天（当前角色）
                msg = input("  你想对虚拟人说什么？: ").strip()
                if msg:
                    reply = self.chat(msg)
                    print(f"    {vh.name}: {reply[:80]}")
            elif choice == "9":
                # 指挥其他虚拟人聊天
                vhs = self.agent_manager.list_virtual_humans()
                if len(vhs) <= 1:
                    print("  还没有其他虚拟人，先创建一个吧！")
                    continue
                print("  选择对话对象：")
                for v in vhs:
                    if v["id"] != vh.id:
                        print(f"    {v['id']}: {v['name']} ({v['stage']}, {v['job']})")
                target_id = input("  输入ID: ").strip()
                if target_id:
                    msg = input(f"  你想对{v.get('name','?')}说什么？: ").strip()
                    if msg:
                        reply = self.chat_with_vh(target_id, msg)
                        print(f"    {vh.name}: {reply[:80]}")
            elif choice == "10":
                result = self.sim_day_pass()
                print(f"  >> {result}")
            elif choice == "11":
                vhs = self.agent_manager.list_virtual_humans()
                if not vhs:
                    print("  还没有任何虚拟人！")
                else:
                    print("  所有虚拟人：")
                    for v in vhs:
                        active_mark = " [当前]" if v["is_active"] else ""
                        player_mark = " [玩家]" if v.get('is_player', False) else ""
                        alive_mark = "" if v.get('alive', True) else " 💀[已去世]"
                        print(f"    {v['id']}: {v['name']}{player_mark}{active_mark}{alive_mark}")
                        if v.get('alive', True):
                            print(f"      年龄: {v.get('age', '?'):.1f}, 职业: {v.get('job', '?')}, 金钱: ${v.get('money', '?')}")
                        else:
                            print(f"      享年: {v.get('age','?'):.1f}岁, 死因: {v.get('death_cause','?')}")
            elif choice == "12":
                vhs = self.agent_manager.list_virtual_humans()
                if not vhs:
                    print("  还没有任何虚拟人！")
                else:
                    print("  当前角色列表：")
                    for v in vhs:
                        active_mark = " [当前]" if v["is_active"] else ""
                        player_mark = " [玩家]" if v.get('is_player', False) else ""
                        print(f"    {v['id']}: {v['name']}{player_mark}{active_mark}")
                    switch = input("  输入ID切换角色: ").strip()
                    if switch:
                        self.select_virtual_human(switch)
            elif choice == "13":
                # 创建AI角色（非玩家控制）
                name = input("  AI角色昵称: ").strip() or "AI村民"
                types = list(PERSONALITY_PRESETS.keys())
                print(f"  可选性格: {', '.join(types)}")
                ptype = input(f"  选择性格 [{types[0]}]: ").strip() or types[0]
                self.create_virtual_human(name, ptype, is_player=False)
                print(f"  ✅ 创建AI角色 {name} 成功！它将自主生活。")
            elif choice == "14" or choice.lower() in ['quit', 'exit', 'q']:
                print("再见！期待下次人生旅程。")
                # 停止自动聊天调度器
                self.auto_chat_scheduler.stop()
                break
            else:
                print("无效选择")

            # 自动更新心情状态
            vh.update_mood()

            # 每3天自动存档
            if vh.day_counter % 3 == 0:
                self.agent_manager.save_all()
                print("  [系统] 自动存档完成")

# ==================== 测试用main ====================
if __name__ == "__main__":
    demo = OpenSimsDemo()
    demo.run_cli()