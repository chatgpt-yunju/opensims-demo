#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenClaw Skill: OpenSims Integration
统一接口，支持HTTP API、MCP、Playwright三种方式调用OpenSims功能
"""

import json
import requests
from typing import Dict, Any, Optional

# 配置
API_BASE = "http://localhost:8000"
MCP_ENABLED = False  # 如果Claude Desktop环境中，会自动检测

class OpenSimsSkill:
    """OpenSims OpenClaw Skill"""

    def __init__(self, api_base: str = None):
        self.api_base = api_base or API_BASE
        self.mcp_client = None

    # ========== 虚拟人管理 ==========
    def create_character(self, name: str, personality_type: str = "中立型", is_player: bool = False) -> Dict[str, Any]:
        """创建虚拟人"""
        resp = requests.post(f"{self.api_base}/api/v1/characters", json={
            "name": name,
            "personality_type": personality_type,
            "is_player": is_player
        })
        return resp.json()

    def list_characters(self) -> list:
        """列出所有虚拟人"""
        resp = requests.get(f"{self.api_base}/api/v1/characters")
        return resp.json().get('characters', [])

    def get_character(self, character_id: str) -> Dict[str, Any]:
        """获取虚拟人详情"""
        resp = requests.get(f"{self.api_base}/api/v1/characters/{character_id}")
        return resp.json()

    def delete_character(self, character_id: str) -> bool:
        """删除虚拟人"""
        resp = requests.delete(f"{self.api_base}/api/v1/characters/{character_id}")
        return resp.json().get('success', False)

    def switch_active(self, character_id: str) -> Dict[str, Any]:
        """切换活跃角色"""
        resp = requests.post(f"{self.api_base}/api/v1/characters/{character_id}/switch-active")
        return resp.json()

    # ========== 行动执行 ==========
    def execute_action(self, character_id: str, action: str, **kwargs) -> Dict[str, Any]:
        """
        执行虚拟人行动

        可用action:
        - eat, sleep, work, relax, socialize, shop, find_job
        - chat (需要message参数)
        - create_xiaohongshu_post (需要title, content, tags可选)
        """
        url = f"{self.api_base}/api/v1/characters/{character_id}/actions/{action}"
        resp = requests.post(url, json=kwargs)
        return resp.json()

    def think(self, character_id: str, goal: str, context: Dict = None) -> Dict[str, Any]:
        """调用Claude Code为虚拟人生成决策"""
        resp = requests.post(
            f"{self.api_base}/api/v1/characters/{character_id}/think",
            json={"goal": goal, "context": context or {}}
        )
        return resp.json()

    def chat(self, character_id: str, message: str, target_id: str = None) -> Dict[str, Any]:
        """
        虚拟人聊天

        如果target_id指定，则是角色间对话；否则是用户与角色对话
        """
        return self.execute_action(character_id, "chat", message=message, target_id=target_id)

    def create_xiaohongshu_post(self, character_id: str, title: str = None, content: str = None,
                                tags: list = None, images: list = None, use_playwright: bool = False) -> Dict[str, Any]:
        """
        发布小红书笔记

        参数:
            character_id: 虚拟人ID（必须是小红书博主职业）
            title: 笔记标题（可选，未提供则自动生成）
            content: 笔记正文（可选，未提供则自动生成）
            tags: 标签列表
            images: 图片URL列表
            use_playwright: 是否使用Playwright自动化（默认False使用模拟或官方API）

        返回:
            包含success, message, state的字典
        """
        return self.execute_action(
            character_id,
            "create_xiaohongshu_post",
            title=title,
            content=content,
            tags=tags,
            images=images,
            use_playwright=use_playwright
        )

    # ========== 系统控制 ==========
    def start_auto_chat(self) -> Dict[str, Any]:
        """启动自动聊天"""
        resp = requests.post(f"{self.api_base}/api/v1/system/auto-chat/start")
        return resp.json()

    def stop_auto_chat(self) -> Dict[str, Any]:
        """停止自动聊天"""
        resp = requests.post(f"{self.api_base}/api/v1/system/auto-chat/stop")
        return resp.json()

    def system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        resp = requests.get(f"{self.api_base}/api/v1/system/status")
        return resp.json()

    # ========== MCP集成（Claude Desktop） ==========
    def use_mcp(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """
        通过MCP调用（在Claude Desktop环境中自动路由）

        注意：此方法需要在MCP服务器进程中运行
        """
        if not MCP_ENABLED:
            return "错误：MCP未启用"

        try:
            from mcp_xhs import xhs_publish, xhs_get_stats, xhs_config_info
            import asyncio

            if tool_name == "xhs_publish":
                result = asyncio.run(xhs_publish(arguments))
                return result[0].text if result else "无返回值"
            elif tool_name == "xhs_get_stats":
                result = asyncio.run(xhs_get_stats(arguments))
                return result[0].text if result else "无返回值"
            elif tool_name == "xhs_config_info":
                result = asyncio.run(xhs_config_info())
                return result[0].text if result else "无返回值"
            else:
                return f"未知工具：{tool_name}"
        except Exception as e:
            return f"MCP调用失败：{str(e)}"


# ========== OpenClaw 标准接口 ==========

def skill_initialize(config: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    OpenClaw Skill初始化接口

    返回:
        {
            "name": "opensims",
            "version": "1.0.0",
            "capabilities": ["virtual_human", "xhs_publish", "auto_chat", ...]
        }
    """
    return {
        "name": "opensims",
        "version": "1.0.0",
        "description": "OpenSims虚拟人生模拟平台集成",
        "capabilities": [
            "virtual_human.manage",
            "virtual_human.action",
            "virtual_human.chat",
            "virtual_human.think",
            "xiaohongshu.publish",
            "xiaohongshu.stats",
            "auto_chat.control",
            "system.status"
        ],
        "config": {
            "api_base": config.get("api_base", "http://localhost:8000") if config else "http://localhost:8000",
            "mcp_enabled": MCP_ENABLED
        }
    }

def skill_execute(action: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    OpenClaw Skill执行接口

    参数:
        action: 动作名称，如 "create_character", "xhs_publish", "think"
        parameters: 动作参数

    返回:
        {"success": bool, "result": any, "error": str}
    """
    skill = OpenSimsSkill(parameters.get('api_base'))

    try:
        if action == "create_character":
            result = skill.create_character(
                name=parameters['name'],
                personality_type=parameters.get('personality_type', '中立型'),
                is_player=parameters.get('is_player', False)
            )
            return {"success": True, "result": result}

        elif action == "list_characters":
            result = skill.list_characters()
            return {"success": True, "result": result}

        elif action == "get_character":
            result = skill.get_character(parameters['character_id'])
            return {"success": True, "result": result}

        elif action == "execute_action":
            result = skill.execute_action(
                character_id=parameters['character_id'],
                action=parameters['action'],
                **parameters.get('kwargs', {})
            )
            return {"success": True, "result": result}

        elif action == "xhs_publish":
            result = skill.create_xiaohongshu_post(
                character_id=parameters['character_id'],
                title=parameters.get('title'),
                content=parameters.get('content'),
                tags=parameters.get('tags'),
                images=parameters.get('images'),
                use_playwright=parameters.get('use_playwright', False)
            )
            return {"success": True, "result": result}

        elif action == "think":
            result = skill.think(
                character_id=parameters['character_id'],
                goal=parameters['goal'],
                context=parameters.get('context', {})
            )
            return {"success": True, "result": result}

        elif action == "start_auto_chat":
            result = skill.start_auto_chat()
            return {"success": True, "result": result}

        elif action == "stop_auto_chat":
            result = skill.stop_auto_chat()
            return {"success": True, "result": result}

        elif action == "system_status":
            result = skill.system_status()
            return {"success": True, "result": result}

        else:
            return {"success": False, "error": f"Unknown action: {action}"}

    except Exception as e:
        return {"success": False, "error": str(e)}


# ========== 命令行测试 ==========

if __name__ == "__main__":
    import sys

    print("OpenSims OpenClaw Skill 测试")
    print("=" * 60)

    # 测试初始化
    init = skill_initialize()
    print(f"Skill: {init['name']} v{init['version']}")
    print(f"Capabilities: {', '.join(init['capabilities'])}")

    # 检查API连接
    skill = OpenSimsSkill()
    try:
        status = skill.system_status()
        print(f"API连接: {'✅' if status else '❌'}")
    except:
        print("API连接: ❌ 请确保 web_api.py 正在运行")

    print("\n可用动作:")
    actions = [
        "create_character(name, personality_type, is_player)",
        "list_characters()",
        "get_character(character_id)",
        "execute_action(character_id, action, **kwargs)",
        "xhs_publish(character_id, title, content, tags, use_playwright)",
        "think(character_id, goal, context)",
        "start_auto_chat()",
        "stop_auto_chat()",
        "system_status()"
    ]
    for a in actions:
        print(f"  - {a}")

    print("=" * 60)
    print("使用示例:")
    print("""
from opensims_skill import skill_execute

# 创建虚拟人
result = skill_execute("create_character", {
    "name": "小红书达人",
    "personality_type": "温柔型"
})

# 发布小红书笔记
result = skill_execute("xhs_publish", {
    "character_id": "abc123",
    "title": "我的新笔记",
    "content": "这是内容...",
    "tags": ["日常", "好物"],
    "use_playwright": False
})
""")
