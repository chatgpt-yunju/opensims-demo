# OpenSims - 模拟人生 + OpenClaw Agent平台

**灵魂永生模式 · 玩家/AI共存 · 可编程Agent系统**

[![GitHub stars](https://img.shields.io/github/stars/chatgpt-yunju/opensims-demo)](https://github.com/chatgpt-yunju/opensims-demo)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

---

## 🎮 什么是OpenSims？

OpenSims是一个**可编程的虚拟人生模拟平台**，允许您：

- ✅ **创建多个虚拟人**：每个都有独特性格、职业、状态
- ✅ **灵��永生模式**：无限行动、永不死亡、自由探索
- ✅ **玩家/AI模式**：指定一个"玩家"角色亲自控制，其他AI自动生活
- ✅ **自动聊天系统**：AI角色之间自主对话，形成社交网络
- ✅ **OpenClaw API**：外部程序可调用虚拟人执行复杂任务（Claude Code集成）
- ✅ **多接口支持**：HTTP REST API、CLI命令行、Windows命名管道

---

## 🚀 快速开始

### 1. 安装依赖

```bash
cd G:/opensims_demo
pip install -r requirements.txt
```

### 2. 运行游戏（CLI）

```bash
python main.py
```

### 3. 体验模拟人生

```
============================================================
    第 0 天   小明  [young_adult]
============================================================
=== 小明 的人生状态 ===
年龄: 18.0岁 | 阶段: young_adult | 职业: 待业
健康: 100/100 | 精力: 100/100 | 心情: 普通
饥饿: 60/100 (饱)
社交: 50/100 | 娱乐: 50/100
金钱: $1000 (今日收入: $0, 支出: $0)
今日行动: 0/999
存活: 是
------------------------------------------------------------
行动选项（灵魂永生模式）:
  1. 吃饭   2. 睡觉   3. 工作   4. 找工作
  5. 娱乐   6. 社交   7. 购物   8. 聊天（当前）
  9. 聊天（指定其他人） 10. 结束今天
  11. 查看所有角色 12. 切换角色 13. 创建AI角色 14. 退出
请选择行动:
```

---

## 🎯 核心玩法

### 创建角色

**首次运行**会提示创建角色：
```
角色昵称: [输入名字]
选择性格: [温柔型/幽默型/严肃型/中立型]
这是你要控制的角色吗？(y/N): y  ← 输入y创建玩家角色，N创建AI角色
```

**推荐初始配置**：
1. 创建1个**玩家角色**（自己控制）
2. 创建3-5个**AI角色**（自动生活）
3. 观察AI之间的自动对话

### 主要操作

| 选项 | 操作 | 说明 |
|------|------|------|
| 1-7 | 各种行动 | 吃饭、睡觉、工作、娱乐、社交、购物 |
| 8 | 聊天（当前） | 与当前控制的角色对话（调用AI或Mock） |
| 9 | 指挥聊天 | 让当前角色与指定其他角色对话 |
| 10 | 结束今天 | 触发状态衰减、年龄增长、随机事件 |
| 11 | 查看所有角色 | 显示所有虚拟人的详细信息 |
| 12 | 切换角色 | 切换到其他角色进行控制 |
| 13 | 创建AI角色 | 添加新的AI虚拟人（自动生活） |
| 14 | 退出 | 保存并退出 |

### 观察自动互动

- **自动聊天调度器**：每30秒有50%概率触发两个AI角色对话
- 玩家角色**不会**参与自动聊天（保持玩家专属）
- 自动聊天会显示在屏幕上，并记录到对话历史

---

## ⚙️ 配置选项

编辑 `config.py`：

### 游戏参数

```python
# 灵魂永生模式
DAY_ACTIONS_LIMIT = 999  # 每日行动次数（999≈无限）

# 自动聊天
AUTO_CHAT_ENABLED = True           # 是否启用��动聊天
AUTO_CHAT_INTERVAL = 30            # 检查间隔（秒）
AUTO_CHAT_PROBABILITY = 0.5        # 触发对话概率（0-1）
AUTO_CHAT_EXCLUDE_PLAYER = True    # 自动聊天是否排除玩家角色

# 职业列表
PROFESSIONS = [
    "上班族", "程序员", "主播", "画家", "外卖员",
    "教师", "医生", "律师", "工程师", "自由职业"
]
```

### API配置

```python
# OpenAI兼容API（用于虚拟人对话）
API_ENDPOINT = "https://api.yunjunet.cn/v1/chat/completions"
API_KEY = "sk-..."  # 您的API密钥
API_MODEL = "step-3.5-flash"
USE_MOCK = False  # True使用内置Mock回复（无需API）
```

---

## 🔌 OpenClaw调用接口

OpenSims可作为**Agent服务**被其他程序调用，执行复杂任务。

### 方式1：HTTP REST API

启动API服务器（需添加 `--api-server` 参数，或修改main.py）：

```bash
# 安装FastAPI
pip install fastapi uvicorn

# 启动API服务器（端口8000）
uvicorn openclaw_api:app --host 127.0.0.1 --port 8000
```

#### API端点

##### 虚拟人管理

```http
GET    /api/v1/virtual-humans           # 列表所有
POST   /api/v1/virtual-humans           # 创建
GET    /api/v1/virtual-humans/{id}      # 详情
DELETE /api/v1/virtual-humans/{id}      # 删除
```

##### 行动控制

```http
POST /api/v1/virtual-humans/{id}/actions/eat
POST /api/v1/virtual-humans/{id}/actions/sleep
POST /api/v1/virtual-humans/{id}/actions/work
POST /api/v1/virtual-humans/{id}/actions/chat
{
  "target": "小明",          # 可选，对话对象
  "message": "你好呀！"       # 对话内容
}
```

##### Claude Code决策（高级）

```http
POST /api/v1/virtual-humans/{id}/think
{
  "goal": "提高社交能力",
  "context": {
    "location": "咖啡馆",
    "other_characters": ["小明", "小红"]
  }
}

# 响应
{
  "thought_process": "分析当前社交需求低，建议参加聚会",
  "generated_code": "self.socialize('小明'); self.relax()",
  "execution_result": {"success": true},
  "new_state": {"social": 55, "fun": 65}
}
```

##### 系统控制

```http
POST /api/v1/system/auto-chat/start   # 启动自动聊天
POST /api/v1/system/auto-chat/stop    # 停止自动聊天
GET  /api/v1/system/status            # 服务状态
```

#### Python调用示例

```python
import requests

BASE = "http://localhost:8000"

# 创建虚拟人
resp = requests.post(f"{BASE}/api/v1/virtual-humans", json={
    "name": "玩家",
    "personality": {"friendliness": 0.8},
    "is_player": True
})
player_id = resp.json()["id"]

# 执行工作
result = requests.post(f"{BASE}/api/v1/virtual-humans/{player_id}/actions/work")
print(result.json()["result"])  # "工作完成，赚了$200"

# 请求Claude决策
think = requests.post(f"{BASE}/api/v1/virtual-humans/{player_id}/think", json={
    "goal": "提高社交能力",
    "context": {"location": "home"}
})
print(f"Claude建议: {think.json()['generated_code']}")
```

---

### 方式2：CLI命令行

OpenSims提供命令行接口，适合批处理和脚本：

```bash
# 创建虚拟人
python main.py --create "小明" --personality "幽默型" --is-player false

# 执行行动
python main.py --action work --agent "小明"

# 聊天
python main.py --chat "小明" "你好呀！"

# Claude决策（需要配置Claude API）
python main.py --think "小明" "如何提高社交？"

# 结束今天
python main.py --end-day
```

#### CLI参数详解

```bash
python main.py [命令]

命令：
  --create <名字> [--personality <性格>] [--is-player true/false]
      创建新虚拟人

  --action <行动名> --agent <角色名> [--params key=value ...]
      执行预定义行动（eat/sleep/work/relax/socialize/shop/find_job）

  --chat <角色名> <消息内容>
      与指定角色对话

  --think <角色名> <目标>
      调用Claude Code为角色生成决策代码

  --end-day
      结束当天，触发衰减、事件、年龄增长

  --list
      列出所有虚拟人

  --select <角色ID>
      切换当前控制角色

  --auto-chat start/stop/status
      控制自动聊天调度器

  --serve
      启动HTTP API服务器（需要安装fastapi）
```

---

### 方式3：Windows命名管道（高性能）

OpenClaw守护进程通过命名管道接收任务，适合实时嵌入式调用。

```python
# Python客户端示例
import json
import win32file
import win32pipe

pipe_name = r"\\.\pipe\OpenClawPipe"

def send_task(task: dict) -> dict:
    """发送任务到OpenClaw管道并获取结果"""
    handle = win32file.CreateFile(
        pipe_name,
        win32file.GENERIC_READ | win32file.GENERIC_WRITE,
        0, None, win32file.OPEN_EXISTING, 0, None
    )

    # 发送任务
    win32file.WriteFile(handle, json.dumps(task).encode())

    # 读取响应
    status, data = win32file.ReadFile(handle, 65536)
    return json.loads(data.decode())

# 使用示例
result = send_task({
    "type": "think",
    "agent_id": "player",
    "goal": "规划未来三天"
})
print(result["generated_code"])
```

---

## 🏗️ 作为Windows服务运行

将OpenClaw安装为系统服务，开机自启动：

```bash
# 安装服务（需要管理员权限）
opensims_service.exe --install

# 启动服务
net start OpenClaw

# 停止服务
net stop OpenClaw

# 卸载服务
opensims_service.exe --install --uninstall
```

服务运行后，可通过任何接口（HTTP/管道）调用。

---

## 🧪 测试

运行单元测试：

```bash
# SimPerson核心功能
python test_sim_person.py

# 多虚拟人管理
python test_multi_vh.py

# 完整游戏流程
python test_sim_game.py

# 平衡性测试
python test_balancing.py
```

---

## 📁 项目结构

```
opensims_demo/
├── agents/
│   ├── __init__.py
│   └── manager.py          # 多虚拟人管理
├── auto_chat_scheduler.py  # 自动聊天调度器
├── virtual_human.py        # SimPerson核心类（模拟人生）
├── api_client.py           # API客户端（OpenAI兼容）
├── storage.py              # JSON持久化
├── config.py               # 配置文件
├── main.py                 # CLI主程序（游戏入口）
├── openclaw_api.py         # HTTP API服务器（待实现）
├── openclaw_cli.py         # CLI命令封装（待实现）
├── openclaw_service.py     # Windows服务（待实现）
├── test_*.py               # 测试文件
├── requirements.txt        # 依赖
├── README.md               # 本文档
└── COMPREHENSIVE_README.md # 完整文档（本文件）
```

---

## 🎨 角色属性系统

### SimPerson核心属性

| 属性 | 范围 | 说明 |
|------|------|------|
| `age` | float | 年龄（可小数，如25.3岁） |
| `stage` | str | 人生阶段：baby/toddler/child/teen/young_adult/adult/middle_age/senior |
| `job` | str | 职业（10种可选） |
| `health` | 0-100 | 健康值 |
| `energy` | 0-100 | 精力值 |
| `hunger` | 0-100 | 饥饿度（越高越饱） |
| `social` | 0-100 | 社交需求满足度 |
| `fun` | 0-100 | 娱乐需求 |
| `mood_level` | str | 情绪：开心/普通/低落/生气/崩溃 |
| `money` | int | 金钱（美元） |
| `alive` | bool | 是否存活（永生模式下始终True） |

### 情绪计算

情绪基于5大属性平均值：
```
avg = (health/20 + hunger/50 + energy/30 + social/40 + fun/40) / 5

avg >= 0.8: 开心
avg >= 0.6: 普通
avg >= 0.4: 低落
avg >= 0.2: 生气
else: 崩溃
```

---

## 🔧 开发指南

### 添加新行动

修改 `virtual_human.py`，在 `SimPerson` 类中添加方法：

```python
def exercise(self):
    """健身行动"""
    cost = 20
    if self.money >= cost:
        self.health = min(100, self.health + 30)
        self.energy = max(0, self.energy - 20)
        self.money -= cost
        self.actions_today += 1
        return "健身完成，身体更健康了"
    return "钱不够请教练！"
```

然后在 `main.py` 添加菜单选项即可。

### 扩展职业列表

编辑 `config.py`：

```python
PROFESSIONS = [
    "上班族", "程序员", "主播", "画家", "外卖员",
    "教师", "医生", "律师", "工程师", "自由职业",
    "运动员", "演员", "科学家"  # 新增
]
```

薪资在 `SimPerson.work()` 方法中配置。

---

## 🔮 路线图

- [x] Sprint 1: 多虚拟人 + 模拟人生核心
- [x] 灵魂永生模式（无限行动、永不死亡）
- [x] 玩家/AI角色区分
- [x] 自动聊天调度器
- [ ] OpenClaw HTTP API 服务器
- [ ] CLI包装器（openclaw_cli.py）
- [ ] Windows服务（openclaw_service.exe）
- [ ] WebSocket实时推送
- [ ] Claude Code深度集成（智能决策）
- [ ] GUI图形界面（Tkinter/Qt）
- [ ] 关系系统（友情、爱情、家庭）
- [ ] 物品/房产系统
- [ ] 多代模拟（生小孩）

---

## 🤝 贡献

欢迎提交Issue和Pull Request！

---

## 📄 许可证

MIT License

---

## 🙏 致谢

- Anthropic Claude Code API
- Python community
- 所有测试用户

---

**Made with ❤️ by OpenSims Team**
**版本**: 1.0 (Soul Immortality Edition)
**最后更新**: 2026-04-04