import json
import os
from typing import Optional, Dict, List
from virtual_human import SimPerson

class Storage:
    """JSON文件存储管理（支持多虚拟人）"""

    def __init__(self, filepath: str = "demo_data.json"):
        self.filepath = filepath

    # ========== 单虚拟人方法（向后兼容） ==========
    def save_virtual_human(self, vh: SimPerson) -> bool:
        """保存单个虚拟人（兼容旧版本）"""
        try:
            data = {
                "name": vh.name,
                "personality": vh.personality,
                "memory": vh.memory,
                "state": vh.state,
                "version": "1.0"
            }
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"[Storage] 保存失败: {e}")
            return False

    def load_virtual_human(self) -> Optional[SimPerson]:
        """加载单个虚拟人（兼容旧版本）"""
        try:
            if not os.path.exists(self.filepath):
                return None

            with open(self.filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 使用 SimPerson.from_dict 统一加载
            vh = SimPerson.from_dict(data)
            return vh
        except Exception as e:
            print(f"[Storage] 加载失败: {e}")
            return None

    # ========== 多虚拟人方法（新） ==========
    def save_all(self, data: dict):
        """保存所有虚拟人数据"""
        try:
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[Storage] 保存所有失败: {e}")

    def load_all_virtual_humans(self) -> Optional[dict]:
        """加载所有虚拟人数据"""
        try:
            if not os.path.exists(self.filepath):
                return None
            with open(self.filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[Storage] 加载所有失败: {e}")
            return None

    def clear_data(self):
        """清空存储（用于重置）"""
        try:
            if os.path.exists(self.filepath):
                os.remove(self.filepath)
        except Exception as e:
            print(f"[Storage] 清空失败: {e}")