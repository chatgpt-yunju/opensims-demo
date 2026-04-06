#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
OpenSims Demo - 主程序入口
功能：虚拟人聊天Demo（支持多虚拟人）
"""

import sys
import time
import uuid
from typing import Optional
from virtual_human import SimPerson
from api_client import APIClient
from storage import Storage
from config import PERSONALITY_PRESETS, AUTO_CHAT_ENABLED
from agents.manager import AgentManager
from auto_chat_scheduler import AutoChatScheduler
from player_growth import PlayerGrowth
from mentor_trigger import MentorTriggerEngine
try:
    from build_info import __version__ as APP_VERSION
except ImportError:
    APP_VERSION = "1.0.2-dev"

class OpenSimsDemo:
    def __init__(self):
        self.storage = Storage()
        self.agent_manager = AgentManager(self.storage)
        self.api_client = APIClient()
        self.auto_chat_scheduler = AutoChatScheduler(
            self.agent_manager,
            self.api_client
        )
        # 注意：auto_chat_scheduler 不再自动启动
        # - CLI模式：需要在 run_cli 中根据配置启动
        # - GUI模式：使用独立的自动聊天线程（gui_simple.py 中实现）

        # 玩家成长系统（延迟初始化，在加载角色后）
        self.player_growth: Optional[PlayerGrowth] = None
        self.mentor_trigger_engine: Optional[MentorTriggerEngine] = None

    @property
    def vh(self) -> Optional[SimPerson]:
        """获取当前活跃虚拟人（供GUI使用）"""
        return self.agent_manager.get_active()

    def load_or_create(self) -> bool:
        """加载或创建虚拟人（返回是否成功）"""
        # 加载所有数据后，初始化玩家成长系统
        active = self.agent_manager.get_active()
        if active:
            # 查找玩家角色
            for vh in self.agent_manager.virtual_humans.values():
                if vh.is_player:
                    self._init_player_growth(vh)
                    break
        return active is not None

    def _init_player_growth(self, player: SimPerson):
        """初始化玩家成长系统"""
        growth_data = self.storage.load_all_virtual_humans()
        if growth_data and "player_growth" in growth_data:
            self.player_growth = PlayerGrowth.from_dict(growth_data["player_growth"])
        else:
            self.player_growth = PlayerGrowth(player.id)
            self._save_player_growth()
        print(f"[成长系统] 已加载玩家成长数据")

        # 将 player_growth 引用传递给自动聊天调度器（用于社交网络效应）
        self.auto_chat_scheduler.set_player_growth(self.player_growth)

        # 初始化导师触发引擎
        self.mentor_trigger_engine = MentorTriggerEngine(
            self.agent_manager,
            self.player_growth
        )
        print(f"[触发引擎] 导师主动引导系统已启动")

    def _save_player_growth(self):
        """保存玩家成长数据"""
        if self.player_growth:
            # 读取现有数据
            all_data = self.storage.load_all_virtual_humans() or {}
            all_data["player_growth"] = self.player_growth.export_to_dict()
            self.storage.save_all(all_data)

    def _analyze_player_interests(self, vh: SimPerson, user_input: str, reply: str):
        """AI分析玩家兴趣（从对话中提取线索）"""
        if not self.player_growth:
            return

        # 简单关键词匹配（未来可用NLP）
        interest_keywords = {
            "编程": ["编程", "代码", "程序", "开发", "软件"],
            "设计": ["设计", "美术", "创意", "艺术", "绘画"],
            "商业": ["创业", "商业", "赚钱", "生意", "市场"],
            "写作": ["写作", "文章", "内容", "文案", "故事"],
            "教育": ["学习", "知识", "教育", "教学", "老师"],
            "音乐": ["音乐", "唱歌", "乐器", "作曲"],
            "运动": ["运动", "健身", "锻炼", "跑步"],
            "社交": ["朋友", "社交", "人际关系", "团队"]
        }

        combined_text = (user_input + " " + reply).lower()
        for interest, keywords in interest_keywords.items():
            if any(k in combined_text for k in keywords):
                if interest not in vh.discovered_player_interests:
                    vh.discovered_player_interests.append(interest)
                if interest not in self.player_growth.discovered_interests:
                    self.player_growth.add_interest(interest, source=vh.name)
                    print(f"[兴趣发现] {vh.name} 发现玩家对 '{interest}' 感兴趣")

    def _update_growth_from_chat(self, vh: SimPerson, user_input: str, reply: str):
        """从对话中更新玩家成长"""
        # 记录这次引导
        guidance_types = ["explore_interest", "skill_building", "mission_synthesis", "mission_confirmation"]
        # 简单判断类型（未来可用分类器）
        if "挑战" in reply or "任务" in reply:
            g_type = "skill_building"
        elif "使命" in reply or "人生" in reply:
            g_type = "mission_synthesis"
        else:
            g_type = "explore_interest"

        self.player_growth.record_guidance(
            mentor_name=vh.name,
            guidance_type=g_type,
            content=reply[:100]  # 截断存储
        )

    def _check_mentor_triggers(self):
        """检查导师主动触发"""
        if not self.mentor_trigger_engine:
            return

        # 检查是否需要触发导师主动引导
        trigger = self.mentor_trigger_engine.check_triggers()
        if not trigger:
            return

        mentor_id = trigger["mentor_id"]
        message = trigger["suggested_initiative"]
        mentor_vh = self.agent_manager.get_virtual_human(mentor_id)
        if not mentor_vh:
            return

        # 记录导师主动发话
        mentor_vh.add_memory("assistant", message)

        # 玩家接收
        player = self.agent_manager.get_active()
        if player and player.is_player:
            player.add_memory("user", message)
            # 关系度提升
            mentor_vh.update_relationship_with_player(2.0, "proactive_guidance")
            mentor_vh.mentor_trigger_count += 1
            print(f"\n[导师主动] {mentor_vh.name}: {message}")
            print(f"[关系] 关系度提升，当前: {mentor_vh.get_relationship_with_player():.0f}")

        # 保存
        self.agent_manager.save_all()
        self._save_player_growth()

    def create_virtual_human(self, name: str, personality_type: str = "中立型", is_player: bool = False) -> SimPerson:
        """创建新虚拟人"""
        personality = PERSONALITY_PRESETS.get(personality_type, PERSONALITY_PRESETS["中立型"])
        vh = self.agent_manager.create_virtual_human(name, personality_type, personality, is_player)
        if is_player:
            self._init_player_growth(vh)
        return vh

    def chat(self, user_input: str, target_vh: SimPerson = None) -> str:
        """单次对话流程（可指定目标虚拟人）"""
        vh = target_vh or self.agent_manager.get_active()
        if not vh:
            return "错误：未选择虚拟人"

        # 添加用户消息到记忆
        vh.add_memory("user", user_input)

        # 记录对话前的状态
        prev_relationship = vh.get_relationship_with_player()

        # 判断是否为玩家角色与AI虚拟人的对话
        is_player_talking_to_ai = vh.is_player and not target_vh  # 玩家主动找当前AI聊天
        is_ai_talking_to_player = not vh.is_player and (target_vh and target_vh.is_player)  # AI回应玩家的聊天

        # 2. 生成回复
        if self.player_growth and (is_player_talking_to_ai or is_ai_talking_to_player):
            # 使命引导模式
            if is_ai_talking_to_player:
                # AI对玩家使用引导式对话
                reply = vh.guide_player_growth(user_input, self.player_growth)
            else:
                # 玩家对AI，生成普通回复（但AI会暗中观察玩家兴趣）
                response = self.api_client.generate_reply(vh, user_input)
                reply = response.get("reply", "（沉默）")
                # AI在回复中可能收集玩家兴趣线索
                self._analyze_player_interests(vh, user_input, reply)
        else:
            # 普通对话模式
            print(f"[System] 正在请求AI回复...")
            response = self.api_client.generate_reply(vh, user_input)
            reply = response.get("reply", "（沉默）")

        # 3. 添加助手回复到记忆
        vh.add_memory("assistant", reply)

        # 4. 更新状态
        vh.update_state_after_chat(user_input, {"reply": reply})
        vh.energy = max(0, vh.energy - 5)
        vh.actions_today += 1

        # 5. 更新玩家成长（如果涉及）
        if self.player_growth and is_player_talking_to_ai:
            self._update_growth_from_chat(vh, user_input, reply)

        # 6. 更新关系度（关键：对话增进关系）
        if is_player_talking_to_ai or is_ai_talking_to_player:
            # 每次有效对话增加关系度
            relationship_gain = 2.0  # 基础增进
            # 如果回复质量高（长度>50字符），额外增加
            if len(reply) > 50:
                relationship_gain += 1.0
            # 使用新方法更新关系度
            actual_gain = vh.update_relationship_with_player(relationship_gain, "dialogue")
            print(f"[关系] {vh.name} 与玩家关系: {prev_relationship:.0f} -> {prev_relationship + actual_gain:.0f}")

        # 7. 保存
        self.agent_manager.save_all()
        self._save_player_growth()

        # 8. 检查导师主动触发
        self._check_mentor_triggers()

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

    def show_guidance_log(self):
        """显示引导日志和玩家成长状态"""
        if not self.player_growth:
            print("[引导日志] 未初始化玩家成长系统")
            return

        print("\n" + "=" * 70)
        print("  玩家成长与引导日志")
        print("=" * 70)

        # 1. 玩家成长摘要
        summary = self.player_growth.get_growth_summary()
        print(f"\n【玩家当前状态】")
        print(f"  使命状态: {summary['current_status']}")
        if summary['life_mission']:
            print(f"  [OK] 已确认人生使命: {summary['life_mission']}")
        else:
            print(f"  [Pending] 尚未确认人生使命")

        print(f"\n【成长指标】")
        print(f"  已发现兴趣领域: {', '.join(summary['discovered_interests']) if summary['discovered_interests'] else '无'}")
        print(f"  完成挑战数: {summary['challenges_completed']}")
        print(f"  使命线索数: {summary['mission_clues_count']}")
        print(f"  总引导次数: {summary['total_guidance_sessions']}")

        if summary['top_skills']:
            print(f"\n【技能熟练度 Top 5】")
            for skill, level in summary['top_skills']:
                bar = "█" * int(level / 10) + "░" * (10 - int(level / 10))
                print(f"  {skill}: {bar} {level:.0f}%")

        # 2. 引导历史记录
        print(f"\n【最近引导记录】")
        history = self.player_growth.guidance_history
        if not history:
            print("  （暂无引导记录）")
        else:
            recent = history[-10:]  # 最近10条
            for i, entry in enumerate(reversed(recent), 1):
                mentor = entry.get('mentor', 'unknown')
                gtype = entry.get('type', 'unknown')
                content = entry.get('content', '')[:60]
                timestamp = entry.get('timestamp', '')[:10]
                print(f"  {i}. [{timestamp}] {mentor} ({gtype}): {content}...")

        # 3. 使命线索
        if self.player_growth.mission_clues:
            print(f"\n【使命线索】")
            for i, clue in enumerate(self.player_growth.mission_clues[-5:], 1):
                clue_text = clue.get('clue', '')
                context = clue.get('context', '')
                connections = clue.get('connections', [])
                print(f"  {i}. {clue_text}")
                if context:
                    print(f"     上下文: {context}")
                if connections:
                    print(f"     关联: {', '.join(connections)}")

        # 4. 人生事件
        if self.player_growth.life_events:
            print(f"\n【最近人生事件】")
            recent_events = self.player_growth.life_events[-5:]
            for i, event in enumerate(reversed(recent_events), 1):
                etype = event.get('type', 'unknown')
                content = event.get('content', '')
                timestamp = event.get('timestamp', '')[:10]
                print(f"  {i}. [{timestamp}] {content} (类型: {etype})")

        # 5. 导师关系度
        print(f"\n【导师关系度】")
        mentors = [vh for vh in self.agent_manager.virtual_humans.values()
                   if getattr(vh, 'is_mentor', False)]
        if not mentors:
            print("  （暂无导师）")
        else:
            for mentor in sorted(mentors, key=lambda v: v.get_relationship_with_player(), reverse=True):
                rel = mentor.get_relationship_with_player()
                status = "亲密" if rel >= 80 else "友好" if rel >= 60 else "中立" if rel >= 40 else "疏远"
                print(f"  {mentor.name}: {rel:.0f} ({status})")

        print("\n" + "=" * 70)

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

    def sim_create_xiaohongshu_post(self):
        vh = self.agent_manager.get_active()
        if not vh or not hasattr(vh, 'create_xiaohongshu_post'):
            return "当前虚拟人无法发布小红书笔记（需要职业：小红书博主）"
        if vh.job != "小红书博主":
            return f"{vh.name} 不是小红书博主！请先找工作或转职。"
        return vh.create_xiaohongshu_post()

    def sim_day_pass(self):
        vh = self.agent_manager.get_active()
        if not vh or not hasattr(vh, 'day_pass'):
            return "当前虚拟人无法结束一天"
        return vh.day_pass()

    def run_cli(self):
        """命令行模式（模拟人生游戏）"""
        print("=" * 60)
        print(f"OpenSims v{APP_VERSION} - 导师引导模式")
        print("=" * 60)

        # 根据配置启动自动聊天调度器（CLI模式）
        if AUTO_CHAT_ENABLED:
            self.auto_chat_scheduler.start()
            print("[系统] 自动聊天调度器已启动")
        else:
            print("[系统] 自动聊天调度器已禁用（配置中关闭）")

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

            # 显示选项 - 导师引导为核心
            print("\n" + "=" * 60)
            print("  主菜单（导师引导优先）")
            print("=" * 60)
            print("  1. 💬 与导师对话（当前角色）")
            print("  2. 📊 查看成长日志")
            print("  3. 👥 查看所有角色")
            print("  4. 🔄 切换角色")
            print("  5. ➕ 创建AI角色")
            print("  6. ⏳ 结束今天")
            print("  7. ⚙️  更多选项")
            print("  8. 🚪 退出")
            print("-" * 60)

            # 显示导师提示（如果有）
            mentors = [vh for vh in self.agent_manager.virtual_humans.values()
                      if getattr(vh, 'is_mentor', False)]
            if mentors:
                print(f"[导师提醒] 你有 {len(mentors)} 位导师陪伴：")
                for m in mentors:
                    rel = m.get_relationship_with_player()
                    print(f"  - {m.name} (关系: {rel:.0f})")
                print("-" * 60)

            choice = input("请选择 (1-8): ").strip()

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
                # 小红书发布
                if vh.job != "小红书博主":
                    print(f"  注意：{vh.name} 当前职业是 {vh.job}，不是小红书博主")
                    confirm = input("  是否要发布小红书笔记？（仍会执行，但效果可能不佳）(y/N): ").strip().lower()
                    if confirm != 'y':
                        continue
                print(f"  >> {vh.name} 正在撰写小红书笔记...")
                result = self.sim_create_xiaohongshu_post()
                print(f"  {result}")
            elif choice == "9":
                # 聊天（当前角色）
                msg = input("  你想对虚拟人说什么？: ").strip()
                if msg:
                    reply = self.chat(msg)
                    print(f"    {vh.name}: {reply[:80]}")
            elif choice == "10":
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
            elif choice == "11":
                # 群聊模式（选择多个角色一起聊天）
                vhs = self.agent_manager.list_virtual_humans()
                if len(vhs) < 3:
                    print("  需要至少3个虚拟人才能群聊")
                    continue
                print("  选择群聊参与者（用逗号分隔ID，至少2人）:")
                for v in vhs:
                    if v["id"] != vh.id:
                        print(f"    {v['id']}: {v['name']} ({v['stage']}, {v['job']})")
                ids_input = input("  输入ID（例如: abc,def,ghi）: ").strip()
                if ids_input:
                    ids = [i.strip() for i in ids_input.split(',') if i.strip()]
                    if len(ids) >= 2:
                        print(f"\n  [{vh.name}] 发起群聊，参与人数: {len(ids)+1}")
                        # 模拟群聊（轮流说话）
                        participants = [vh] + [self.agent_manager.get_virtual_human(pid) for pid in ids]
                        participants = [p for p in participants if p]
                        if len(participants) >= 3:
                            self._simulate_group_chat(participants)
                        else:
                            print("  选择的参与者无效")
            elif choice == "12":
                result = self.sim_day_pass()
                print(f"  >> {result}")
            elif choice == "13":
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
            elif choice == "14":
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
            elif choice == "15":
                self.show_guidance_log()
            elif choice == "16" or choice.lower() in ['quit', 'exit', 'q']:
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

    # ========== 新菜单辅助方法（确保存在） ==========
    def _show_all_characters(self):
        vhs = self.agent_manager.list_virtual_humans()
        if not vhs:
            print("  （暂无虚拟人）")
            return
        print("\n【所有虚拟人】")
        for v in vhs:
            active = " [当前]" if v["is_active"] else ""
            player = " [玩家]" if v.get('is_player') else ""
            mentor = " [导师]" if v.get('is_mentor') else ""
            print(f"  {v['id']}: {v['name']}{player}{mentor}{active}")
            if v.get('alive', True):
                print(f"    年龄: {v.get('age', '?'):.1f}, 职业: {v.get('job', '?')}")

    def _switch_character_menu(self):
        vhs = self.agent_manager.list_virtual_humans()
        if len(vhs) <= 1:
            print("  需要至少2个角色才能切换")
            return
        print("\n【切换角色】")
        for v in vhs:
            active = " [当前]" if v["is_active"] else ""
            print(f"  {v['id']}: {v['name']}{active}")
        switch = input("  输入ID: ").strip()
        if switch:
            self.select_virtual_human(switch)

    def _create_character_menu(self):
        name = input("  角色昵称: ").strip() or "AI村民"
        types = list(PERSONALITY_PRESETS.keys())
        print(f"  可选性格: {', '.join(types)}")
        ptype = input(f"  选择性格 [{types[0]}]: ").strip() or types[0]
        is_player = input("  这是玩家角色吗？(y/N): ").strip().lower() == 'y'
        self.create_virtual_human(name, ptype, is_player)
        print(f"  [OK] 创建成功")

    def _more_options_menu(self):
        while True:
            print("\n【模拟人生行动】")
            print("  1. 吃饭  2. 睡觉  3. 工作  4. 找工作")
            print("  5. 娱乐  6. 社交  7. 购物  8. 小红书")
            print("  9. 群聊 10. 返回")
            c = input("选择: ").strip()
            if c == "1":
                print(f"  {self.sim_eat()}")
            elif c == "2":
                print(f"  {self.sim_sleep()}")
            elif c == "3":
                print(f"  {self.sim_work()}")
            elif c == "4":
                print(f"  {self.sim_find_job()}")
            elif c == "5":
                print(f"  {self.sim_relax()}")
            elif c == "6":
                target = input("  和谁？(留空随机): ").strip()
                if target:
                    active_vh = self.agent_manager.get_active()
                    if active_vh:
                        print(f"  {active_vh.socialize()} {target}")
                else:
                    active_vh = self.agent_manager.get_active()
                    if active_vh:
                        print(f"  {active_vh.socialize()}")
            elif c == "7":
                print(f"  {self.sim_shop()}")
            elif c == "8":
                if vh.job != "小红书博主":
                    print("  注意：不是小红书博主")
                result = self.sim_create_xiaohongshu_post()
                print(f"  {result}")
            elif c == "9":
                vhs = self.agent_manager.list_virtual_humans()
                if len(vhs) >= 3:
                    ids = input("  输入ID(逗号分隔): ").strip().split(',')
                    ids = [i.strip() for i in ids if i.strip()]
                    if len(ids) >= 2:
                        participants = [vh] + [self.agent_manager.get_virtual_human(pid) for pid in ids]
                        participants = [p for p in participants if p]
                        if len(participants) >= 3:
                            self._simulate_group_chat(participants)
            elif c == "10" or c.lower() in ['b', 'back', 'q']:
                break
