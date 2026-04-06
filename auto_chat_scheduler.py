import threading
import time
import random
from config import AUTO_CHAT_ENABLED, AUTO_CHAT_INTERVAL, AUTO_CHAT_PROBABILITY, AUTO_CHAT_EXCLUDE_PLAYER

class AutoChatScheduler:
    """自动聊天调度器（灵魂永生模式）"""

    def __init__(self, agent_manager, api_client, message_callback=None):
        """初始化调度器

        Args:
            agent_manager: 代理管理器
            api_client: API客户端
            message_callback: 消息回调函数，接收 (speaker_name, message, is_group) 参数
        """
        self.agent_manager = agent_manager
        self.api_client = api_client
        self.message_callback = message_callback
        self.player_growth = None  # 延迟设置
        self.running = False
        self.thread = None

    def set_player_growth(self, player_growth: 'PlayerGrowth'):
        """设置玩家成长系统引用（Social networking effect）"""
        self.player_growth = player_growth

    def start(self):
        """启动后台调度线程"""
        # 不再检查 AUTO_CHAT_ENABLED，由调用方决定是否启动
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        print(f"[AutoChat] 自动聊天调度器已启动（间隔{AUTO_CHAT_INTERVAL}秒，概率{AUTO_CHAT_PROBABILITY*100:.0f}%）")

    def stop(self):
        """停止调度器"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        print("[AutoChat] 调度器已停止")

    def _run_loop(self):
        """后台循环"""
        while self.running:
            try:
                time.sleep(AUTO_CHAT_INTERVAL)
                self._check_and_chat()
            except Exception as e:
                print(f"[AutoChat] 错误: {e}")

    def _check_and_chat(self):
        """检查是否需要触发自动对话（支持双人和群聊）"""
        mgr = self.agent_manager
        vhs = mgr.list_virtual_humans()

        if len(vhs) < 2:
            return

        alive_vhs = [v for v in vhs if v.get('alive', True)]

        if AUTO_CHAT_EXCLUDE_PLAYER:
            alive_vhs = [v for v in alive_vhs if not v.get('is_player', False)]

        if len(alive_vhs) < 2:
            return

        if random.random() > AUTO_CHAT_PROBABILITY:
            return

        # 30%概率触发群聊（3-5人）
        if random.random() < 0.3 and len(alive_vhs) >= 3:
            group_size = random.randint(3, min(5, len(alive_vhs)))
            participant_dicts = random.sample(alive_vhs, group_size)
            participants = [mgr.get_virtual_human(p["id"]) for p in participant_dicts]
            self._trigger_group_chat(participants)
        else:
            # 双人对话
            v1, v2 = random.sample(alive_vhs, 2)
            v1_obj = mgr.get_virtual_human(v1["id"])
            v2_obj = mgr.get_virtual_human(v2["id"])
            if v1_obj and v2_obj:
                self._trigger_conversation(v1_obj, v2_obj)

    def _trigger_conversation(self, vh1, vh2, turns=3):
        """触发两个虚拟人之间的对话"""
        # 防御：确保vh1和vh2是SimPerson对象（而非dict）
        if not (hasattr(vh1, 'name') and hasattr(vh2, 'name')):
            print(f"[AutoChat] 错误: 传入的参数不是虚拟人对象 (vh1 type={type(vh1)}, vh2 type={type(vh2)})")
            return

        print(f"\n[AutoChat] {vh1.name} ↔ {vh2.name} 开始聊天...")

        # 轮流对话
        current_speaker = vh1
        other = vh2

        # === 社交网络效应：可能引入玩家话题 ===
        player_context = self._build_player_context(vh1, vh2)

        for turn in range(turns):
            if turn == 0:
                # 第一句由当前选中的speaker说
                base_prompt = f"你是{current_speaker.name}，性格{current_speaker.personality}。你要对{other.name}说一句打招呼的话。"
            else:
                base_prompt = f"你是{current_speaker.name}，继续和{other.name}聊天。根据对话历史回应。"

            # 有概率引入玩家话题（social networking effect）
            if player_context and random.random() < 0.4:
                prompt = f"{base_prompt}\n\n{player_context}\n\n可以适当聊聊玩家的近况。"
            else:
                prompt = base_prompt

            # 获取记忆上下文（最近20条，10轮对话）
            memories = current_speaker.memory[-20:]  # 扩展上下文窗口
            context = "\n".join([f"{m['role']}: {m['content']}" for m in memories])

            try:
                # 调用API生成回复
                reply = self.api_client.generate_reply(current_speaker, prompt + "\n" + context)
                message = reply.get('reply', "（沉默）")[:200]  # 允许更长回复
            except Exception as e:
                message = f"（错误：{e}）"

            print(f"  {current_speaker.name}: {message}")

            # 通过回调通知GUI（如果存在）
            if self.message_callback:
                try:
                    self.message_callback(current_speaker.name, message, is_group=False)
                except:
                    pass  # 回调失败不影响对话

            # 记录记忆
            current_speaker.add_memory("assistant", message)
            other.add_memory("user", message)

            # 交换说话者
            current_speaker, other = other, current_speaker

            if turn < turns - 1:
                time.sleep(random.uniform(0.5, 1.5))

        print(f"[AutoChat] 对话结束")

    def _trigger_group_chat(self, participants):
        """触发群聊（3+人）"""
        print(f"\n[AutoChat] 群聊开始: {'、'.join(p.name for p in participants)}")

        # 群聊轮次
        num_turns = random.randint(4, 8)

        for turn in range(num_turns):
            # 随机选择说话者
            speaker = random.choice(participants)
            others = [p for p in participants if p.id != speaker.id]

            # 构建群聊上下文（扩展：每个人最近10条）
            recent_messages = []
            for p in participants:
                mems = p.memory[-10:]  # 扩展上下文
                for m in mems:
                    recent_messages.append((p.name, m['content']))

            # 取最近20条
            context = "\n".join([f"{name}: {msg}" for name, msg in recent_messages[-20:]])

            prompt = f"你在一个群聊中，参与对话的人有：{', '.join([p.name for p in participants])}\n\n最近对话：\n{context}\n\n请你说一句简短的、符合性格的话参与讨论："

            try:
                reply = self.api_client.generate_reply(speaker, prompt)
                message = reply.get('reply', "（沉默）")[:150]
            except Exception as e:
                message = f"（错误：{e}）"

            print(f"  {speaker.name}: {message}")

            # 通过回调通知GUI（如果存在）
            if self.message_callback:
                try:
                    self.message_callback(speaker.name, message, is_group=True)
                except:
                    pass

            # 所有人都记录这条消息
            for p in participants:
                p.add_memory("user" if p.id != speaker.id else "assistant", message)

            time.sleep(random.uniform(0.5, 2))

        print(f"[AutoChat] 群聊结束")
    def _build_player_context(self, vh1, vh2) -> str:
        """构建玩家相关话题上下文（社交网络效应）"""
        if not self.player_growth:
            return ""

        # 检查两个虚拟人是否有关注玩家
        player_related = []
        for vh in [vh1, vh2]:
            # 如果是导师，或者与玩家关系度高
            if getattr(vh, 'is_mentor', False) or (hasattr(vh, 'get_relationship_with_player') and vh.get_relationship_with_player() > 60):
                player_related.append(vh)

        if not player_related:
            return ""

        # 构建玩家近况摘要
        summary = self.player_growth.get_growth_summary()
        context_lines = ["[玩家近况分享]"]
        context_lines.append(f"  当前使命状态: {summary['current_status']}")
        if summary['life_mission']:
            context_lines.append(f"  已确认使命: {summary['life_mission']}")
        if summary['discovered_interests']:
            context_lines.append(f"  兴趣领域: {', '.join(summary['discovered_interests'])}")
        context_lines.append(f"  完成挑战: {summary['challenges_completed']}个")
        context_lines.append(f"  引导次数: {summary['total_guidance_sessions']}次")

        # 添加关心度修饰
        mentor_vh = player_related[0]
        relationship = mentor_vh.get_relationship_with_player()
        if relationship >= 80:
            context_lines.append(f"\n{mentor_vh.name} 非常关心玩家的成长，经常主动提供帮助。")
        elif relationship >= 60:
            context_lines.append(f"\n{mentor_vh.name} 对玩家的进展保持关注。")

        return "\n".join(context_lines)
