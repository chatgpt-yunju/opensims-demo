"""
玩家成长与人生使命发现系统
追踪玩家的成长轨迹，帮助虚拟人引导玩家找到人生使命
"""

from typing import List, Dict, Optional
from datetime import datetime
import json

class PlayerGrowth:
    """追踪玩家成长和使命发现进程"""

    def __init__(self, player_id: str):
        self.player_id = player_id
        self.discovered_interests: List[str] = []  # 已发现的兴趣领域
        self.skill_levels: Dict[str, float] = {}  # 技能熟练度 0-100
        self.mission_clues: List[Dict] = []  # 使命线索碎片
        self.life_events: List[Dict] = []  # 重要人生事件
        self.challenges_completed: int = 0  # 完成的挑战数
        self.reflection_journal: List[Dict] = []  # 反思日记
        self.current_mission_status: str = "探索中"  # 使命状态：探索中/已发现/已确认
        self.confirmed_life_mission: Optional[str] = None  # 已确认的人生使命
        self.guidance_history: List[Dict] = []  # 虚拟人引导历史

    def add_interest(self, interest: str, source: str = None):
        """发现新兴趣领域"""
        if interest not in self.discovered_interests:
            self.discovered_interests.append(interest)
            self.life_events.append({
                "type": "interest_discovered",
                "content": f"对{interest}产生兴趣",
                "source": source,
                "timestamp": datetime.now().isoformat()
            })

    def improve_skill(self, skill: str, amount: float = 5):
        """提升技能等级"""
        if skill not in self.skill_levels:
            self.skill_levels[skill] = 0
        self.skill_levels[skill] = min(100, self.skill_levels[skill] + amount)

    def add_mission_clue(self, clue: str, context: str = None):
        """收集使命线索"""
        clue_data = {
            "clue": clue,
            "context": context,
            "timestamp": datetime.now().isoformat(),
            "connections": []  # 与其他线索的关联
        }
        self.mission_clues.append(clue_data)

        # 检查线索之间的关联（简单的关键词匹配）
        for existing in self.mission_clues[:-1]:
            if self._clues_connected(clue, existing["clue"]):
                clue_data["connections"].append(existing["clue"])
                existing["connections"].append(clue)

    def _clues_connected(self, clue1: str, clue2: str) -> bool:
        """检查两个线索是否有关联（简化版）"""
        # 这里可以用更复杂的NLP方法，暂时用关键词重叠
        words1 = set(clue1.lower().split())
        words2 = set(clue2.lower().split())
        return len(words1 & words2) >= 1

    def complete_challenge(self, challenge_name: str, description: str = ""):
        """完成一次挑战/任务"""
        self.challenges_completed += 1
        self.life_events.append({
            "type": "challenge_completed",
            "content": f"完成挑战: {challenge_name}",
            "description": description,
            "timestamp": datetime.now().isoformat()
        })

    def add_reflection(self, reflection: str, topic: str = None):
        """添加反思日记"""
        entry = {
            "topic": topic,
            "content": reflection,
            "timestamp": datetime.now().isoformat()
        }
        self.reflection_journal.append(entry)

    def confirm_mission(self, mission: str):
        """确认人生使命"""
        self.confirmed_life_mission = mission
        self.current_mission_status = "已确认"
        self.life_events.append({
            "type": "mission_confirmed",
            "content": f"确认人生使命: {mission}",
            "timestamp": datetime.now().isoformat()
        })

    def record_guidance(self, mentor_name: str, guidance_type: str, content: str):
        """记录虚拟人的引导"""
        self.guidance_history.append({
            "mentor": mentor_name,
            "type": guidance_type,  # question/task/advice/challenge
            "content": content,
            "timestamp": datetime.now().isoformat()
        })

    def get_growth_summary(self) -> Dict:
        """获取成长总结"""
        top_skills = sorted(
            self.skill_levels.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]

        return {
            "current_status": self.current_mission_status,
            "life_mission": self.confirmed_life_mission,
            "discovered_interests": self.discovered_interests,
            "top_skills": top_skills,
            "challenges_completed": self.challenges_completed,
            "mission_clues_count": len(self.mission_clues),
            "total_guidance_sessions": len(self.guidance_history)
        }

    def export_to_dict(self) -> Dict:
        """导出为字典（用于保存）"""
        return {
            "player_id": self.player_id,
            "discovered_interests": self.discovered_interests,
            "skill_levels": self.skill_levels,
            "mission_clues": self.mission_clues,
            "life_events": self.life_events,
            "challenges_completed": self.challenges_completed,
            "reflection_journal": self.reflection_journal,
            "current_mission_status": self.current_mission_status,
            "confirmed_life_mission": self.confirmed_life_mission,
            "guidance_history": self.guidance_history
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'PlayerGrowth':
        """从字典加载"""
        pg = cls(data["player_id"])
        pg.discovered_interests = data.get("discovered_interests", [])
        pg.skill_levels = data.get("skill_levels", {})
        pg.mission_clues = data.get("mission_clues", [])
        pg.life_events = data.get("life_events", [])
        pg.challenges_completed = data.get("challenges_completed", 0)
        pg.reflection_journal = data.get("reflection_journal", [])
        pg.current_mission_status = data.get("current_mission_status", "探索中")
        pg.confirmed_life_mission = data.get("confirmed_life_mission")
        pg.guidance_history = data.get("guidance_history", [])
        return pg
