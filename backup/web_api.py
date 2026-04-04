"""
OpenSims Web API Server
提供HTTP REST API和WebSocket实时推送
"""

import os
import json
import time
import uuid
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

# 导入核心模块
from virtual_human import SimPerson
from agents.manager import AgentManager
from storage import Storage
from api_client import APIClient
from auto_chat_scheduler import AutoChatScheduler
from config import *

# 初始化FastAPI
app = FastAPI(title="OpenSims Web API", version="1.0.0")

# 允许跨域（开发方便，生产环境需限制）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局实例（单例模式）
storage = Storage()
agent_manager = AgentManager(storage)
api_client = APIClient()
auto_chat_scheduler = AutoChatScheduler(agent_manager, api_client)
auto_chat_scheduler.start()

# ========== 数据模型 ==========
class CreateCharacterRequest(BaseModel):
    name: str
    personality_type: str = "中立型"
    is_player: bool = False

class ChatRequest(BaseModel):
    message: str
    target_id: Optional[str] = None

class ActionResult(BaseModel):
    success: bool
    message: str
    state: Optional[Dict[str, Any]] = None

# ========== 工具函数 ==========
def character_to_dict(vh: SimPerson) -> Dict[str, Any]:
    """将虚拟人转换为字典（API响应）"""
    return {
        "id": vh.id,
        "name": vh.name,
        "personality": vh.personality,
        "is_player": getattr(vh, 'is_player', False),
        "age": round(vh.age, 1),
        "stage": vh.stage,
        "job": vh.job,
        "health": vh.health,
        "energy": vh.energy,
        "hunger": vh.hunger,
        "social": vh.social,
        "fun": vh.fun,
        "money": vh.money,
        "mood_level": vh.mood_level,
        "alive": vh.alive,
        "memory_count": len(vh.memory)
    }

# ========== REST API 端点 ==========

@app.get("/")
async def root():
    """API根路径"""
    return {
        "name": "OpenSims Web API",
        "version": "1.0.0",
        "endpoints": {
            "characters": "/api/v1/characters",
            "actions": "/api/v1/characters/{id}/actions/{action}",
            "chat": "/api/v1/characters/{id}/chat",
            "think": "/api/v1/characters/{id}/think"
        }
    }

@app.get("/api/v1/characters")
async def list_characters():
    """获取所有虚拟人列表"""
    return {"characters": agent_manager.list_virtual_humans()}

@app.post("/api/v1/characters")
async def create_character(req: CreateCharacterRequest):
    """创建新虚拟人"""
    from config import PERSONALITY_PRESETS
    personality = PERSONALITY_PRESETS.get(req.personality_type, PERSONALITY_PRESETS["中立型"])
    vh = agent_manager.create_virtual_human(req.name, req.personality_type, personality, req.is_player)
    return character_to_dict(vh)

@app.get("/api/v1/characters/{vh_id}")
async def get_character(vh_id: str):
    """获取指定虚拟人详情"""
    vh = agent_manager.get_virtual_human(vh_id)
    if not vh:
        raise HTTPException(status_code=404, detail="Character not found")
    return character_to_dict(vh)

@app.delete("/api/v1/characters/{vh_id}")
async def delete_character(vh_id: str):
    """删除虚拟人"""
    agent_manager.delete_virtual_human(vh_id)
    return {"success": True, "message": "Character deleted"}

@app.post("/api/v1/characters/{vh_id}/actions/{action_name}")
async def execute_action(vh_id: str, action_name: str):
    """执行行动（eat, sleep, work, relax, socialize, shop, find_job）"""
    vh = agent_manager.get_virtual_human(vh_id)
    if not vh:
        raise HTTPException(status_code=404, detail="Character not found")

    action_methods = {
        "eat": vh.eat,
        "sleep": vh.sleep,
        "work": vh.work,
        "relax": vh.relax,
        "socialize": lambda: vh.socialize(),
        "shop": vh.shop,
        "find_job": vh.find_job
    }

    if action_name not in action_methods:
        raise HTTPException(status_code=400, detail=f"Unknown action: {action_name}")

    try:
        result = action_methods[action_name]()
        agent_manager.save_all()
        return {
            "success": True,
            "message": result,
            "state": character_to_dict(vh)
        }
    except Exception as e:
        return {"success": False, "message": str(e)}

@app.post("/api/v1/characters/{vh_id}/chat")
async def character_chat(vh_id: str, req: ChatRequest):
    """与虚拟人聊天（用户→虚拟人）"""
    vh = agent_manager.get_virtual_human(vh_id)
    if not vh:
        raise HTTPException(status_code=404, detail="Character not found")

    # 如果指定了target_id，则是角色间对话
    if req.target_id:
        target_vh = agent_manager.get_virtual_human(req.target_id)
        if not target_vh:
            raise HTTPException(status_code=404, detail="Target character not found")
        # 让vh向target_vh发送消息
        target_vh.add_memory("user", f"{vh.name}: {req.message}")
        reply = api_client.generate_reply(target_vh, f"{vh.name}: {req.message}")
        target_vh.add_memory("assistant", reply['reply'])
        target_vh.energy = max(0, target_vh.energy - 5)
        agent_manager.save_all()
        return {
            "success": True,
            "message": reply['reply'],
            "state": character_to_dict(target_vh)
        }
    else:
        # 用户直接与vh对话
        reply = api_client.generate_reply(vh, req.message)
        vh.add_memory("user", req.message)
        vh.add_memory("assistant", reply['reply'])
        vh.energy = max(0, vh.energy - 5)
        agent_manager.save_all()
        return {
            "success": True,
            "message": reply['reply'],
            "state": character_to_dict(vh)
        }

@app.post("/api/v1/characters/{vh_id}/think")
async def character_think(vh_id: str, goal: str):
    """调用Claude Code为虚拟人生成决策（高级功能）"""
    vh = agent_manager.get_virtual_human(vh_id)
    if not vh:
        raise HTTPException(status_code=404, detail="Character not found")

    # 构建Prompt
    prompt = f"""
你是{vh.name}，一个{vh.age:.1f}岁的{vh.stage}，职业是{vh.job}。

当前状态：
- 健康: {vh.health}/100, 精力: {vh.energy}/100
- 饥饿: {vh.hunger}/100, 社交: {vh.social}/100
- 心情: {vh.mood_level}, 金钱: ${vh.money}

目标：{goal}

请生成Python代码来帮助{vh.name}达成目标。可用方法：
self.eat(), self.sleep(), self.work(), self.relax(), self.socialize(), self.shop()
可以直接修改属性（如 self.money += 100）

只输出代码，不要解释。
"""

    try:
        # 调用Claude Code（如果配置了API密钥）
        response = api_client._api_generate(vh, prompt)
        generated_code = response.get("reply", "# Claude未配置，使用Mock回复\nself.eat()")
    except Exception as e:
        generated_code = f"# 错误: {str(e)}"

    return {
        "success": True,
        "goal": goal,
        "generated_code": generated_code,
        "character": character_to_dict(vh)
    }

@app.post("/api/v1/characters/{vh_id}/switch-active")
async def switch_active_character(vh_id: str):
    """切换当前活跃（玩家控制）角色"""
    agent_manager.set_active(vh_id)
    vh = agent_manager.get_active()
    return {
        "success": True,
        "active_character": character_to_dict(vh) if vh else None
    }

@app.get("/api/v1/system/status")
async def system_status():
    """系统状态"""
    return {
        "auto_chat_running": auto_chat_scheduler.running,
        "total_characters": len(agent_manager.virtual_humans),
        "active_character": agent_manager.get_active().id if agent_manager.get_active() else None
    }

@app.post("/api/v1/system/auto-chat/start")
async def start_auto_chat():
    """启动自动聊天"""
    auto_chat_scheduler.start()
    return {"success": True, "message": "Auto-chat started"}

@app.post("/api/v1/system/auto-chat/stop")
async def stop_auto_chat():
    """停止自动聊天"""
    auto_chat_scheduler.stop()
    return {"success": True, "message": "Auto-chat stopped"}

# ========== WebSocket 实时推送 ==========
class ConnectionManager:
    """WebSocket连接管理器"""
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, event: str, data: Dict[str, Any]):
        """广播事件到所有连接的客户端"""
        message = json.dumps({
            "event": event,
            "data": data,
            "timestamp": datetime.now().isoformat()
        })
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                pass

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket连接端点"""
    await manager.connect(websocket)
    try:
        while True:
            # 保持连接活跃，客户端可以发送心跳
            data = await websocket.receive_text()
            # 可以处理客户端消息
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# 广播事件的辅助函数（在auto_chat_scheduler中调用）
async def broadcast_auto_chat(vh1_name: str, vh2_name: str, message: str):
    await manager.broadcast("auto_chat", {
        "from": vh1_name,
        "to": vh2_name,
        "message": message
    })

# 修改auto_chat_scheduler调用广播（需导入）
# auto_chat_scheduler.py 需要修改以调用 broadcast_auto_chat

if __name__ == "__main__":
    import uvicorn
    print("Starting OpenSims Web API Server...")
    print("Visit: http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)