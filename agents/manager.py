import uuid
from typing import Dict, Optional
from virtual_human import SimPerson
from storage import Storage

class AgentManager:
    """多虚拟人管理器"""

    def __init__(self, storage: Storage):
        self.storage = storage
        self.virtual_humans: Dict[str, SimPerson] = {}
        self.active_vh_id: Optional[str] = None
        self.load_all()

    def load_all(self):
        """加载所有虚拟人"""
        data = self.storage.load_all_virtual_humans()
        if data:
            for vh_data in data.get("virtual_humans", []):
                vh = SimPerson.from_dict(vh_data)
                self.virtual_humans[vh_data["id"]] = vh
            self.active_vh_id = data.get("active_vh_id")
            print(f"[AgentManager] 加载了 {len(self.virtual_humans)} 个虚拟人")
        else:
            print("[AgentManager] 无现有数据")

    def create_virtual_human(self, name: str, personality_type: str, personality: dict, is_player: bool = False) -> SimPerson:
        """创建新虚拟人"""
        import time
        vh_id = str(uuid.uuid4())[:8]
        vh = SimPerson(name, personality, vh_id=vh_id, age=18)
        vh.created_at = time.time()
        vh.is_player = is_player  # 标记是否为玩家角色
        self.virtual_humans[vh_id] = vh
        self.set_active(vh_id)
        self.save_all()
        print(f"[AgentManager] 创建虚拟人 {name} (ID: {vh_id}, {'玩家' if is_player else 'AI'})")
        return vh

    def get_virtual_human(self, vh_id: str) -> Optional[SimPerson]:
        """获取指定虚拟人"""
        return self.virtual_humans.get(vh_id)

    def get_active(self) -> Optional[SimPerson]:
        """获取当前活跃虚拟人"""
        if self.active_vh_id:
            return self.virtual_humans.get(self.active_vh_id)
        return None

    def set_active(self, vh_id: str):
        """设置活跃虚拟人"""
        if vh_id in self.virtual_humans:
            self.active_vh_id = vh_id
            self.save_all()
            print(f"[AgentManager] 切换至虚拟人 {self.virtual_humans[vh_id].name}")

    def delete_virtual_human(self, vh_id: str):
        """删除虚拟人"""
        if vh_id in self.virtual_humans:
            name = self.virtual_humans[vh_id].name
            del self.virtual_humans[vh_id]
            if self.active_vh_id == vh_id:
                self.active_vh_id = None
            self.save_all()
            print(f"[AgentManager] 删除虚拟人 {name}")

    def list_virtual_humans(self):
        """列出所有虚拟人"""
        result = []
        for vh_id, vh in self.virtual_humans.items():
            data = {
                "id": vh_id,
                "name": vh.name,
                "personality": vh.personality,
                "state": vh.state,
                "memory_count": len(vh.memory),
                "is_active": vh_id == self.active_vh_id,
                "is_player": getattr(vh, 'is_player', False)
            }
            if hasattr(vh, 'age'):
                data.update({
                    "age": vh.age,
                    "stage": vh.stage,
                    "job": vh.job,
                    "money": vh.money,
                    "health": vh.health,
                    "alive": vh.alive
                })
            result.append(data)
        return result

    def save_all(self):
        """保存所有虚拟人"""
        data = {
            "version": "2.0",
            "virtual_humans": [
                vh.to_dict() for vh in self.virtual_humans.values()
            ],
            "active_vh_id": self.active_vh_id
        }
        self.storage.save_all(data)