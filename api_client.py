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
            response = self._mock_generate(vh, user_input)
        else:
            response = self._api_generate(vh, user_input)

        # Human-like Chat 增强：应用6个真人特征
        if hasattr(vh, 'human_like_chat'):
            # 构造当前状态（从 vh.state 中读取）
            vh_state = {
                "energy": vh.state.get("energy", 100),
                "mood": vh.state.get("mood", "普通"),
                "relationship": vh.state.get("relationship", 0)
            }
            # 额外状态
            extra_state = {
                "hunger": getattr(vh, 'hunger', 60),
                "health": getattr(vh, 'health', 100),
                "fun": getattr(vh, 'fun', 50)
            }
            enhanced = vh.human_like_chat.enhance_reply(
                response["reply"],
                user_input,
                vh_state=vh_state,
                vh_extra_state=extra_state
            )
            response["reply"] = enhanced

        return response

    def _mock_generate(self, vh: SimPerson, user_input: str) -> Dict:
        """Mock回复引擎（无需API）"""
        # 基于性格选择回复风格
        friendliness = vh.personality.get("friendliness", 0.5)
        humor = vh.personality.get("humor", 0.5)

        # 简单关键词匹配（扩展）
        responses = {
            "你好": ["你好呀！", "嗨～", "很高兴见到你！"],
            "名字": [f"我叫{vh.name}呀", "你可以叫我{vh.name}"],
            "天气": ["今天天气不错呢", "我不太方便出门呢"],
            "再见": ["再见！", "下次再聊～", "拜拜！"],
            # 职业与赚钱相关
            "赚钱": ["赚钱这事说来话长...", "我理解你在考虑收入来源。", "关于赚钱，我觉得要先明确自己的优势。"],
            "工作": ["工作啊，我最近也在思考职业规划。", "你现在做什么工作？", "工作是为了生活，但也可以很有意义。"],
            "职业": ["职业选择确实重要。", "你有什么感兴趣的行业吗？", "我觉得职业要和性格匹配。"],
            "钱": ["钱的事情确实要重视。", "虽然钱不是万能的，但很重要。", "你是在考虑理财吗？"],
            "收入": ["收入来源可以是多元的。", "你现在的收入够用吗？", "增加收入需要时间和技能。"],
            # 学习与成长
            "学习": ["学习是个终身的过程。", "你想学什么？", "我之前也花了很多时间学习。"],
            "技能": ["技能越多越自由。", "你现在掌握哪些技能？", "我建议你学点实用的技能。"],
            "教育": ["教育改变命运。", "你是在考虑深造吗？", "现在学习渠道很多。"],
            # 情感支持
            "累了": ["累了吗？那休息一下吧。", "感觉累的时候要适当放松。", "我懂那种疲惫的感觉。"],
            "困": ["困了就早点睡吧。", "睡眠很重要，别熬夜。", "我也困了..."],
            "饿": ["说到吃的，我也有点饿了。", "饿了就去吃点东西吧。", "健康饮食很重要。"],
            "开心": ["开心就好！", "看到你开心我也很高兴。", "有什么开心事分享一下？"],
            "难过": ["别难过，一切都会好的。", "我在这里陪着你。", "需要我陪你聊聊吗？"]
        }

        # 检查关键词
        matched = False
        for keyword, options in responses.items():
            if keyword in user_input:
                reply = random.choice(options)
                matched = True
                break

        if not matched:
            # 上下文感知的默认回复（基于用户输入长度和问题类型）
            if "?" in user_input or any(q in user_input for q in ["怎么", "如何", "为什么", "什么", "吗", "呢"]):
                # 用户提问但无匹配关键词
                question_responses = [
                    "这是个好问题，让我想想...",
                    "你问的这个问题挺有意思的。",
                    "我不太确定，但我们可以一起探讨。",
                    "这个问题需要具体情况分析。",
                    "你期望的答案是什么？先说说你的想法吧。"
                ]
                reply = random.choice(question_responses)
            elif len(user_input) < 5:
                # 简短输入
                short_responses = {
                    friendliness > 0.6: ["嗯嗯", "我在呢", "接着说", "好哒"],
                    friendliness <= 0.6: ["嗯", "哦", "知道了"]
                }
                reply = random.choice(short_responses[True if friendliness > 0.6 else False])
            else:
                # 一般陈述
                statement_responses = [
                    "我明白了。",
                    "原来如此。",
                    "interesting...",
                    "继续说，我在听。",
                    "然后呢？"
                ]
                reply = random.choice(statement_responses)

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
        # 会话管理：确保每个对话有唯一会话ID
        session_id = getattr(vh, 'current_session_id', None)
        if not session_id:
            session_id = str(uuid.uuid4())
            vh.current_session_id = session_id

        # 限制历史长度：最多保留10轮对话（用户+助手=20条）
        max_history = 10
        if len(vh.memory) > max_history * 2:
            # 保留最近的对话，但保留第一条作为"开场"
            keep_start = 1  # 保留第一条系统开场
            vh.memory = vh.memory[:keep_start] + vh.memory[-(max_history*2-1):]

        # 构建消息历史（OpenAI格式）
        messages = []

        # System消息：角色设定
        system_prompt = f"""你是一个虚拟人，名字是{vh.name}。
性格参数：友好度{vh.personality.get('friendliness', 0.5):.1f}/1.0，
幽默度{vh.personality.get('humor', 0.5):.1f}/1.0，
严肃度{vh.personality.get('seriousness', 0.5):.1f}/1.0。

当前状态：能量值{vh.state['energy']}/100，情绪{vh.state['mood']}，与用户关系{vh.state.get('relationship', 0)}/100。

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