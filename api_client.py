import os
import requests
import random
from typing import Dict
from virtual_human import SimPerson
from config import API_ENDPOINT, API_TIMEOUT, USE_MOCK, API_MODEL

class APIClient:
    """API客户端（支持OpenAI兼容格式和Mock降级）"""

    def __init__(self):
        self.endpoint = API_ENDPOINT
        self.timeout = API_TIMEOUT
        self.use_mock = USE_MOCK
        # 从环境变量读取API密钥（优先级高于配置文件）
        self.api_key = os.getenv("OPENSIMS_API_KEY", "")
        self.model = API_MODEL

    def generate_reply(self, vh: SimPerson, user_input: str) -> Dict:
        """生成回复（Mock或真实API）"""
        # 如果配置为Mock mode或未配置API密钥，使用Mock
        if self.use_mock or not self.api_key:
            return self._mock_generate(vh, user_input)
        else:
            return self._api_generate(vh, user_input)

    def _mock_generate(self, vh: SimPerson, user_input: str) -> Dict:
        """Mock回复引擎（无需API）"""
        # 基于性格选择回复风格
        friendliness = vh.personality.get("friendliness", 0.5)
        humor = vh.personality.get("humor", 0.5)

        # 简单关键词匹配
        responses = {
            "你好": ["你好呀！", "嗨～", "很高兴见到你！"],
            "名字": [f"我叫{vh.name}呀", "你可以叫我{}".format(vh.name)],
            "天气": ["今天天气不错呢", "我不太方便出门呢"],
            "再见": ["再见！", "下次再聊～", "拜拜！"],
        }

        # 检查关键词
        for keyword, options in responses.items():
            if keyword in user_input:
                reply = random.choice(options)
                break
        else:
            # 默认回复库
            default_friendly = [
                "嗯嗯，我在听呢～",
                " interesting!",
                "我明白你的意思了",
                "然后呢？"
            ]
            default_neutral = [
                "哦。",
                "知道了。",
                "嗯。"
            ]

            if friendliness > 0.6:
                reply = random.choice(default_friendly)
            else:
                reply = random.choice(default_neutral)

            # 加上幽默感修饰
            if humor > 0.6 and random.random() < 0.3:
                reply += " 😄"

        return {
            "reply": reply,
            "emotion": self._mood_from_friendliness(friendliness),
            "energy_delta": -random.randint(1, 3)
        }

    def _mood_from_friendliness(self, friendliness: float) -> str:
        """根据友好度推断情绪"""
        if friendliness > 0.7:
            return random.choice(["happy", "excited"])
        elif friendliness < 0.4:
            return random.choice(["neutral", "serious"])
        else:
            return "neutral"

    def _api_generate(self, vh: SimPerson, user_input: str) -> Dict:
        """调用OpenAI兼容API"""
        # 构建消息历史（OpenAI格式）
        messages = []

        # System消息：角色设定
        system_prompt = f"""你是一个虚拟人，名字是{vh.name}。
性格参数：友好度{vh.personality.get('friendliness', 0.5):.1f}/1.0，
幽默度{vh.personality.get('humor', 0.5):.1f}/1.0，
严肃度{vh.personality.get('seriousness', 0.5):.1f}/1.0。

当前状态：能量值{vh.state['energy']}/100，情绪{vh.state['mood']}，与用户关系{vh.state['relationship']}/100。

请以这个虚拟人的身份回复用户，保持性格一致。回复要简洁自然，符合情绪状态。"""

        messages.append({"role": "system", "content": system_prompt})

        # 添加对话历史
        for mem in vh.get_context():
            messages.append({
                "role": mem["role"],
                "content": mem["content"]
            })

        # 添加当前用户输入
        messages.append({"role": "user", "content": user_input})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 500
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        try:
            resp = requests.post(
                self.endpoint,
                json=payload,
                headers=headers,
                timeout=self.timeout
            )
            resp.raise_for_status()
            data = resp.json()

            # 解析OpenAI格式响应
            if "choices" in data and len(data["choices"]) > 0:
                reply = data["choices"][0]["message"]["content"].strip()
            else:
                raise ValueError("API响应格式错误：缺少choices")

            return {
                "reply": reply,
                "emotion": vh.state["mood"],  # 暂不更新，保持原情绪
                "energy_delta": -2
            }
        except requests.RequestException as e:
            print(f"[APIClient] API调用失败: {e}")
            # 降级到Mock模式
            print("[APIClient] 降级到Mock回复")
            return self._mock_generate(vh, user_input)
        except Exception as e:
            print(f"[APIClient] 解析响应失败: {e}")
            return self._mock_generate(vh, user_input)