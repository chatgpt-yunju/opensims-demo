#!/usr/bin/env python3
"""
设置管理模块 - 处理 settings.json 的加载和保存
"""

import json
import os
from typing import Dict, Any

DEFAULT_SETTINGS = {
    "api_endpoint": "https://api.yunjunet.cn/v1/chat/completions",
    "api_key": "",
    "model": "step-3.5-flash",
    "use_mock": False,
    "auto_chat_enabled": False,
    "auto_chat_rounds": 10,
    "auto_chat_interval": 30  # 自动对话间隔（秒）
}

SETTINGS_FILE = "settings.json"


def load_settings() -> Dict[str, Any]:
    """从文件加载设置，如果不存在则返回默认值"""
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            # 合并默认值，确保所有键都存在
            merged = DEFAULT_SETTINGS.copy()
            merged.update(settings)
            return merged
        except Exception as e:
            print(f"[Settings] 加载设置失败: {e}，使用默认值")
            return DEFAULT_SETTINGS.copy()
    else:
        return DEFAULT_SETTINGS.copy()


def save_settings(settings: Dict[str, Any]) -> bool:
    """保存设置到文件"""
    try:
        # 只保存有效字段
        to_save = {k: settings.get(k, DEFAULT_SETTINGS[k]) for k in DEFAULT_SETTINGS.keys()}
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(to_save, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"[Settings] 保存设置失败: {e}")
        return False


def get_settings_path() -> str:
    """获取设置文件路径（绝对路径）"""
    return os.path.abspath(SETTINGS_FILE)
