# 性格辅助函数

def apply_personality_effect(personality: dict, user_input: str) -> dict:
    """
    根据性格参数影响回复的语气
    返回额外的context信息供API使用
    """
    effects = []

    if personality.get("friendliness", 0.5) > 0.7:
        effects.append("语气友好、亲切")
    if personality.get("humor", 0.5) > 0.7:
        effects.append("带点幽默感")
    if personality.get("seriousness", 0.5) > 0.7:
        effects.append("回答严谨、准确")

    return {"style_hints": effects}