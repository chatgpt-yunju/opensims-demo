# OpenSims Demo Configuration

# API配置
API_ENDPOINT = "https://api.yunjunet.cn/v1/chat/completions"  # OpenAI兼容端点
API_KEY = ""  # 从环境变量读取：os.getenv("OPENSIMS_API_KEY")
API_TIMEOUT = 30  # 秒
API_MODEL = "step-3.5-flash"  # 云君网络模型

# 是否使用Mock模式（如果没有API，设为True）
USE_MOCK = False  # 使用真实API（需要配置API_KEY）

# 性格预设
PERSONALITY_PRESETS = {
    "温柔型": {"friendliness": 0.9, "humor": 0.3, "seriousness": 0.2},
    "幽默型": {"friendliness": 0.7, "humor": 0.9, "seriousness": 0.1},
    "严肃型": {"friendliness": 0.4, "humor": 0.1, "seriousness": 0.9},
    "中立型": {"friendliness": 0.5, "humor": 0.5, "seriousness": 0.5}
}

# 数据文件路径
DATA_FILE = "demo_data.json"

# ===== 新增：多虚拟人与自动聊天设置 =====
# 是否启用自动聊天（虚拟人之间自动对话）
AUTO_CHAT_ENABLED = False  # 默认关闭，需要手动开启
AUTO_CHAT_INTERVAL = 30    # 自动对话间隔（秒）
AUTO_CHAT_PROBABILITY = 0.3  # 每次心跳触发对话的概率（0-1）

# 最大虚拟人数量（防止资源耗尽）
MAX_VIRTUAL_HUMANS = 10

# ===== 模拟人生游戏系统配置 =====
# 自动聊天开关（灵魂永生模式）
AUTO_CHAT_ENABLED = True   # 开启自动聊天（虚拟人之间自主对话）
AUTO_CHAT_INTERVAL = 30    # 自动对话检查间隔（秒）
AUTO_CHAT_PROBABILITY = 0.5  # 每次检查触发对话的概率（0-1）

# 人生阶段定义（按年龄）
LIFE_STAGES = {
    "baby": {"min_age": 0, "max_age": 3, "default_job": "婴儿"},
    "toddler": {"min_age": 3, "max_age": 6, "default_job": "幼儿"},
    "child": {"min_age": 6, "max_age": 12, "default_job": "学生"},
    "teen": {"min_age": 12, "max_age": 18, "default_job": "学生"},
    "young_adult": {"min_age": 18, "max_age": 25, "default_job": "待业"},
    "adult": {"min_age": 25, "max_age": 40, "default_job": "上班族"},
    "middle_age": {"min_age": 40, "max_age": 60, "default_job": "资深员工"},
    "senior": {"min_age": 60, "max_age": 100, "default_job": "退休"}
}

# 职业列表
PROFESSIONS = [
    "上班族", "程序员", "主播", "画家", "外卖员",
    "教师", "医生", "律师", "工程师", "自由职业",
    "小红书博主",  # 新增：内容创作者
    "贵人"  # 新增：人生导师型职业
]

# 游戏参数
DAY_ACTIONS_LIMIT = 999      # 每天行动次数限制（灵魂永生：无限次）

# 自动聊天配置
AUTO_CHAT_EXCLUDE_PLAYER = True  # 自动聊天是否排除玩家角色
ACTION_TIME_COST = {         # 行动消耗天数
    "eat": 0.1,
    "sleep": 0.2,
    "work": 0.3,
    "job_hunt": 0.2,
    "relax": 0.1,
    "socialize": 0.1,
    "shop": 0.2
}

# 状态自然衰减（每天）
NATURAL_DECAY = {
    "hunger": -10,
    "energy": -5,
    "social": -5,
    "fun": -5
}

# ===== 小红书博主配置 =====
# 小红书平台参数
XIAOHONGSHU_CONFIG = {
    "max_tags": 5,                    # 最多标签数
    "max_title_length": 20,           # 标题最大长度
    "max_content_length": 1000,       # 正文最大长度
    "base_followers": 100,            # 初始粉丝数
    "base_engagement_rate": 0.02,     # 基础互动率（2%）
    "hot_probability": 0.05,          # 爆款概率（5%）
    "income_per_1000_views": 10,      # 每千次阅读收入（元）
    # 官方API配置（可选，如不配置则使用模拟模式）
    "api_enabled": False,             # 是否启用官方API
    "app_id": "",                     # 小红书开放平台App ID
    "app_secret": "",                 # App Secret
    "access_token": "",               # 用户授权Access Token
    "api_endpoint": "https://api.xiaohongshu.com/api/gxapi/",  # API端点
    # Playwright自动化配置
    "playwright_cookie_file": "xhs_cookies.txt",  # cookie文件路径
    "playwright_headless": True,      # 是否无头模式运行
}