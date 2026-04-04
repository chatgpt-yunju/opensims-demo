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
        """序列化（包含模拟人生数据）"""
        return {
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
            }
        }

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
        return vh

    # ========== 聊天兼容方法 ==========
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

    def add_memory(self, role: str, content: str):
        """添加对话记忆"""
        memory_item = {
            "role": role,
            "content": content,
            "timestamp": time.time()
        }
        self.memory.append(memory_item)

        # 限制记忆长度，防止过大
        if len(self.memory) > 100:
            self.memory = self.memory[-100:]

    def update_state_after_chat(self, user_input: str, api_response: dict):
        """根据对话更新状态"""
        # 能量消耗（每条对话-1到-3）
        energy_delta = api_response.get("energy_delta", -2)
        self.state["energy"] = max(0, min(100, self.state["energy"] + energy_delta))

        # 情绪更新
        if "emotion" in api_response:
            self.state["mood"] = api_response["emotion"]

        # 关系度提升（如果是友好对话）
        if self.state["energy"] > 50:
            self.state["relationship"] = min(100, self.state["relationship"] + 1)

    def get_context(self, last_n: int = 10) -> List[Dict]:
        """获取最近N条对话作为上下文"""
        return self.memory[-last_n:] if self.memory else []

    def get_status_text(self) -> str:
        """获取状态文本（用于显示）"""
        return f"能量: {self.state['energy']}/100 | 情绪: {self.state['mood']} | 关系: {self.state['relationship']}/100"

    def to_dict(self) -> dict:
        """序列化为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "personality": self.personality,
            "memory": self.memory,
            "state": self.state,
            "created_at": self.created_at
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'VirtualHuman':
        """从字典反序列化"""
        vh = cls(data["name"], data["personality"], vh_id=data.get("id"))
        vh.memory = data.get("memory", [])
        vh.state = data.get("state", {
            "energy": 100,
            "mood": "neutral",
            "relationship": 0
        })
        vh.created_at = data.get("created_at", time.time())
        return vh