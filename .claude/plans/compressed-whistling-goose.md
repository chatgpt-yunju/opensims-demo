# 计划：1:1真实社交引导系统

## Context
- 现有 `virtual_human.py` 已具备完整导师框架（4种导师类型、四阶段引导策略）
- `player_growth.py` 完整追踪玩家成长维度
- 缺失：**主动触发机制**（导师何时、如何主动找玩家）
- 缺失：**关系度动态更新**（虚拟人之间、与玩家之间）
- 缺失：**导师选择算法**（多个候选人时谁出马）

## Goal
实现"教师/贵人虚拟人主动引导玩家找到人生使命"，包括：
1. 触发条件检测（玩家状态、进度、时间）
2. 关系度更新（对话、行动影响关系）
3. 导师选择（基于关系度+专长匹配）
4. 主动引导对话（调用现有 `generate_mission_guidance()`）
5. 社交网络效应（虚拟人之间讨论玩家进展）

## Phase 1: 关系度动态更新系统

**Files to modify:**
- `virtual_human.py`
- `main.py`

**Changes:**
1. 实现 `update_relationship_with_player(delta, reason)` 方法
2. 实现 `_update_relationship_with_other_vh(other_id, delta, reason)` 方法
3. 在 `chat()` 和 `socialize()` 中调用关系更新
4. 关系度影响：
   - 高关系度（>80）：引导效果+30%
   - 中等关系度（40-80）：正常效果
   - 低关系度（<40）：引导效果减半，玩家可能抵触

## Phase 2: 主动触发引擎

**New file:** `mentor_trigger.py`

**Core class:** `MentorTriggerEngine`

**Responsibilities:**
1. 定期检查（每次玩家行动后调用）
2. 检测触发条件：
   - 玩家连续3次行动未与导师对话
   - 玩家某个技能停滞（连续2次skill_building无进展）
   - 玩家情绪低落（mood_level in ["低落", "生气", "崩溃"]）
   - 玩家收集到3个以上mission_clues但未整合
   - 玩家完成重大挑战后需要反思
3. 选择最合适的导师：
   - 过滤：必须是"教师"或"贵人"职业（待定义职业列表）
   - 排序：relationship_with_player 降序 + 最近交互时间 升序
   - 平衡：确保不总是同一位导师
4. 返回触发建议：`{mentor_id, trigger_type, reason}`

**Trigger types:**
- `"emotional_support"` - 玩家情绪低落时
- `"progress_check"` - 进度停滞时
- `"mission_synthesis"` - 线索需要整合时
- `"challenge_debrief"` - 完成挑战后需要反思
- `"proactive_checkin"` - 主动关怀（周期性）

## Phase 3: 社交网络效应

**Modify:** `auto_chat_scheduler.py`

**Add:**
1. 虚拟人之间会讨论玩家成长进展（如果知道）
2. 讨论影响：
   - 提升虚拟人对玩家的关心度（增加主动触发权重）
   - 虚拟人可能会"竞争"（谁更了解玩家）
   - 形成对玩家的统一/分歧意见

## Phase 4: Web API 集成

**Modify:** `main.py` 和 `web_api.py` (if exists)

**New endpoints:**
- `GET /api/v1/guidance/active-mentors` - 可用导师列表
- `POST /api/v1/guidance/mentor/{id}/initiate` - 导师主动发起
- `GET /api/v1/guidance/pending` - 待处理的引导（前端轮询用）

**Integration:**
- `main.py` 在每次 `chat()` 后调用 `mentor_engine.check_triggers()`
- 如果有触发，通过 `AutoChatScheduler` 或新机制让导师"主动发消息"

## Phase 5: 新增"贵人"职业类型

**Files:**
- `config.py` - 添加"贵人"到 `PROFESSIONS`
- 为"贵人"和"教师"设置特殊的主动触发权重

**Special mentor types:**
- 教师：专注于技能学习和挑战指导
- 贵人：专注于人生方向和资源链接

## Testing & Verification

**Unit Tests:**
1. `test_mentor_trigger.py` - 触发条件检测
2. `test_relationship_update.py` - 关系度更新逻辑
3. `test_mentor_selection.py` - 导师选择算法

**Integration Test:**
1. 创建玩家 + 2位导师（教师、贵人）
2. 玩家行动（工作、聊天、完成挑战）
3. 验证：导师是否会主动发送引导消息
4. 验证：关系度随交互变化
5. 验证：虚拟人之间讨论玩家进展

**CLI Demo:**
- 运行 `main.py`，观察后台日志
- "小明，你最近在探索什么？" - 导师主动消息

## Implementation Order

1. Phase 1 (关系度更新) - 1小时
2. Phase 2 (主动触发引擎) - 2小时
3. Phase 3 (社交网络效应) - 1小时
4. Phase 4 (Web API集成) - 1小时
5. Phase 5 (新增贵人职业) - 0.5小时
6. Testing - 1小时

**Total estimate:** 6.5小时

## Risks & Mitigation

| Risk | Mitigation |
|------|------------|
| 主动引导过多打扰玩家 | 设置触发冷却（同一导师24小时内不重复主动） |
| 关系度计算复杂 | 简化公式：基础值 + 对话次数*2 + 成功引导*5 - 忽视*1 |
| 多导师竞争失衡 | 限制每天最多2次主动引导，随机选择 |

## Success Criteria

- ✅ 玩家不用主动找导师，导师会定期主动关心
- ✅ 虚拟人之间的对话内容包含玩家成长话题
- ✅ 关系度随交互动态变化（0-100）
- ✅ 多个导师时，选择逻辑合理（不总是同一个人）
- ✅ 引导内容基于玩家成长状态（调用现有 `generate_mission_guidance()`）

---
**Created:** 2025-04-05
**Status:** Ready for implementation
