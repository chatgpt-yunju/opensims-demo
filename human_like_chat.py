"""
Human-like Chat System - 仿真人类聊天的6个核心特征
"""

import random
import time
from typing import List, Dict, Optional, Tuple
from enum import Enum

# =========== 1. 状态与情绪管理 ===========

class EmotionalState:
    """情绪状态管理"""

    def __init__(self, mood_level: str = "普通", energy: int = 100, relationship: int = 50):
        self.mood_level = mood_level  # 开心/普通/低落/生气/崩溃
        self.energy = energy  # 0-100
        self.relationship = relationship  # 0-100

    def get_mood_intensity(self) -> float:
        """情绪强度（0.0-1.0）"""
        mapping = {
            "开心": 0.9,
            "普通": 0.6,
            "低落": 0.4,
            "生气": 0.3,
            "崩溃": 0.1
        }
        return mapping.get(self.mood_level, 0.5)

    def is_tired(self) -> bool:
        """是否疲劳"""
        return self.energy < 30

    def is_high_energy(self) -> bool:
        return self.energy > 70


class MoodInducedPhrases:
    """不同情绪下的口头禅和语气词"""

    @staticmethod
    def get_phrases(mood: str, friendliness: float) -> List[str]:
        phrases = {
            "开心": {
                "starter": ["哇！", "哈哈！", "太棒了！", "好开心～", "耶！"],
                "filler": ["～", "呢", "啦", "呀", "哦"],
                "ending": ["～", "！", "💕", "✨"]
            },
            "普通": {
                "starter": ["嗯，", "哦，", "然后呢？", "有意思。"],
                "filler": ["呢", "吧", "啊"],
                "ending": ["。", "…"]
            },
            "低落": {
                "starter": ["唉…", "也许吧…", "随便了…", "不知道…"],
                "filler": ["…", "呃"],
                "ending": ["…", "。"]
            },
            "生气": {
                "starter": ["哼！", "搞什么！", "真是的！"],
                "filler": ["！"],
                "ending": ["！", "！！"]
            },
            "崩溃": {
                "starter": ["……", "算了吧…", "我受够了…"],
                "filler": ["……"],
                "ending": ["……"]
            }
        }
        # 根据友好度调整语气亲和力
        base = phrases.get(mood, phrases["普通"])
        if friendliness > 0.7:
            # 更活泼，多用语气词
            base["starter"] = [s + random.choice(["～", "✨", "😊"]) if random.random() < 0.3 else s for s in base["starter"]]
        return base


# =========== 2. 记忆利用：记住之前聊过什么 ===========

class ConversationMemory:
    """对话记忆管理"""

    def __init__(self, memories: List[Dict] = None):
        self.memories = memories or []
        self.max_len = 50

    def add(self, role: str, content: str):
        """添加对话记忆"""
        self.memories.append({
            "role": role,
            "content": content,
            "timestamp": time.time()
        })
        if len(self.memories) > self.max_len:
            self.memories = self.memories[-self.max_len:]

    def get_recent(self, n: int = 5) -> List[Dict]:
        """获取最近N条对话"""
        return self.memories[-n:] if self.memories else []

    def get_user_mentions(self) -> List[str]:
        """提取用户提到的关键词（简化版）"""
        keywords = []
        for mem in self.memories:
            if mem["role"] == "user":
                # 简单分词（实际应用可以用NLP）
                words = mem["content"].split()
                keywords.extend([w for w in words if len(w) > 1])
        return keywords

    def has_topic_continuity(self, current_input: str) -> Optional[str]:
        """检查当前输入是否延续之前的话题"""
        recent = self.get_recent(3)
        if not recent:
            return None
        # 简单重叠检测
        current_words = set(current_input.lower().split())
        for mem in recent:
            if mem["role"] == "user":
                prev_words = set(mem["content"].lower().split())
                overlap = current_words & prev_words
                if overlap:
                    return f"你们刚才在聊：{mem['content'][:20]}..."
        return None


# =========== 3. 主动反问与话题延伸 ===========

class TopicExtender:
    """话题延伸引擎"""

    def __init__(self):
        self.press_on_patterns = [
            "你之前说的{keyword}，后来怎么样了？",
            "对了，你提到过{keyword}，能多聊聊吗？",
            "我对{keyword}挺感兴趣的，再多说点？"
        ]
        self.open_ended_questions = [
            "你为什么这么想？",
            "那是什么样的体验？",
            "可以举个例子吗？",
            "你当时感觉如何？",
            "这件事对你有什么影响？"
        ]

    def should_extend(self, memory: ConversationMemory, user_input: str, mood: str) -> Tuple[bool, Optional[str]]:
        """
        决定是否延伸话题
        返回：(是否延伸, 延伸的问题)
        """
        # 情绪低落时减少主动提问
        if mood in ["低落", "崩溃"] and random.random() < 0.7:
            return False, None

        # 如果用户输入很短，倾向于追问
        if len(user_input) < 10 and random.random() < 0.4:
            return True, random.choice(self.open_ended_questions)

        # 20%概率主动延伸（延续话题）
        if random.random() < 0.2:
            continuity = memory.has_topic_continuity(user_input)
            if continuity:
                # 提取用户之前提到的关键词简化版
                keywords = memory.get_user_mentions()
                if keywords:
                    keyword = random.choice(keywords[-3:])
                    question = random.choice(self.press_on_patterns).format(keyword=keyword)
                    return True, question

        return False, None


# =========== 4. 口语化、停顿、省略 ===========

class ColloquialEnhancer:
    """口语化增强器"""

    @staticmethod
    def add_pauses(text: str) -> str:
        """在合适位置添加停顿标记"""
        # 在逗号后、句号前添加停顿
        if random.random() < 0.3:
            text = text.replace("，", "，…")
            text = text.replace("。", "…。")
        return text

    @staticmethod
    def add_fillers(text: str, friendliness: float) -> str:
        """添加填充词（嗯、啊、那个…）"""
        fillers = ["嗯…", "那个…", "其实吧…", "怎么说呢…"]
        if friendliness > 0.6 and random.random() < 0.4:
            if text.startswith("我") or text.startswith("你"):
                prefix = random.choice(fillers)
                text = prefix + text
        return text

    @staticmethod
    def shorten_text(text: str, energy: int) -> str:
        """根据能量决定是否缩短回复"""
        # 能量低时更简短
        if energy < 50 and len(text) > 30 and random.random() < 0.5:
            # 截断后半部分
            half = len(text) // 2
            text = text[:half] + "…"
        return text


# =========== 5. 知行合一的行动暗示 ===========

class ActionConsistent:
    """言行一致：根据对话内容暗示可能的行动"""

    def __init__(self):
        self.action_hints = {
            "饿": ["我得去吃点东西了", "说到吃的我饿了", "先去吃饭"],
            "累": ["我要歇会儿", "有点困了", "想躺平"],
            "困": ["该睡觉了", "熬不住了", "晚安"],
            "玩": ["要不要放松一下？", "找点乐子", "去打游戏？"],
            "工作": ["得干活了", "要忙了", "回头聊"]
        }

    def maybe_add_action_hint(self, reply: str, user_input: str, vh_state: Dict) -> str:
        """
        根据对话内容或状态，添加行动暗示
        """
        # 检查用户输入中是否包含行动词汇
        for keyword, hints in self.action_hints.items():
            if keyword in user_input:
                if random.random() < 0.3:
                    reply += " " + random.choice(hints)
                break

        # 根据虚拟人自身状态添加
        if vh_state.get("energy", 100) < 30:
            if random.random() < 0.2:
                reply += " (我得休息一下了)"
        elif vh_state.get("hunger", 60) < 30:
            if random.random() < 0.2:
                reply += " (好饿啊…)"

        return reply


# =========== 6. 主控制器 ===========

class HumanLikeChatSystem:
    """
    仿真人类聊天的总控制器
    集成6个核心特征：
    1. 不直接回答，带情绪、语气、口头禅
    2. 根据当前状态（累、饿、开心、烦）改变说话风格
    3. 会记得之前聊过什么
    4. 会主动反问、延伸话题
    5. 会简短、停顿、省略、口语化
    6. 决策和聊天一致（言行一致暗示行动）
    """

    def __init__(self, personality: Dict, memories: List[Dict] = None):
        """
        初始化人类化聊天系统

        Args:
            personality: 性格属性（friendliness, humor, seriousness）
            memories: 已有的对话记忆（对虚拟人 memory 列表的引用）
        """
        self.personality = personality
        self.memory = ConversationMemory(memories)
        self.topic_extender = TopicExtender()
        self.action_consistency = ActionConsistent()

    def add_to_memory(self, role: str, content: str):
        """添加对话到记忆"""
        self.memory.add(role, content)

    def enhance_reply(self, base_reply: str, user_input: str, vh_state: Dict, vh_extra_state: Dict = None) -> str:
        """
        增强基础回复，添加人类特征

        Args:
            base_reply: API或Mock生成的基础回复
            user_input: 用户输入
            vh_state: 虚拟人当前状态（energy, mood, relationship）
            vh_extra_state: 虚拟人额外状态（如饥饿等）

        Returns:
            增强后的回复
        """
        enhanced = base_reply

        # 构建情绪状态对象
        emotional_state = EmotionalState(
            mood_level=vh_state.get("mood", "普通"),
            energy=vh_state.get("energy", 100),
            relationship=vh_state.get("relationship", 50)
        )

        # 1. 根据状态调整风格
        mood_phrases = MoodInducedPhrases.get_phrases(emotional_state.mood_level, self.personality.get("friendliness", 0.5))

        # 30%概率添加开头语气词
        if random.random() < 0.3:
            starter = random.choice(mood_phrases["starter"])
            enhanced = starter + enhanced

        # 2. 口语化处理
        enhanced = ColloquialEnhancer.add_fillers(enhanced, self.personality.get("friendliness", 0.5))
        enhanced = ColloquialEnhancer.add_pauses(enhanced)

        # 3. 根据能量调整长度
        enhanced = ColloquialEnhancer.shorten_text(enhanced, emotional_state.energy)

        # 4. 主动延伸话题（20%概率）
        should_extend, question = self.topic_extender.should_extend(self.memory, user_input, emotional_state.mood_level)
        if should_extend and question:
            enhanced += "\n" + question

        # 5. 言行一致：添加行动暗示
        combined_state = {
            "energy": emotional_state.energy,
            "mood": emotional_state.mood_level,
            "relationship": emotional_state.relationship,
            **(vh_extra_state or {})
        }
        enhanced = self.action_consistency.maybe_add_action_hint(enhanced, user_input, combined_state)

        # 6. 幽默感修饰（如果性格幽默）
        if self.personality.get("humor", 0) > 0.7 and random.random() < 0.2:
            funny_suffix = random.choice([" 😄", " lol", "（开玩笑的）", "～"])
            enhanced += funny_suffix

        # 7. 关系度高时更亲密
        if emotional_state.relationship > 70 and random.random() < 0.3:
            pet_names = ["亲爱的", "宝宝", "宝贝", "友友"]
            enhanced = random.choice(pet_names) + "，" + enhanced[0].lower() + enhanced[1:]

        return enhanced.strip()

    def to_dict(self) -> Dict:
        """序列化状态（用于调试）"""
        # 由于不存储状态，只返回 personality 和 memory 数量
        return {
            "personality": self.personality,
            "memory_count": len(self.memory.memories)
        }
