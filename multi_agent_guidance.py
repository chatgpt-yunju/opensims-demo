"""
Multi-Agent 协作引导系统
模拟ClaudeCode的多角色协作：规划师、反驳师、反馈师等
"""

from typing import List, Dict, Optional
import random
from enum import Enum

class AgentRole(Enum):
    """内部子Agent角色类型"""
    PLANNER = "planner"          # 规划师 - 制定探索路径
    CRITIC = "critic"            # 反驳师 - 挑战假设，避免盲目
    FEEDBACK = "feedback"        # 反馈师 - 提供建设性意见
    ENCOURAGER = "encourager"    # 鼓励师 - 情感支持
    SYNTHESIZER = "synthesizer"  # 整合师 - 综合多角度建议

class SubAgent:
    """子Agent - 每个有独特的思维框架和输出风格"""

    def __init__(self, role: AgentRole, parent_vh):
        self.role = role
        self.parent = parent_vh  # 所属虚拟人
        self.perspective = self._get_perspective()
        self.style = self._get_style()

    def _get_perspective(self) -> str:
        """该角色的思考视角"""
        perspectives = {
            AgentRole.PLANNER: "从长远目标和阶段性计划的角度思考",
            AgentRole.CRITIC: "从潜在风险、逻辑漏洞和反事实角度思考",
            AgentRole.FEEDBACK: "从具体行动步骤和改进空间角度思考",
            AgentRole.ENCOURAGER: "从情感支持和动机强化角度思考",
            AgentRole.SYNTHESIZER: "从多维度整合和系统平衡角度思考"
        }
        return perspectives[self.role]

    def _get_style(self) -> str:
        """对话风格"""
        styles = {
            AgentRole.PLANNER: "结构化、有条理、分步骤",
            AgentRole.CRITIC: "直接、犀利、提出反面证据",
            AgentRole.FEEDBACK: "具体、可操作、温和",
            AgentRole.ENCOURAGER: "温暖、肯定、充满希望",
            AgentRole.SYNTHESIZER: "全面、平衡、系统性"
        }
        return styles[self.role]

    def generate_response(self, context: Dict, player_input: str) -> str:
        """生成该角色的回复"""
        # 基于角色类型生成特定的回复
        if self.role == AgentRole.PLANNER:
            return self._planner_response(context, player_input)
        elif self.role == AgentRole.CRITIC:
            return self._critic_response(context, player_input)
        elif self.role == AgentRole.FEEDBACK:
            return self._feedback_response(context, player_input)
        elif self.role == AgentRole.ENCOURAGER:
            return self._encourager_response(context, player_input)
        elif self.role == AgentRole.SYNTHESIZER:
            return self._synthesizer_response(context, player_input)

    def _planner_response(self, context: Dict, player_input: str) -> str:
        """规划师：制定探索路径"""
        templates = [
            f"我注意到你提到了'{player_input[:20]}'。我们可以把它分解成几个小步骤：\n1. 第一周：了解基础\n2. 第二周：动手实践\n3. 第三周：反思总结\n\n你觉得这个节奏如何？",
            f"关于'{player_input[:20]}'，我建议你先明确目标，然后制定3个月的探索计划。要包括：\n- 要学习的技能\n- 要尝试的活动\n- 如何评估进展\n\n需要我帮你细化吗？",
            f"这是一个很好的方向！让我帮你规划���下成长路径：\n短期（1个月）：\n中期（3个月）：\n长期（6个月）：\n\n我们先确定短期目标吧。"
        ]
        return random.choice(templates)

    def _critic_response(self, context: Dict, player_input: str) -> str:
        """反驳师：挑战假设，避免盲目"""
        templates = [
            f"等等，你确定'{player_input[:20]}'真的是你想要的吗？很多人在这方面投入大量时间后才发现并不适合。\n\n你能列出至少3个理由说明为什么这个方向适合你吗？",
            f"我理解你的热情，但我们需要更谨慎。'{player_input[:20]}'这条路可能面临哪些挑战？你准备好了吗？\n\n让我们想想 worst case scenario。",
            f"是不是受到外界影响太大了？有时候我们会被表面的东西吸引，而忽略了自己真正的优势。\n\n回顾一下你过去做得最好的事情，和这个方向有什么关联？",
            f"这个想法听起来不错，但我们要避免 confirmation bias。有没有相反的证据表明这可能不适合你？"
        ]
        return random.choice(templates)

    def _feedback_response(self, context: Dict, player_input: str) -> str:
        """反馈师：提供建设性改进建议"""
        templates = [
            f"你的想法很有潜力！如果从这几个方面完善会更好：\n1. 具体化：把'{player_input[:20]}'变成可测量的目标\n2. 分阶段：不要一次性做太多\n3. 寻求反馈：定期找相关人士交流\n\n你觉得哪一点最难？",
            f"基于你之前的探索，我注意到你在相关技能上有基础。建议：\n- 每周投入固定时间（建议5-10小时）\n- 找到实践机会而不仅仅是学习\n- 记录每次实践的心得\n\n要我具体说说某个方面吗？",
            f"很多人会犯的错误是把兴趣当成职业。我的建议是：先用最小成本试错（比如2周时间），验证是否真的适合。\n\n你打算怎么验证？"
        ]
        return random.choice(templates)

    def _encourager_response(self, context: Dict, player_input: str) -> str:
        """鼓励师：情感支持和动机强化"""
        templates = [
            f"哇！你提到'{player_input[:20]}'的时候，我能感受到你的热情！这种热情非常珍贵，很多人缺少的就是这个。\n\n无论遇到什么困难，记住你最初为什么选择这条路。",
            f"我相信你！探索新领域需要勇气，而你已经在行动了。每一次尝试都是成长，即使结果不如预期。\n\n我会一直在这里支持你！",
            f"你的进步让我感动！从你之前的经历看，你具备成功所需的素质：好奇心、坚持、反思能力。\n\n继续前进，你一定可以的！",
            f"不要怕失败。所有成功人士都经历过无数次失败。重要的是从失败中学习。\n\n我为你感到骄傲！"
        ]
        return random.choice(templates)

    def _synthesizer_response(self, context: Dict, player_input: str) -> str:
        """整合师：综合多角度，形成系统建议"""
        templates = [
            f"让我们从几个角度综合看'{player_input[:20]}'：\n\n✅ 优势：你对此有热情，且已有相关基础\n⚠️ 风险：可能遇到瓶颈期，需要坚持\n💡 机会：这个领域有发展空间\n🎯 行动：建议MVP（最小可行尝试）\n\n平衡来看，这是一个值得探索的方向，但需要理性规划。",
            f"整合各方面的因素：你的性格（{self.parent.personality}）、当前技能、市场需求、个人价值观。\n\n我觉得关键在于：\n1. 是否与你的核心价值观一致\n2. 是否有可行的入门路径\n3. 能否承受可能的代价\n\n我们可以逐一讨论。",
            f"这不是非黑即白的决定。你可以：\n- 短期投入一定时间探索\n- 同时保持其他选项\n- 定期复盘并调整方向\n\n灵活应变是 smart choice。"
        ]
        return random.choice(templates)


class MultiAgentGuidanceSystem:
    """多Agent协作引导系统 - 每个虚拟人内置"""

    def __init__(self, parent_vh):
        self.parent = parent_vh
        self.agents = self._initialize_agents()
        self.discussion_history: List[Dict] = []  # Agent间讨论历史
        self.coordination_mode = "sequential"  # 协调模式：sequential/concurrent

    def _initialize_agents(self) -> Dict[AgentRole, SubAgent]:
        """初始化所有子Agent"""
        agents = {}
        for role in AgentRole:
            agents[role] = SubAgent(role, self.parent)
        return agents

    def collaborative_guidance(self, player_input: str, player_growth) -> Dict:
        """
        多Agent协作生成引导回复

        流程：
        1. Planner 制定探索框架
        2. Critic 挑战假设
        3. Feedback 提供具体建议
        4. Encourager 情感支持
        5. Synthesizer 综合成最终回复

        返回：所有Agent的观点 + 最终整合回复
        """
        context = {
            "player_input": player_input,
            "player_growth": player_growth.get_growth_summary() if player_growth else None,
            "parent_vh": {
                "name": self.parent.name,
                "mentor_type": self.parent.mentor_type,
                "personality": self.parent.personality
            }
        }

        contributions = {}
        discussion = []

        # === Agent 协作流水线 ===

        # 1. Planner 制定探索框架
        planner_outlook = self.agents[AgentRole.PLANNER].generate_response(context, player_input)
        contributions["planner"] = planner_outlook
        discussion.append(f"[规划师] {planner_outlook}")

        # 2. Critic 挑战
        critic_challenge = self.agents[AgentRole.CRITIC].generate_response(context, player_input)
        contributions["critic"] = critic_challenge
        discussion.append(f"[反驳师] {critic_challenge}")

        # 3. Feedback 提供具体建议
        feedback_suggestions = self.agents[AgentRole.FEEDBACK].generate_response(context, player_input)
        contributions["feedback"] = feedback_suggestions
        discussion.append(f"[反馈师] {feedback_suggestions}")

        # 4. Encourager 情感支持
        encouragement = self.agents[AgentRole.ENCOURAGER].generate_response(context, player_input)
        contributions["encourager"] = encouragement
        discussion.append(f"[鼓励师] {encouragement}")

        # 5. Synthesizer 整合
        synthesis = self.agents[AgentRole.SYNTHESIZER].generate_response(context, player_input)
        contributions["synthesizer"] = synthesis
        discussion.append(f"[整合师] {synthesis}")

        # 记录讨论
        self.discussion_history.append({
            "timestamp": datetime.datetime.now().isoformat(),
            "player_input": player_input,
            "contributions": contributions
        })

        # 返回最终回复
        final_reply = self._format_final_response(contributions)

        return {
            "final_reply": final_reply,
            "agent_contributions": contributions,
            "discussion_log": discussion,
            "coordinator": self.parent.name
        }

    def _format_final_response(self, contributions: Dict[str, str]) -> str:
        """格式化最终��复"""
        # 不同导师类型偏好不同的回复格式
        if self.parent.mentor_type == "创意激发者":
            # 创意型：有趣、活泼、带emoji
            parts = [
                random.choice(["✨", "🎯", "🚀"]) + " " + contributions["planner"].split('\n')[0],
                contributions["feedback"],
                contributions["encourager"]
            ]
            return "\n\n".join(parts)

        elif self.parent.mentor_type == "目标规划师":
            # 规划型：结构化、清晰
            parts = [
                "📋 探索计划：",
                contributions["planner"],
                "\n⚠️ 需要注意：",
                contributions["critic"],
                "\n✅ 行动建议：",
                contributions["feedback"]
            ]
            return "".join(parts)

        elif self.parent.mentor_type == "情感支持者":
            # 情感型：温暖、共鸣
            parts = [
                contributions["encourager"],
                contributions["synthesizer"],
                contributions["feedback"]
            ]
            return "\n".join(parts)

        else:  # 平衡引导者
            # 平衡型：整合所有观点
            return contributions["synthesizer"]

    def get_agent_insights(self) -> Dict:
        """获取Agent系统的洞察（用于调试/展示）"""
        if not self.discussion_history:
            return {"message": "暂无讨论记录"}

        latest = self.discussion_history[-1]
        return {
            "last_discussion": latest,
            "agent_count": len(self.agents),
            "coordination_mode": self.coordination_mode
        }
