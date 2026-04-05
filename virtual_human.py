import time
import uuid
import random
from typing import List, Dict
from config import LIFE_STAGES, PROFESSIONS, DAY_ACTIONS_LIMIT, NATURAL_DECAY, XIAOHONGSHU_CONFIG

class SimPerson:
    """模拟人生角色（扩展自VirtualHuman）"""

    def __init__(self, name: str, personality: dict, vh_id: str = None, age: float = 18):
        # === 基础身份 ===
        self.id = vh_id
        self.name = name
        self.personality = personality
        self.created_at = time.time()

        # === 模拟人生属性 ===
        self.age = round(age, 1)  # 年龄，允许小数
        self.stage = self._get_stage_by_age(age)
        self.job = "待业" if age >= 18 else "学生"
        self.alive = True

        # 核心状态（0-100）
        self.health = 100      # 健康
        self.energy = 100      # 精力
        self.hunger = 60       # 饥饿（越高越饱）
        self.social = 50       # 社交需求满足度
        self.fun = 50          # 娱乐需求
        self.mood_value = 50   # 心情值（0-100）

        # 金钱系统
        self.money = 1000
        self.income = 0
        self.expense = 0

        # 情绪状态（文字描述）
        self.mood_level = "普通"  # 开心/普通/低落/生气/崩溃

        # 关系系统
        self.relationships = {}  # {other_vh_id: {"affection": 0, "trust": 0, "type": "neutral"}}

        # 游戏机制
        self.actions_today = 0   # 今日已行动次数
        self.day_counter = 0     # 天数计数
        self.death_cause = None  # 死亡原因
        self.is_player = False   # 是否为玩家控制角色

        # 对话记忆（继承）
        self.memory: List[Dict] = []

        # 聊天兼容性state字段（旧代码需要）
        self.state = {
            "energy": self.energy,
            "mood": self.mood_level,
            "relationship": 0
        }

        # === 使命引导者属性 ===
        self.is_mentor = False  # 是否为导师角色（教师/贵人）
        self.mentor_type = self._assign_mentor_type()  # 导师类型（如果is_mentor=True才有效）
        self.guidance_style = self._determine_guidance_style()  # 引导风格
        self.guidance_goal = "帮助玩家找到人生使命"  # 所有虚拟人的共同目标
        self.relationship_with_player = 50  # 与玩家的关系度 (0-100)
        self.last_guidance_topic = None  # 上次引导话题
        self.discovered_player_interests: List[str] = []  # 发现的玩家兴趣
        self.mentor_trigger_count = 0  # 主动触发次数

        # === Multi-Agent 协作系统 ===
        self.multi_agent_system = None  # 延迟初始化，在首次引导时创建
        self.use_multi_agent = True  # 是否启用多Agent协作

        # 根据初始职业确定是否为导师
        self._update_mentor_status_from_job()

        # === 小红书博主专用属性 ===
        # 只有当职业是"小红书博主"时才激活
        self.xiaohongshu = {
            "followers": XIAOHONGSHU_CONFIG["base_followers"],  # 初始粉丝数
            "total_views": 0,        # 总阅读量
            "total_likes": 0,        # 总点赞
            "total_collections": 0,  # 总收藏
            "total_comments": 0,     # 总评论
            "engagement_rate": 0.0,  # 互动率（点赞+收藏+评论）/阅读量
            "posts_published": 0,    # 已发布笔记数
            "hot_posts": 0,          # 爆款笔记数（阅读>1万）
            "last_post_date": None,  # 最后发布时间
            "monetization_level": 0  # 变现等级（0-5）
        }

    # ========== 使命引导者系统 ==========
    def _assign_mentor_type(self) -> str:
        """根据性格分配导师类型"""
        f = self.personality.get("friendliness", 0.5)
        h = self.personality.get("humor", 0.5)
        s = self.personality.get("seriousness", 0.5)

        if h > 0.7:
            return "创意激发者"  # 幽默型：激发创意和乐趣
        elif s > 0.7:
            return "目标规划师"  # 严肃型：目标设定和执行力
        elif f > 0.7:
            return "情感支持者"  # 友好型：情感支持和倾听
        else:
            return "平衡引导者"  # 中立型：全面平衡

    def _determine_guidance_style(self) -> str:
        """确定引导风格"""
        styles = {
            "创意激发者": "通过创意活动和趣味挑战引导",
            "目标规划师": "通过结构化任务和目标分解引导",
            "情感支持者": "通过深度对话和情感共鸣引导",
            "平衡引导者": "根据情况灵活调整引导方式"
        }
        return styles.get(self.mentor_type, "灵活引导")

    def generate_mission_guidance(self, player_input: str, player_growth: 'PlayerGrowth') -> Dict:
        """
        生成使命引导对话和任务
        返回包含回复和可能的引导任务的结构化数据
        """
        # 基于性格和导师类型生成引导内容
        context = self._build_guidance_context(player_input, player_growth)

        # 根据当前玩家状态决定引导策略
        strategy = self._choose_guidance_strategy(player_growth)

        # 生成引导回复
        reply = self._craft_guidance_reply(context, strategy, player_growth)

        # 记录引导历史
        if player_growth:
            player_growth.record_guidance(self.name, "dialogue", reply)

        return {
            "reply": reply,
            "guidance_type": strategy["type"],
            "suggested_action": strategy.get("action"),
            "topic": strategy["topic"]
        }

    def _build_guidance_context(self, player_input: str, player_growth: 'PlayerGrowth') -> str:
        """构建引导上下文"""
        context_parts = [
            f"你是{self.name}，一个{self.age:.0f}岁的{self._translate_stage(self.stage)}，职业是{self.job}",
            f"你的性格：友好度{self.personality.get('friendliness', 0.5):.1f}, 幽默度{self.personality.get('humor', 0.5):.1f}, 严肃度{self.personality.get('seriousness', 0.5):.1f}",
            f"你的导师类型：{self.mentor_type}",
            f"你的目标：帮助玩家（玩家）找到人生使命",
        ]

        if player_growth:
            summary = player_growth.get_growth_summary()
            context_parts.append(f"\n玩家当前状态:")
            context_parts.append(f"  - 已发现兴趣: {', '.join(summary['discovered_interests']) if summary['discovered_interests'] else '无'}")
            context_parts.append(f"  - 使命状态: {summary['current_status']}")
            if summary['life_mission']:
                context_parts.append(f"  - 已确认使命: {summary['life_mission']}")
            context_parts.append(f"  - 完成的挑战: {summary['challenges_completed']}个")
            context_parts.append(f"  - 收到的引导: {summary['total_guidance_sessions']}次")

        context_parts.append(f"\n玩家刚才说: {player_input}")

        return "\n".join(context_parts)

    def _choose_guidance_strategy(self, player_growth: 'PlayerGrowth') -> Dict:
        """选择合适的引导策略"""
        # 基于玩家成长阶段选择策略
        if not player_growth or not player_growth.discovered_interests:
            # 阶段1：兴趣探索
            return {
                "type": "explore_interest",
                "topic": "探索兴趣",
                "action": "建议尝试新的活动",
                "question_type": "open_ended"
            }
        elif not player_growth.confirmed_life_mission and player_growth.challenges_completed < 5:
            # 阶段2：技能发展和挑战
            top_interest = player_growth.discovered_interests[0] if player_growth.discovered_interests else "通用技能"
            return {
                "type": "skill_building",
                "topic": top_interest,
                "action": f"提供关于{top_interest}的小挑战",
                "question_type": "challenge"
            }
        elif player_growth.mission_clues and not player_growth.confirmed_life_mission:
            # 阶段3：使命线索整合
            return {
                "type": "mission_synthesis",
                "topic": "整合使命线索",
                "action": "引导玩家思考线索之间的联系",
                "question_type": "reflective"
            }
        else:
            # 阶段4：使命确认或后续成长
            return {
                "type": "mission_confirmation",
                "topic": "确认人生使命",
                "action": "鼓励玩家明确表达使命",
                "question_type": "direct"
            }

    def _craft_guidance_reply(self, context: str, strategy: Dict, player_growth: 'PlayerGrowth') -> str:
        """ Craft 引导式回复"""
        # 基于导师类型和策略生成回复
        mentor_phrases = {
            "创意激发者": [
                "探索无限可能...",
                "让我帮你打开新世界的大门！",
                "今天我们来点有趣的东西！"
            ],
            "目标规划师": [
                "让我们制定一个清晰的计划。",
                "目标分解是成功的关键。",
                "我会帮你一步步实现。"
            ],
            "情感支持者": [
                "我理解你的感受。",
                "你可以和我分享任何想法。",
                "你的内心声音很重要。"
            ],
            "平衡引导者": [
                "让我们综合考虑各方面。",
                "平衡发展是个好主意。",
                "我会给你全面的建议。"
            ]
        }

        opener = random.choice(mentor_phrases.get(self.mentor_type, ["你好！"]))

        # 根据策略类型构建回复
        if strategy["type"] == "explore_interest":
            reply = f"{opener}\n\n我想了解你的兴趣。你平时喜欢做什么？有什么事情让你废寝忘食吗？\n\n探索不同的领域是很重要的第一步。"
        elif strategy["type"] == "skill_building":
            topic = strategy["topic"]
            reply = f"{opener}\n\n我发现你对{topic}感兴趣。我有个小挑战给你：\n\n尝试深入{topic}的某个方面，花30分钟学习或实践，然后告诉我你的感受。\n\n愿意接受吗？"
        elif strategy["type"] == "mission_synthesis":
            clues = player_growth.mission_clues[-3:] if player_growth.mission_clues else []
            reply = f"{opener}\n\n我注意到你收集了一些线索：\n"
            for i, clue in enumerate(clues, 1):
                reply += f"  {i}. {clue['clue']}\n"
            reply += f"\n这些线索之间有联系吗？你觉得它们指向什么共同的方向？"
        elif strategy["type"] == "mission_confirmation":
            if player_growth.confirmed_life_mission:
                reply = f"{opener}\n\n你之前提到的人生使命是：{player_growth.confirmed_life_mission}\n\n现在你对这个使命有什么更深的体会吗？或者有新的发现？"
            else:
                reply = f"{opener}\n\n经过这么久的探索，你是否感觉找到了什么特别想做的事情？\n\n试着用一句话描述你的人生使命，我们可以一起完善它。"
        else:
            reply = f"{opener}\n\n让我们聊聊你的成长吧。"

        # 添加性格修饰
        if self.personality.get("humor", 0) > 0.6:
            reply += "\n（放松点，这应该是个有趣的过程！）"
        if self.personality.get("seriousness", 0) > 0.7:
            reply += "\n请认真思考后再回答。"

        return reply

    def guide_player_growth(self, message: str, player_growth: 'PlayerGrowth') -> str:
        """
        对外接口：引导玩家成长
        返回回复消息（可能包含任务建议）

        如果启用 multi_agent，则使用多Agent协作生成回复
        否则使用单Agent基础模式
        """
        if self.use_multi_agent:
            # 延迟初始化多Agent系统（避免循环导入）
            if self.multi_agent_system is None:
                try:
                    from multi_agent_guidance import MultiAgentGuidanceSystem
                    self.multi_agent_system = MultiAgentGuidanceSystem(self)
                except ImportError:
                    self.use_multi_agent = False
                    print(f"[{self.name}] Multi-Agent模块未找到，降级到单Agent模式")

            if self.use_multi_agent and self.multi_agent_system:
                # 多Agent协作生成
                result = self.multi_agent_system.collaborative_guidance(message, player_growth)
                return result["final_reply"]

        # 降级：单Agent基础模式
        guidance = self.generate_mission_guidance(message, player_growth)
        return guidance["reply"]


    # ========== 角色职业状态同步 ==========
    def _update_mentor_status_from_job(self):
        """根据职业更新是否为导师"""
        mentor_jobs = ["教师", "贵人"]
        self.is_mentor = self.job in mentor_jobs
        if self.is_mentor:
            self.mentor_type = self._assign_mentor_type()
            self.guidance_style = self._determine_guidance_style()
            # 导师初始关系度更高
            self.relationship_with_player = max(self.relationship_with_player, 60)

    # ========== 模拟人生核心系统 ==========
    def _get_stage_by_age(self, age: float) -> str:
        """根据年龄获取人生阶段"""
        for stage, config in LIFE_STAGES.items():
            if config["min_age"] <= age < config["max_age"]:
                return stage
        return "senior"  # 默认老年

    def update_mood(self):
        """根据状态更新情绪"""
        # 基于health, hunger, energy, social, fun综合计算
        factors = [
            self.health / 20,      # 健康影响大
            self.hunger / 50,
            self.energy / 30,
            self.social / 40,
            self.fun / 40
        ]
        avg = sum(factors) / len(factors)

        if avg >= 0.8:
            self.mood_level = "开心"
        elif avg >= 0.6:
            self.mood_level = "普通"
        elif avg >= 0.4:
            self.mood_level = "低落"
        elif avg >= 0.2:
            self.mood_level = "生气"
        else:
            self.mood_level = "崩溃"

        self.state["mood"] = self.mood_level
        return self.mood_level

    def eat(self):
        """吃饭行动"""
        cost = 30
        if self.money >= cost:
            self.hunger = min(100, self.hunger + 40)
            self.energy = max(0, self.energy - 5)  # 吃饭不影响精力或轻微降低
            self.money -= cost
            self.expense += cost
            self.actions_today += 1
            # day_counter 由 day_pass 统一增加
            return f"吃了顿饭，花费${cost}，饥饿感下降"
        else:
            return "钱不够吃饭！"

    def sleep(self):
        """睡觉行动"""
        self.energy = min(100, self.energy + 60)
        self.health += 5
        self.actions_today += 1
        # day_counter 由 day_pass 统一增加
        return "睡了一觉，精神恢复了"

    def work(self):
        """工作行动"""
        if not self.job or self.job == "待业":
            return "你没有工作！先找份工作吧。"

        # 计算收入（基于职业）
        base_salary = {
            "上班族": 150, "程序员": 200, "主播": 300,
            "画家": 250, "外卖员": 100, "教师": 140,
            "医生": 400, "律师": 500, "工程师": 220,
            "自由职业": 180
        }.get(self.job, 100)

        # 精力影响效率
        efficiency = max(0.2, self.energy / 100)  # 最低20%效率
        earnings = int(base_salary * efficiency * random.uniform(0.8, 1.2))

        self.money += earnings
        self.income += earnings
        self.energy -= 30
        self.hunger -= 20
        self.fun -= 15
        # age/day_counter 增长在 day_pass 统一处理
        self.actions_today += 1

        # 工作可能触发升职事件
        if random.random() < 0.1:
            return f"工作完成，赚了${earnings}！感觉很有成就感！"
        return f"工作完成，赚了${earnings}"

    def find_job(self):
        """找工作/换工作"""
        new_job = random.choice(PROFESSIONS)
        salary_hints = {
            "上班族": "普通白领", "程序员": "高收入", "主播": "不稳定但可能很高",
            "画家": "艺术人生", "外卖员": "多劳多得", "教师": "稳定",
            "医生": "高薪高压", "律师": "高收入", "工程师": "技术活",
            "自由职业": "时间自由"
        }
        hint = salary_hints.get(new_job, "新工作")
        self.job = new_job
        self._update_mentor_status_from_job()  # 更新导师状态
        self.actions_today += 1
        # day_counter 由 day_pass 处理
        return f"恭喜！你找到了新工作：{new_job}（{hint}）"

    def relax(self):
        """娱乐放松"""
        self.fun = min(100, self.fun + 30)
        self.mood_value += 15
        self.energy -= 10
        self.actions_today += 1
        # day_counter 由 day_pass 处理
        return "娱乐放松了一，心情变好了"

    def socialize(self, target_name: str = None):
        """社交活动"""
        self.social = min(100, self.social + 25)
        self.mood_value += 10
        self.energy -= 10
        self.actions_today += 1
        # day_counter 由 day_pass 处理

        target = f"与{target_name}" if target_name else ""
        return f"和{target_name}聊了，社交需求得到满足"

    def shop(self):
        """购物"""
        cost = random.randint(50, 200)
        if self.money >= cost:
            self.money -= cost
            self.expense += cost
            self.fun += 20
            self.actions_today += 1
            # day_counter 由 day_pass 处理
            return f"逛街购物花费${cost}，心情变好了"
        else:
            return "钱不够购物！"

    def create_xiaohongshu_post(self, title=None, content=None, tags=None, images=None):
        """
        创建并发布小红书笔记

        如果启用了官方API（XIAOHONGSHU_CONFIG["api_enabled"]=True），则调用真实API；
        否则使用模拟模式生成假数据。
        """
        if self.job != "小红书博主":
            return "只有小红书博主才能发布笔记哦！"

        # 生成标题和内容（如果未提供）
        if not title or not content:
            generated = self._generate_xiaohongshu_content()
            title = title or generated.get("title", "我的日常")
            content = content or generated.get("content", "今天很开心！")
            tags = tags or generated.get("tags", ["日常"])

        # 限制标签数量
        if tags and len(tags) > XIAOHONGSHU_CONFIG["max_tags"]:
            tags = tags[:XIAOHONGSHU_CONFIG["max_tags"]]

        # 限制标题和内容长度
        title = title[:XIAOHONGSHU_CONFIG["max_title_length"]]
        content = content[:XIAOHONGSHU_CONFIG["max_content_length"]]

        # 检查是否启用官方API
        if XIAOHONGSHU_CONFIG.get("api_enabled", False):
            try:
                from xhs_api import get_xhs_client
                client = get_xhs_client()
                if client.enabled:
                    return self._publish_via_official_api(title, content, images, tags)
                else:
                    print("[XHS] API未配置，降级到模拟模式")
                    return self._publish_simulated(title, content, tags)
            except Exception as e:
                print(f"[XHS] API调用异常: {e}，降级到模拟模式")
                return self._publish_simulated(title, content, tags)
        else:
            return self._publish_simulated(title, content, tags)

    def _publish_via_official_api(self, title: str, content: str, images: list, tags: list) -> str:
        """通过小红书官方API发布"""
        try:
            from xhs_api import get_xhs_client
            client = get_xhs_client()

            if not client.enabled:
                return "[警告] 小红书API未配置，切换为模拟模式\n" + self._publish_simulated(title, content, tags)

            # 调用发布接口
            result = client.publish_note(
                title=title,
                content=content,
                images=images,
                tags=tags
            )

            if result.get('success'):
                note_id = result.get('note_id', 'unknown')
                note_url = result.get('url', '')

                # 本地统计数据（由于API调用后需异步产生数据，这里暂不更新）
                self.xiaohongshu["posts_published"] += 1
                self.xiaohongshu["last_post_date"] = time.time()
                self.actions_today += 1
                self.fun = min(100, self.fun + 20)
                self.mood_value += 10

                msg = f"""小红书笔记已发布（官方API）！
标题：{title}
标签：{', '.join(tags)}
Note ID: {note_id}
链接：{note_url if note_url else '暂无'}
粉丝：{self.xiaohongshu['followers']}人"""
                return msg
            else:
                return f"小红书API发布失败: {result.get('error', 'Unknown error')}"

        except ImportError:
            return "[错误] xhs_api模块未找到，请确保xhs_api.py存在"
        except Exception as e:
            return f"[错误] 小红书API调用异常: {str(e)}"

    def _publish_simulated(self, title: str, content: str, tags: list) -> str:
        """模拟小红书发布（本地计算统计数据）"""
        # 计算本次发布效果
        is_hot = random.random() < XIAOHONGSHU_CONFIG["hot_probability"]

        # 基础阅读量：粉丝数 * 曝光系数（0.1-0.3）
        base_views = int(self.xiaohongshu["followers"] * random.uniform(0.1, 0.3))
        if is_hot:
            base_views *= random.uniform(5, 15)  # 爆款10-50倍曝光
            self.xiaohongshu["hot_posts"] += 1

        views = int(base_views)
        likes = int(views * XIAOHONGSHU_CONFIG["base_engagement_rate"] * random.uniform(0.8, 1.5))
        collections = int(likes * random.uniform(0.2, 0.5))
        comments = int(views * random.uniform(0.01, 0.05))

        # 更新累计数据
        self.xiaohongshu["total_views"] += views
        self.xiaohongshu["total_likes"] += likes
        self.xiaohongshu["total_collections"] += collections
        self.xiaohongshu["total_comments"] += comments
        self.xiaohongshu["posts_published"] += 1
        self.xiaohongshu["last_post_date"] = time.time()

        # 更新粉丝数（优质内容涨粉）
        if is_hot or views > self.xiaohongshu["followers"] * 0.5:
            new_followers = int(views * 0.01 * random.uniform(0.5, 2.0))
            self.xiaohongshu["followers"] += new_followers
        else:
            # 普通内容可能掉粉
            lost_followers = random.randint(0, max(0, int(self.xiaohongshu["followers"] * 0.001)))
            self.xiaohongshu["followers"] = max(0, self.xiaohongshu["followers"] - lost_followers)

        # 计算互动率
        if views > 0:
            engagement = (likes + collections + comments) / views
            self.xiaohongshu["engagement_rate"] = engagement

        # 计算本次收入
        income = int(views / 1000 * XIAOHONGSHU_CONFIG["income_per_1000_views"])
        self.money += income
        self.income += income

        # 更新状态
        self.actions_today += 1
        self.fun = min(100, self.fun + 20)  # 创作带来乐趣
        self.mood_value += 10

        # 构建返回消息
        hot_text = "[爆款]" if is_hot else ""
        result_msg = f"""小红书笔记已发布！
标题：{title}
标签：{', '.join(tags)}
效果：{views}阅读, {likes}点赞, {collections}收藏, {comments}评论 {hot_text}
收益：+${income}
粉丝：{self.xiaohongshu['followers']}人"""
        return result_msg

    def _generate_xiaohongshu_content(self):
        """使用Claude Code生成小红书内容（如果API可用）"""
        try:
            from api_client import APIClient
            api_client = APIClient()

            prompt = f"""
你是{self.name}，一个{self.age:.1f}岁的{self._translate_stage(self.stage)}，职业是{self.job}。
性格：{self.personality}

请为小红书写一篇笔记，要求：
1. 标题吸引人（ emoji开头，简洁有力）
2. 正文用 emoji分隔，轻松愉快
3. 包含3-5个热门标签（如 #日常 #好物推荐）
4. 字数300-500字
5. 符合你的性格设定

只输出JSON格式：
{{"title": "...", "content": "...", "tags": ["...", "..."]}}
"""
            # 注意：这里需要调用API生成，但当前APIClient是针对对话的
            # 简化处理：返回默认模板
            pass
        except:
            pass

        # 降级：根据性格返回预设模板
        templates = [
            {
                "title": "今天也是元气满满的一天！",
                "content": "早上起来做了瑜伽，感觉整个人都清醒了～推荐大家试试！ 中午去了一家超棒的咖啡馆，拿铁非常好喝 晚上和闺蜜聚会，聊了好多有趣的事 今天又是充实的一天！",
                "tags": ["日常", "瑜伽", "咖啡", "闺蜜聚会"]
            },
            {
                "title": "分享我的工作效率小技巧",
                "content": "最近发现了一个超级好用的时间管理方法！番茄工作法真的提高了我的专注度 设定25分钟专注+5分钟休息，一上午能完成好多任务 推荐给大家～ #工作效率 #时间管理",
                "tags": ["工作效率", "时间管理", "自律", "干货分享"]
            },
            {
                "title": "周末探店：发现一家神仙小店",
                "content": "今天偶然走进了一家隐藏在巷子里的小店，环境超级nice！ 装饰很有艺术感，适合拍照打卡 点了一杯特调，味道独特～强烈推荐大家来试试！#探店 #小众店铺",
                "tags": ["探店", "小众店铺", "拍照打卡", "美食"]
            }
        ]
        return random.choice(templates)

    def day_pass(self):
        """结束一天，触发自然衰减和随机事件"""
        # 自然衰减
        for attr, decay in NATURAL_DECAY.items():
            current = getattr(self, attr)
            setattr(self, attr, max(0, min(100, current + decay)))

        # 年龄增长：根据行动次数计算
        # 每次行动平均消耗0.2天，假设每天最多3次行动，则每天增长约0.6岁
        if self.actions_today > 0:
            age_increase = 0.1 + (self.actions_today * 0.1)  # 基础0.1 + 每次行动0.1
            self.age += age_increase
            print(f"  [时间] 经过{self.actions_today}次行动，年龄增长{age_increase:.2f}岁")

        self.actions_today = 0
        self.day_counter += 1

        # 检查死亡（永生模式下通常不触发）
        if self.check_death():
            return "你病逝了..."

        # 随机事件（30%概率）
        if random.random() < 0.3:
            return self.random_event()

        # 更新人生阶段
        self.stage = self._get_stage_by_age(self.age)

        return "新的一天开始了..."

    def random_event(self):
        """随机事件系统"""
        events = [
            ("感冒了，健康下降", lambda: self._change_health(-20), 0.15),
            ("捡到钱了！", lambda: self._change_money(100), 0.1),
            ("和朋友吵架了", lambda: self._change_mood(-30), 0.12),
            ("升职加薪", lambda: self._change_money(500), 0.08),
            ("中了小彩票", lambda: self._change_money(1000), 0.03),
            ("投资失败", lambda: self._change_money(-300), 0.08),
            ("遇到真爱", lambda: None, 0.05),  # 占位，后续扩展
            ("身体检查发现小问题", lambda: self._change_health(-10), 0.1),
            ("心情豁然开朗", lambda: self._change_mood(30), 0.09),
            ("没什么特别", lambda: None, 0.1)
        ]

        # 加权随机
        total_weight = sum(e[2] for e in events)
        r = random.random() * total_weight
        cumulative = 0
        for msg, func, weight in events:
            cumulative += weight
            if r <= cumulative:
                result_msg = f"随机事件：{msg}"
                if func:
                    func()
                return result_msg
        return "平凡的一天过去了"

    def _change_health(self, delta):
        self.health = max(0, min(100, self.health + delta))

    def _change_money(self, delta):
        self.money += delta
        if delta > 0:
            self.income += delta
        else:
            self.expense += abs(delta)

    def _change_mood(self, delta):
        self.mood_value = max(0, min(100, self.mood_value + delta))

    def check_death(self) -> bool:
        """检查是否死亡（灵魂永生模式：永不死亡）"""
        # 永生模式：不设置死亡
        # 若想恢复死亡，取消下面两行的注释
        # if self.health <= 0:
        #     self.alive = False
        #     self.death_cause = "病逝"
        #     return True
        # if self.age >= 100:
        #     self.alive = False
        #     self.death_cause = "寿终正寝"
        #     return True
        return False

    def get_status_full(self):
        """获取完整状态文本（用于显示）"""
        lines = [
            f"=== {self.name} 的人生状态 ===",
            f"年龄: {self.age:.1f}岁 | 阶段: {self._translate_stage(self.stage)} | 职业: {self.job}",
            f"健康: {self.health}/100 | 精力: {self.energy}/100 | 心情: {self.mood_level}",
            f"饥饿: {self.hunger}/100 ({'饱' if self.hunger>70 else '饿'})",
            f"社交: {self.social}/100 | 娱乐: {self.fun}/100",
            f"金钱: ${self.money} (今日收入: ${self.income}, 支出: ${self.expense})",
            f"今日行动: {self.actions_today}/{DAY_ACTIONS_LIMIT}",
            f"存活: {'是' if self.alive else '否'}"
        ]
        if not self.alive:
            lines.append(f"死亡原因: {self.death_cause}")
        return "\n".join(lines)

    def _translate_stage(self, stage_key: str) -> str:
        """人生阶段中文翻译"""
        translations = {
            "baby": "婴儿", "toddler": "幼儿", "child": "儿童",
            "teen": "青少年", "young_adult": "青年", "adult": "成年",
            "middle_age": "中年", "senior": "老年"
        }
        return translations.get(stage_key, stage_key)

    # ========== 聊天兼容方法（继承自VirtualHuman） ==========
    def add_memory(self, role: str, content: str):
        """添加对话记忆（保持兼容）"""
        memory_item = {
            "role": role,
            "content": content,
            "timestamp": time.time()
        }
        self.memory.append(memory_item)
        if len(self.memory) > 100:
            self.memory = self.memory[-100:]

    def get_context(self, last_n: int = 10) -> List[Dict]:
        return self.memory[-last_n:] if self.memory else []

    def to_dict(self) -> dict:
        """序列化（包含模拟人生数据和导师属性）"""
        data = {
            "id": self.id,
            "name": self.name,
            "personality": self.personality,
            "memory": self.memory,
            "state": self.state,
            "created_at": self.created_at,
            # 模拟人生数据
            "sim": {
                "age": self.age,
                "stage": self.stage,
                "job": self.job,
                "money": self.money,
                "energy": self.energy,
                "health": self.health,
                "hunger": self.hunger,
                "social": self.social,
                "fun": self.fun,
                "mood_value": self.mood_value,
                "mood_level": self.mood_level,
                "relationships": self.relationships,
                "alive": self.alive,
                "day_counter": self.day_counter,
                "actions_today": self.actions_today
            },
            # 导师系统属性
            "is_mentor": getattr(self, 'is_mentor', False),
            "mentor_type": getattr(self, 'mentor_type', '平衡引导者'),
            "relationship_with_player": getattr(self, 'relationship_with_player', 50),
            "discovered_player_interests": getattr(self, 'discovered_player_interests', []),
        }
        return data

    @classmethod
    def from_dict(cls, data: dict) -> 'SimPerson':
        """从字典反序列化"""
        vh = cls(
            name=data["name"],
            personality=data["personality"],
            vh_id=data.get("id"),
            age=data.get("sim", {}).get("age", 18)
        )
        vh.memory = data.get("memory", [])
        vh.created_at = data.get("created_at", time.time())

        # 加载模拟人生数据
        sim_data = data.get("sim", {})
        vh.age = sim_data.get("age", 18)
        vh.stage = sim_data.get("stage", vh._get_stage_by_age(vh.age))
        vh.job = sim_data.get("job", "待业")
        vh.money = sim_data.get("money", 1000)
        vh.energy = sim_data.get("energy", 100)
        vh.health = sim_data.get("health", 100)
        vh.hunger = sim_data.get("hunger", 60)
        vh.social = sim_data.get("social", 50)
        vh.fun = sim_data.get("fun", 50)
        vh.mood_value = sim_data.get("mood_value", 50)
        vh.mood_level = sim_data.get("mood_level", "普通")
        vh.relationships = sim_data.get("relationships", {})
        vh.alive = sim_data.get("alive", True)
        vh.day_counter = sim_data.get("day_counter", 0)
        vh.actions_today = sim_data.get("actions_today", 0)
        vh.income = sim_data.get("income", 0)  # 也可能需要
        vh.expense = sim_data.get("expense", 0)

        # 聊天兼容状态
        vh.state = {
            "energy": vh.energy,
            "mood": vh.mood_level,
            "relationship": 0
        }

        # 加载导师系统属性
        vh.is_mentor = data.get("is_mentor", False)
        vh.mentor_type = data.get("mentor_type", "平衡引导者")
        vh.relationship_with_player = data.get("relationship_with_player", 50)
        vh.discovered_player_interests = data.get("discovered_player_interests", [])
        if not hasattr(vh, 'mentor_trigger_count'):
            vh.mentor_trigger_count = 0
        # 初始化 multi_agent_system
        vh.multi_agent_system = None
        vh.use_multi_agent = True

        # 如果职业是教师/贵人，自动标记为导师
        vh._update_mentor_status_from_job()

        return vh

    def update_state_after_chat(self, user_input: str, api_response: dict):
        """根据对话更新状态（保持与旧代码兼容）"""
        # 能量消耗
        energy_delta = api_response.get("energy_delta", -2)
        self.energy = max(0, min(100, self.energy + energy_delta))
        self.state["energy"] = self.energy

        # 情绪更新（简化）
        if "emotion" in api_response:
            self.mood_level = api_response["emotion"]
            self.state["mood"] = self.mood_level

        # 关系度（虚拟人之间的好感度暂不实现）
        pass

    def get_status_text(self) -> str:
        """获取简状态（用于显示）"""
        return f"能量: {self.energy}/100 | 情绪: {self.mood_level} | 金钱: ${self.money}"

    def get_context(self, last_n: int = 10) -> List[Dict]:
        """获取最近N条对话作为上下文"""
        return self.memory[-last_n:] if self.memory else []

    # ========== 关系系统 ==========
    def update_relationship_with_player(self, delta: float, reason: str = None):
        """更新与玩家的关系度"""
        old_value = self.relationship_with_player
        self.relationship_with_player = max(0, min(100, self.relationship_with_player + delta))
        # 记录关系变化（可用于分析）
        if reason:
            pass  # TODO: 可选记录关系变化历史
        return self.relationship_with_player - old_value

    def update_relationship_with_other_vh(self, other_id: str, delta: float, reason: str = None):
        """更新与其他虚拟人的关系度"""
        if other_id not in self.relationships:
            self.relationships[other_id] = {"affection": 50, "trust": 50, "type": "neutral"}

        rel = self.relationships[other_id]
        old_aff = rel["affection"]
        rel["affection"] = max(0, min(100, rel["affection"] + delta))

        # 信任度变化（只有正向互动才提升信任）
        if delta > 0:
            rel["trust"] = min(100, rel["trust"] + delta * 0.5)

        # 关系类型标签
        if rel["affection"] >= 80:
            rel["type"] = "亲密"
        elif rel["affection"] >= 60:
            rel["type"] = "友好"
        elif rel["affection"] >= 40:
            rel["type"] = "中立"
        elif rel["affection"] >= 20:
            rel["type"] = "疏远"
        else:
            rel["type"] = "敌对"

        return self.relationships[other_id]

    def get_relationship_with_player(self) -> int:
        """获取与玩家的关系度"""
        return self.relationship_with_player

    def get_relationship_with_other(self, other_id: str) -> Dict:
        """获取与其他虚拟人的关系详情"""
        return self.relationships.get(other_id, {"affection": 50, "trust": 50, "type": "陌生"})
