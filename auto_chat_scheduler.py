import threading
import time
import random
from config import AUTO_CHAT_ENABLED, AUTO_CHAT_INTERVAL, AUTO_CHAT_PROBABILITY, AUTO_CHAT_EXCLUDE_PLAYER

class AutoChatScheduler:
    """自动聊天调度器（灵魂永生模式）"""

    def __init__(self, agent_manager, api_client):
        self.agent_manager = agent_manager
        self.api_client = api_client
        self.running = False
        self.thread = None

    def start(self):
        """启动后台调度线程"""
        if not AUTO_CHAT_ENABLED:
            print("[AutoChat] 自动聊天已禁用（配置中关闭）")
            return

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
        """检查是否需要触发自动对话"""
        mgr = self.agent_manager
        vhs = mgr.list_virtual_humans()

        # 至少需要2个虚拟人
        if len(vhs) < 2:
            return

        # 仅考虑存活的虚拟人
        alive_vhs = [v for v in vhs if v.get('alive', True)]

        # 如果配置排除玩家角色，过滤掉玩家控制的角色
        if AUTO_CHAT_EXCLUDE_PLAYER:
            alive_vhs = [v for v in alive_vhs if not v.get('is_player', False)]

        # 需要至少2个非玩家角色才能自动聊天
        if len(alive_vhs) < 2:
            return

        # 根据概率决定是否触发
        if random.random() > AUTO_CHAT_PROBABILITY:
            return

        # 随机选择两个不同的虚拟人
        v1, v2 = random.sample(alive_vhs, 2)
        v1_obj = mgr.get_virtual_human(v1["id"])
        v2_obj = mgr.get_virtual_human(v2["id"])

        if not v1_obj or not v2_obj:
            return

        # 生成对话
        print(f"\n[AutoChat] {v1_obj.name} 和 {v2_obj.name} 开始聊天...")

        # 简单对话脚本
        greetings = [
            f"你好啊，{v2_obj.name}！",
            f"最近怎么样，{v2_obj.name}？",
            f"嘿，{v2_obj.name}，聊会天呗？"
        ]
        responses = [
            f"还不错，{v1_obj.name}！你呢？",
            "还行吧，最近有点忙。",
            "正无聊呢，你找我聊天太及时了！"
        ]

        greeting = random.choice(greetings)
        response = random.choice(responses)

        # 执行对话（通过API或Mock）
        print(f"  {v1_obj.name}: {greeting}")
        v1_obj.add_memory("user", greeting)  # 简化：把对方的话当作用户输入
        reply1 = self.api_client.generate_reply(v2_obj, greeting)
        v2_obj.add_memory("assistant", reply1['reply'])
        print(f"  {v2_obj.name}: {reply1['reply'][:60]}")

        # 可能还有后续
        if random.random() < 0.5:
            time.sleep(0.5)  # 模拟延迟
            second_line = f"确实呢，{v1_obj.name}"
            print(f"  {v1_obj.name}: {second_line}")
            v1_obj.add_memory("assistant", second_line)