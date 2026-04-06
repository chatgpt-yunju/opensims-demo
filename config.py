# OpenSims Demo Configuration

# API配置（默认值）
API_ENDPOINT = "https://api.yunjunet.cn/v1/chat/completions"
API_KEY = ""
API_TIMEOUT = 30  # 秒
API_MODEL = "step-3.5-flash"
USE_MOCK = False

# 性格预设
PERSONALITY_PRESETS = {
    "温柔型": {"friendliness": 0.9, "humor": 0.3, "seriousness": 0.2},
    "幽默型": {"friendliness": 0.7, "humor": 0.9, "seriousness": 0.1},
    "严肃型": {"friendliness": 0.4, "humor": 0.1, "seriousness": 0.9},
    "中立型": {"friendliness": 0.5, "humor": 0.5, "seriousness": 0.5}
}

# 数据文件路径
DATA_FILE = "demo_data.json"

# 自动聊天配置（CLI模式使用）
AUTO_CHAT_ENABLED = False
AUTO_CHAT_INTERVAL = 30
AUTO_CHAT_PROBABILITY = 0.3
AUTO_CHAT_EXCLUDE_PLAYER = True

# 最大虚拟人数量
MAX_VIRTUAL_HUMANS = 10

# 人生阶段定义
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
    "小红书博主",
    "贵人"
]

# 游戏参数
DAY_ACTIONS_LIMIT = 999
ACTION_TIME_COST = {
    "eat": 0.1,
    "sleep": 0.2,
    "work": 0.3,
    "job_hunt": 0.2,
    "relax": 0.1,
    "socialize": 0.1,
    "shop": 0.2
}

# 状态自然衰减
NATURAL_DECAY = {
    "hunger": -10,
    "energy": -5,
    "social": -5,
    "fun": -5
}

# 小红书博主配置
XIAOHONGSHU_CONFIG = {
    "max_tags": 5,
    "max_title_length": 20,
    "max_content_length": 1000,
    "base_followers": 100,
    "base_engagement_rate": 0.02,
    "hot_probability": 0.05,
    "income_per_1000_views": 10,
    "api_enabled": False,
    "app_id": "",
    "app_secret": "",
    "access_token": "",
    "api_endpoint": "https://api.xiaohongshu.com/api/gxapi/",
    "playwright_cookie_file": "xhs_cookies.txt",
    "playwright_headless": True,
}
