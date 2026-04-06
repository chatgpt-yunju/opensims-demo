import os
import uuid  # 用于生成会话ID
import json
import requests
import random
from typing import Dict
from virtual_human import SimPerson
from config import API_ENDPOINT, API_TIMEOUT, USE_MOCK, API_MODEL

# 尝试加载 .env 文件（如果存在）
try:
    from dotenv import load_dotenv
    load_dotenv()  # 加载 .env 文件中的环境变量
except ImportError:
    pass  # dotenv 未安装，忽略（依赖 requirements.txt）

class APIClient:
    """API客户端（支持OpenAI兼容格式和Mock降级）"""

    def __init__(self):
        self.endpoint = API_ENDPOINT
        self.timeout = API_TIMEOUT
        self.use_mock = USE_MOCK
        # 从环境变量读取API密钥（支持多个变量名，按优先级）
        # 1. ANTHROPIC_AUTH_TOKEN (用户提供的格式)
        # 2. OPENSIMS_API_KEY (原始格式)
        self.api_key = os.getenv("ANTHROPIC_AUTH_TOKEN", "") or os.getenv("OPENSIMS_API_KEY", "")
        # 如果提供了ANTHROPIC_BASE_URL，覆盖配置的API_ENDPOINT
        if os.getenv("ANTHROPIC_BASE_URL"):
            self.endpoint = os.getenv("ANTHROPIC_BASE_URL").rstrip('/') + "/v1/chat/completions"
        self.model = API_MODEL

    def generate_reply(self, vh: SimPerson, user_input: str, stream_callback=None) -> Dict:
        """生成回复（Mock或真实API）

        Args:
            vh: 虚拟人实例
            user_input: 用户输入
            stream_callback: 流式回调函数，接收文本片段；如果为None则返回完整回复

        Returns:
            包含 reply, emotion, energy_delta 的字典（仅当 stream_callback 为None时有效）
        """
        # 如果配置为Mock mode或未配置API密钥，使用Mock
        if self.use_mock or not self.api_key:
            response = self._mock_generate(vh, user_input, stream_callback)
        else:
            response = self._api_generate(vh, user_input, stream_callback)

        # 如果使用了流式回调，直接返回 None（结果已通过回调处理）
        if stream_callback:
            return None

        # Human-like Chat 增强：应用6个真人特征（仅对完整回复）
        if hasattr(vh, 'human_like_chat'):
            vh_state = {
                "energy": vh.state.get("energy", 100),
                "mood": vh.state.get("mood", "���通"),
                "relationship": vh.state.get("relationship", 0)
            }
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

    def _mock_generate(self, vh: SimPerson, user_input: str, stream_callback=None) -> Dict:
        """Mock回复引擎（无需API）- 模拟多Agent深度分析"""
        friendliness = vh.personality.get("friendliness", 0.5)
        humor = vh.personality.get("humor", 0.5)
        seriousness = vh.personality.get("seriousness", 0.5)

        # 判断问题类型
        question_words = ["怎么", "如何", "为什么", "什么", "吗", "呢", "?", "？"]
        is_question = any(q in user_input for q in question_words)
        is_complex = len(user_input) > 10 and ("如何" in user_input or "怎么" in user_input or "为什么" in user_input)

        # 简单关键词匹配（保持兼容）
        simple_responses = {
            "你好": ["你好呀！", "嗨～", "很高兴见到你！"],
            "名字": [f"我叫{vh.name}呀", f"你可以叫我{vh.name}"],
            "天气": ["今天天气不错呢", "我不太方便出门呢"],
            "再见": ["再见！", "下次再聊～", "拜拜！"]
        }

        for keyword, options in simple_responses.items():
            if keyword in user_input:
                reply = random.choice(options)
                if stream_callback:
                    for ch in reply:
                        stream_callback(ch)
                    return None
                return {"reply": reply, "emotion": self._mood_from_friendliness(friendliness), "energy_delta": -2}

        # 对于复杂问题，使用多Agent协作式深度回复
        deep_analysis_keywords = ["赚钱", "钱", "收入", "财", "工作", "职业", "找工作", "学习", "技能", "教育", "培训"]
        has_deep_topic = any(k in user_input for k in deep_analysis_keywords)

        if is_question and (is_complex or has_deep_topic):
            reply = self._generate_deep_analysis(vh, user_input, friendliness, humor, seriousness)
        else:
            reply = self._simple_reply(user_input, friendliness, humor)

        if stream_callback:
            # 模拟流式输出 - 逐字符或逐词发送
            import time
            for ch in reply:
                stream_callback(ch)
                time.sleep(0.01)  # 模拟打字速度
            return None

        return {"reply": reply, "emotion": self._mood_from_friendliness(friendliness), "energy_delta": -random.randint(1, 3)}

    def _simple_reply(self, user_input: str, friendliness: float, humor: float) -> str:
        """简单回复（兼容原有逻辑）"""
        # 关键词扩展
        responses = {
            "赚钱": ["赚钱这事说来话长...", "我理解你在考虑收入来源。", "关于赚钱，我觉得要先明确自己的优势。"],
            "工作": ["工作啊，我最近也在思考职业规划。", "你现在做什么工作？", "工作是为了生活，但也可以很有意义。"],
            "职业": ["职业选择确实重要。", "你有什么感兴趣的行业吗？", "我觉得职业要和性格匹配。"],
            "钱": ["钱的事情确实要重视。", "虽然钱不是万能的，但很重要。", "你是在考虑理财吗？"],
            "收入": ["收入来源可以是多元的。", "你现在的收入够用吗？", "增加收入需要时间和技能。"],
            "学习": ["学习是个终身的过程。", "你想学什么？", "我之前也花了很多时间学习。"],
            "技能": ["技能越多越自由。", "你现在掌握哪些技能？", "我建议你学点实用的技能。"],
            "教育": ["教育改变命运。", "你是在考虑深造吗？", "现在学习渠道很多。"],
            "累了": ["累了吗？那休息一下吧。", "感觉累的时候要适当放松。", "我懂那种疲惫的感觉。"],
            "困": ["困了就早点睡吧。", "睡眠很重要，别熬夜。", "我也困了..."],
            "饿": ["说到吃的，我也有点饿了。", "饿了就去吃点东西吧。", "健康饮食很重要。"],
            "开心": ["开心就好！", "看到你开心我也很高兴。", "有什么开心事分享一下？"],
            "难过": ["别难过，一切都会好的。", "我在这里陪着你。", "需要我陪你聊聊吗？"]
        }

        for keyword, options in responses.items():
            if keyword in user_input:
                return random.choice(options)

        # 上下文感知默认回复
        if "?" in user_input or any(q in user_input for q in ["怎么", "如何", "为什么", "什么", "吗", "呢"]):
            question_responses = [
                "这是个好问题，让我想想...",
                "你问的这个问题挺有意思的。",
                "我不太确定，但我们可以一起探讨。",
                "这个问题需要具体情况分析。",
                "你期望的答案是什么？先说说你的想法吧。"
            ]
            return random.choice(question_responses)
        elif len(user_input) < 5:
            short_responses = {
                friendliness > 0.6: ["嗯嗯", "我在呢", "接着说", "好哒"],
                friendliness <= 0.6: ["嗯", "哦", "知道了"]
            }
            return random.choice(short_responses[True if friendliness > 0.6 else False])
        else:
            statement_responses = [
                "我明白了。",
                "原来如此。",
                "interesting...",
                "继续说，我在听。",
                "然后呢？"
            ]
            return random.choice(statement_responses)

    def _generate_deep_analysis(self, vh: SimPerson, user_input: str, friendliness: float, humor: float, seriousness: float) -> str:
        """生成深度分析回复（模拟多Agent协作）"""
        # 分析问题类型
        if "赚钱" in user_input or "钱" in user_input or "收入" in user_input or "财" in user_input:
            return self._analyze_money_question(vh, user_input, friendliness, seriousness)
        elif "工作" in user_input or "职业" in user_input or "找工作" in user_input:
            return self._analyze_career_question(vh, user_input, friendliness, seriousness)
        elif "学习" in user_input or "技能" in user_input or "教育" in user_input:
            return self._analyze_learning_question(vh, user_input, friendliness, seriousness)
        else:
            return self._analyze_general_question(vh, user_input, friendliness, seriousness)

    def _analyze_money_question(self, vh: SimPerson, user_input: str, friendliness: float, seriousness: float) -> str:
        """多角度分析赚钱问题"""
        # Planner: 制定框架
        planner_parts = [
            "📋 关于赚钱，我来帮你系统分析一下：",
            "1️⃣ **明确目标**: 你想达到什么收入水平？",
            "2️⃣ **盘点资源**: 你目前有什么技能、时间、资金？",
            "3️⃣ **探索路径**: 有哪些可能的收入来源？"
        ]

        # Critic: 挑刺与风险
        critic_parts = [
            "\n⚠️ **需要谨慎的方面**:",
            "• 不要盲目追求快钱，容易踩坑",
            "• 评估风险：时间投入 vs 预期回报",
            "• 警惕「轻松赚钱」的诱惑"
        ]

        # Feedback: 具体建议
        feedback_parts = [
            "\n✅ **行动建议**:",
            "• 从最小可行性方案开始试错",
            "• 投资自己最划算（学习技能）",
            "• 建立多元收入来源（三条腿走路）",
            "• 记录开销，优化支出结构"
        ]

        # Encourager: 情感支持
        if friendliness > 0.5:
            encourager_parts = [
                "\n💪 **加油！** 赚钱是个长期过程，",
                "重要的是开始行动并持续优化。",
                "我相信你能找到适合自己的路！"
            ]
        else:
            encourager_parts = [
                "\n总之，理性规划，稳步前进。"
            ]

        # Synthesizer: 整合输出
        synthesis = "".join(planner_parts + critic_parts + feedback_parts + encourager_parts)

        # 根据严肃度调整语气
        if seriousness > 0.7:
            synthesis = synthesis.replace("💪", "").replace("📋", "1.").replace("⚠️", "注意:").replace("✅", "建议:")

        return synthesis

    def _analyze_career_question(self, vh: SimPerson, user_input: str, friendliness: float, seriousness: float) -> str:
        """多角度分析职业问题"""
        planner = [
            "🎯 职业规划分析：",
            "• 自我认知：你的兴趣、性格、价值观是什么？",
            "• 市场调研：哪些行业有发展前景？",
            "• 能力匹配：你目前的能力与目标岗位差距？"
        ]

        critic = [
            "\n🔍 需要反思:",
            "• 不要只看薪资，要关注成长空间",
            "• 频繁跳槽可能影响履历稳定性",
            "• 工作是为了生活，别本末倒置"
        ]

        feedback = [
            "\n🚀 **具体步骤**:",
            "1. 做职业兴趣测试（如MBTI）了解自己",
            "2. 找3-5位目标行业从业者交流（信息访谈）",
            "3. 制定3个月能力提升计划",
            "4. 更新简历，开始投递或内推"
        ]

        if friendliness > 0.6:
            synthesis = "".join(planner + critic + feedback + ["\n🌟 你的职业生涯由你自己定义，"], ["慢慢来，不着急！"])
        else:
            synthesis = "".join(planner + critic + feedback + ["\n以上，需要根据实际情况调整。"])

        return synthesis

    def _analyze_learning_question(self, vh: SimPerson, user_input: str, friendliness: float, seriousness: float) -> str:
        """多角度分析学习问题"""
        planner = [
            "📚 学习计划建议：",
            "• 明确目标：学这个为了什么？",
            "• 拆解知识体系：需要哪些前置知识？",
            "• 实践导向：学完要用起来"
        ]

        critic = [
            "\n❌ 常见误区:",
            "• 不要只收藏不学习",
            "• 不要追求完美主义（完成比完美重要）",
            "• 不要孤立学习（要输出、要分享）"
        ]

        feedback = [
            "\n💡 **高效学习法**:",
            "1. **费曼技巧**：学完能教给别人才算真懂",
            "2. **番茄工作法**：25分钟专注+5分钟休息",
            "3. **项目驱动**：边做边学，用项目倒推学习",
            "4. **社区学习**：加入学习小组，互相监督"
        ]

        if humor > 0.6:
            synthesis = "".join(planner + critic + feedback + ["\n😄 学习就像刷经验，"])
        else:
            synthesis = "".join(planner + critic + feedback + ["\nKeep learning!"])

        return synthesis

    def _analyze_general_question(self, vh: SimPerson, user_input: str, friendliness: float, seriousness: float) -> str:
        """通用问题分析"""
        responses = [
            "让我从几个角度分析一下你的问题「{}」：\n\n".format(user_input[:20]),
            "1. 你目前的现状是什么？\n2. 你期望达到什么状态？\n3. 中间差距在哪里？\n4. 第一步可以做什么？\n\n",
            "📌 **我的建议**: 把大目标拆成小步骤，先完成第一步，然后迭代。"
        ]

        if friendliness > 0.6:
            responses.append("\n别担心，我们一步步来，我在呢！")

        return "".join(responses)

    def _mood_from_friendliness(self, friendliness: float) -> str:
        """根据友好度推断情绪"""
        if friendliness > 0.7:
            return random.choice(["happy", "excited"])
        elif friendliness < 0.4:
            return random.choice(["neutral", "serious"])
        else:
            return "neutral"

    def _api_generate(self, vh: SimPerson, user_input: str, stream_callback=None) -> Dict:
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
            "max_tokens": 500,
            "stream": stream_callback is not None  # 仅当需要流式时启用
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        try:
            if stream_callback:
                # 流式模式
                resp = requests.post(
                    self.endpoint,
                    json=payload,
                    headers=headers,
                    timeout=self.timeout,
                    stream=True
                )
                resp.raise_for_status()

                reply_parts = []
                for line in resp.iter_lines():
                    if not line:
                        continue
                    line = line.decode('utf-8', errors='ignore')
                    if line.startswith('data: '):
                        data_str = line[6:]  # 去掉 "data: " 前缀
                        if data_str == "[DONE]":
                            break
                        try:
                            data = json.loads(data_str)
                            delta = data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                            if delta:
                                reply_parts.append(delta)
                                stream_callback(delta)
                        except json.JSONDecodeError:
                            continue

                reply = "".join(reply_parts).strip()
                return {
                    "reply": reply,
                    "emotion": vh.state["mood"],
                    "energy_delta": -2
                }
            else:
                # 非流式模式（原有逻辑）
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
                    "emotion": vh.state["mood"],
                    "energy_delta": -2
                }
        except requests.RequestException as e:
            print(f"[APIClient] API调用失败: {e}")
            # 降级到Mock模式
            print("[APIClient] 降级到Mock回复")
            return self._mock_generate(vh, user_input, stream_callback)
        except Exception as e:
            print(f"[APIClient] 解析响应失败: {e}")
            return self._mock_generate(vh, user_input, stream_callback)