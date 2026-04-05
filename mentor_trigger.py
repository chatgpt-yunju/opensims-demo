"""
导师主动触发引擎
决定何时、哪个导师主动发起对玩家的引导
"""

import time
import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from virtual_human import SimPerson
from player_growth import PlayerGrowth

class TriggerCondition:
    """触发条件配置"""

    def __init__(self):
        self.max_active_mentors_per_day = 2  # 每天最多主动引导次数
        self.cooldown_hours = 24  # 同一导师触发冷却（小时）
        self.min_relationship = 30  # 最低关系度门槛
        self.emotional_support_threshold = 50  # 情绪支持触发阈值
        self.stagnation_check_dialogues = 3  # 检查停滞需要的对话次数

class MentorTriggerEngine:
    """导师主动触发引擎"""

    # 触发类型常量
    TRIGGER_EMOTIONAL_SUPPORT = "emotional_support"  # 情绪支持（玩家情绪低落）
    TRIGGER_PROGRESS_CHECK = "progress_check"        # 进度检查（玩家线索多但未行动）
    TRIGGER_MISSION_SYNTHESIS = "mission_synthesis"  # 使命综合（线索需要整合）
    TRIGGER_CHALLENGE_DEBRIEF = "challenge_debrief"  # 挑战后反思
    TRIGGER_PROACTIVE_CHECKIN = "proactive_checkin"  # 主动关怀（周期性）
    TRIGGER_SKILL_STAGNATION = "skill_stagnation"    # 技能停滞

    def __init__(self, agent_manager, player_growth: PlayerGrowth):
        self.agent_manager = agent_manager
        self.player_growth = player_growth
        self.conditions = TriggerCondition()
        self.last_trigger_time: Dict[str, datetime] = {}  # mentor_id -> 最后触发时间
        self.daily_trigger_count = 0
        self.last_reset_day = datetime.now().date()

        # 触发历史（用于分析和调试）
        self.trigger_history: List[Dict] = []

    def check_triggers(self, player_state: Dict = None) -> Optional[Dict]:
        """
        检查是否需要触发导师主动引导
        在每次玩家行动后调用

        返回：触发建议或None
        """
        # 重置每日计数
        today = datetime.now().date()
        if today != self.last_reset_day:
            self.daily_trigger_count = 0
            self.last_reset_day = today

        # 检查每日限制
        if self.daily_trigger_count >= self.conditions.max_active_mentors_per_day:
            return None

        # 获取所有虚拟人
        all_vhs = self.agent_manager.list_virtual_humans()
        mentors = [v for v in all_vhs if self._is_mentor(v)]

        if not mentors:
            return None

        # 分析玩家状态，判断触发类型
        trigger_type, reason = self._analyze_player_status(player_state)

        if not trigger_type:
            return None

        # 选择最合适的导师
        selected_mentor = self._select_mentor(mentors, trigger_type)

        if not selected_mentor:
            return None

        # 检查冷却
        if self._is_on_cooldown(selected_mentor["id"]):
            return None

        # 记录触发
        self._record_trigger(selected_mentor["id"], trigger_type, reason)

        # 构建触发建议
        return {
            "mentor_id": selected_mentor["id"],
            "mentor_name": selected_mentor["name"],
            "trigger_type": trigger_type,
            "reason": reason,
            "suggested_initiative": self._get_initiative_message(trigger_type, selected_mentor),
            "timestamp": datetime.now().isoformat()
        }

    def _is_mentor(self, vh_data: Dict) -> bool:
        """判断虚拟人是否为导师类型（教师或贵人）"""
        job = vh_data.get("job", "")
        return job in ["教师", "贵人"]

    def _analyze_player_status(self, player_state: Dict) -> tuple[Optional[str], Optional[str]]:
        """分析玩家状态，决定触发类型"""
        if not self.player_growth:
            return None, None

        summary = self.player_growth.get_growth_summary()

        # 条件1：使命线索需要整合
        if summary["mission_clues_count"] >= 3 and not summary["life_mission"]:
            # 检查最近是否已经有相关讨论
            last_guidance = self.player_growth.guidance_history[-1] if self.player_growth.guidance_history else None
            if not last_guidance or "mission" not in last_guidance.get("type", ""):
                return self.TRIGGER_MISSION_SYNTHESIS, f"已收集{summary['mission_clues_count']}条使命线索，需要整合"

        # 条件2：完成挑战后需要反思
        if summary["challenges_completed"] > 0:
            last_event = self.player_growth.life_events[-1] if self.player_growth.life_events else None
            if last_event and last_event.get("type") == "challenge_completed":
                return self.TRIGGER_CHALLENGE_DEBRIEF, "刚完成挑战，需要复盘"

        # 条件3：发现兴趣但未实践（需要行动引导）
        if summary["challenges_completed"] == 0 and len(summary["discovered_interests"]) > 0:
            return self.TRIGGER_SKILL_STAGNATION, "发现兴趣但未实践，需要小步尝试"

        # 条件4：周期性主动关怀（低概率）
        if random.random() < 0.15:  # 15%概率触发
            return self.TRIGGER_PROACTIVE_CHECKIN, "主动关心进展"

        return None, None

    def _select_mentor(self, mentors: List[Dict], trigger_type: str) -> Optional[Dict]:
        """
        选择最合适的导师
        策略：关系度 + 最近交互时间 + 导师专长匹配 + 随机性
        """
        # 过滤：关系度达标
        qualified = [m for m in mentors if m.get("relationship_with_player", 50) >= self.conditions.min_relationship]
        if not qualified:
            return None

        # 评分维度
        scores = {}
        for mentor in qualified:
            score = 0

            # 1. 关系度分数（最高40分）
            score += mentor.get("relationship_with_player", 50) * 0.4

            # 2. 最近交互惩罚（越久未交互，分数越高，避免冷落）
            last_interaction = self._get_last_interaction_time(mentor["id"])
            hours_ago = (datetime.now() - last_interaction).total_seconds() / 3600 if last_interaction else 999
            recency_bonus = min(20, hours_ago * 0.5)  # 每10小时+5分，上限20
            score += recency_bonus

            # 3. 导师专长匹配（触发类型 vs 导师类型）
            mentor_type = self._get_mentor_type_from_job(mentor.get("job", ""))
            type_match = self._match_trigger_to_mentor_type(trigger_type, mentor_type)
            score += type_match * 10  # 最高+30

            # 4. 随机性（避免每次都选同一个人）
            score += random.uniform(0, 15)

            scores[mentor["id"]] = {
                "mentor": mentor,
                "score": score
            }

        # 选最高分
        if not scores:
            return None

        sorted_scores = sorted(scores.items(), key=lambda x: x[1]["score"], reverse=True)
        return sorted_scores[0][1]["mentor"]

    def _get_last_interaction_time(self, mentor_id: str) -> Optional[datetime]:
        """获取最后交互时间"""
        if not self.player_growth:
            return None

        for entry in reversed(self.player_growth.guidance_history):
            if entry.get("mentor") == mentor_id:
                try:
                    return datetime.fromisoformat(entry["timestamp"])
                except:
                    continue
        return None

    def _get_mentor_type_from_job(self, job: str) -> str:
        """从职业映射到导师类型"""
        if job == "教师":
            return "目标规划师"  # 教师通常是规划型
        elif job == "贵人":
            return "情感支持者"  # 贵人通常是支持型
        return "平衡引导者"

    def _match_trigger_to_mentor_type(self, trigger_type: str, mentor_type: str) -> float:
        """触发类型与导师类型的匹配度（0-1）"""
        match_matrix = {
            self.TRIGGER_EMOTIONAL_SUPPORT: {
                "情感支持者": 1.0,
                "平衡引导者": 0.5,
                "目标规划师": 0.2,
                "创意激发者": 0.3
            },
            self.TRIGGER_PROGRESS_CHECK: {
                "目标规划师": 1.0,
                "平衡引导者": 0.7,
                "创意激发者": 0.4,
                "情感支持者": 0.3
            },
            self.TRIGGER_MISSION_SYNTHESIS: {
                "平衡引导者": 1.0,
                "目标规划师": 0.8,
                "创意激发者": 0.6,
                "情感支持者": 0.5
            },
            self.TRIGGER_CHALLENGE_DEBRIEF: {
                "目标规划师": 1.0,
                "反馈师": 0.9,
                "平衡引导者": 0.7
            },
            self.TRIGGER_PROACTIVE_CHECKIN: {
                "情感支持者": 1.0,
                "创意激发者": 0.8,
                "平衡引导者": 0.6
            }
        }

        return match_matrix.get(trigger_type, {}).get(mentor_type, 0.5)

    def _is_on_cooldown(self, mentor_id: str) -> bool:
        """检查导师是否在冷却中"""
        if mentor_id not in self.last_trigger_time:
            return False

        last_time = self.last_trigger_time[mentor_id]
        hours_elapsed = (datetime.now() - last_time).total_seconds() / 3600
        return hours_elapsed < self.conditions.cooldown_hours

    def _record_trigger(self, mentor_id: str, trigger_type: str, reason: str):
        """记录触发事件"""
        self.last_trigger_time[mentor_id] = datetime.now()
        self.daily_trigger_count += 1

        self.trigger_history.append({
            "mentor_id": mentor_id,
            "trigger_type": trigger_type,
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        })

        # 保持历史记录不过大
        if len(self.trigger_history) > 100:
            self.trigger_history = self.trigger_history[-100:]

    def _get_initiative_message(self, trigger_type: str, mentor: Dict) -> str:
        """生成主动发起的开场白（导师视角）"""
        mentor_name = mentor.get("name", "导师")
        mentor_type = mentor.get("mentor_type", "平衡引导者")

        templates = {
            self.TRIGGER_EMOTIONAL_SUPPORT: [
                f"[{mentor_name}] 嘿，玩家，我注意到你最近似乎在探索一些事情。有什么想和我聊聊的吗？",
                f"[{mentor_name}] 你好！我感觉你最近可能有些想法在酝酿。我在这里，随时愿意倾听。"
            ],
            self.TRIGGER_PROGRESS_CHECK: [
                f"[{mentor_name}] 玩家，很久没聊了。你最近在忙什么？有没有新的发现？",
                f"[{mentor_name}] 我想了解一下你的近况。有什么想分享的吗？"
            ],
            self.TRIGGER_MISSION_SYNTHESIS: [
                f"[{mentor_name}] 玩家，我注意到你收集了不少线索。找个时间我们一起梳理一下吧？",
                f"[{mentor_name}] 是时候整合你的探索成果了。愿意和我聊聊你的发现吗？"
            ],
            self.TRIGGER_CHALLENGE_DEBRIEF: [
                f"[{mentor_name}] 恭喜完成挑战！现在感觉如何？有什么体会想分享？",
                f"[{mentor_name}] 看到你取得的成绩，真为你高兴！我们一起来复盘一下吧。"
            ],
            self.TRIGGER_PROACTIVE_CHECKIN: [
                f"[{mentor_name}] 嗨！最近怎么样？随时可以找我聊天。",
                f"[{mentor_name}] 好久没交流了。今天想聊点什么？"
            ],
            self.TRIGGER_SKILL_STAGNATION: [
                f"[{mentor_name}] 玩家，我发现你对{mentor.get('discovered_interests', ['一些领域'])[0]}有兴趣，但还没深入实践。需要我帮你规划一下吗？",
                f"[{mentor_name}] 有兴趣是好事，但行动更重要。让我们一起把兴趣转化为技能吧！"
            ]
        }

        msgs = templates.get(trigger_type, [f"[{mentor_name}] 你好，最近怎么样？"])
        return random.choice(msgs)

    def force_trigger(self, mentor_id: str, trigger_type: str = None) -> Dict:
        """
        强制触发（用于测试或特殊情况）
        绕过冷却和每日限制
        """
        mentor = self.agent_manager.get_virtual_human(mentor_id)
        if not mentor:
            return {"error": "导师不存在"}

        trigger_type = trigger_type or self.TRIGGER_PROACTIVE_CHECKIN
        message = self._get_initiative_message(trigger_type, {
            "name": mentor.name,
            "mentor_type": mentor.mentor_type,
            "discovered_interests": mentor.discovered_player_interests
        })

        return {
            "mentor_id": mentor_id,
            "mentor_name": mentor.name,
            "trigger_type": trigger_type,
            "reason": "手动触发",
            "suggested_initiative": message,
            "timestamp": datetime.now().isoformat()
        }

    def get_trigger_stats(self) -> Dict:
        """获取触发统计（用于监控）"""
        return {
            "total_triggers": len(self.trigger_history),
            "daily_count": self.daily_trigger_count,
            "last_trigger": self.trigger_history[-1] if self.trigger_history else None,
            "cooldown_mentors": [
                m_id for m_id, t in self.last_trigger_time.items()
                if (datetime.now() - t).total_seconds() / 3600 < self.conditions.cooldown_hours
            ]
        }
