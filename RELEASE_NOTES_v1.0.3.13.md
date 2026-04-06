# OpenSims v1.0.3.13 - 高级GUI增强版

## 📅 发布日期
2026-04-06

## 🎯 版本特性

### ✨ 新增功能

1. **GUI设置面板**
   - 菜单栏新增"设置"选项
   - 可自定义 API Endpoint、API Key、Model
   - 支持切换模拟模式（Mock）无需重启
   - 配置自动保存到 `settings.json`

2. **自动对话系统**
   - 可配置自动聊天轮数（1-100轮）
   - 可配置间隔时间（默认30秒）
   - 自动选择导师并生成话题
   - 消息标记 `[自动]` 区分自动对话
   - 后台线程运行，不影响交互

3. **流式输出（打字效果）**
   - API响应实时流式显示
   - 逐字符渲染，模拟真人在打字
   - 支持模拟模式流式（带延迟）
   - 自动聊天同样享受流式效果

4. **配置管理系统**
   - 新增 `settings.py` 模块
   - `settings.json` 存储用户配置
   - 自动合并默认值，容错性强
   - 配置修改后提示重启应用

### 🔧 技术改进

- `api_client.py`：
  - `generate_reply` 新增 `stream_callback` 参数
  - `_api_generate` 支持 OpenAI streaming 格式
  - `_mock_generate` 模拟流式输出
- `gui_simple.py`：
  - `get_reply` 集成流式回调
  - 新增 `_append_to_last_message`、`_finish_stream_message`
  - 自动聊天worker使用 `after` 实现非阻塞打字动画
- `config.py`：支持从 `settings.json` 动态读取配置
- `build_gui_simple.py`：自动复制 `settings.json` 和 `settings.py` 到打包目录

## 📦 发布文件

```
dist/
├── OpenSims_GUI_Simple_1.0.3.13.exe  (77.9 MB)
├── start_opensims_gui_simple_v1.0.3.13.bat
└── start_opensims_gui_simple_latest.bat
```

**必需配套文件**（运行exe时需要放在同一目录）：
- `config.py`
- `requirements.txt`
- `README.md`
- `human_like_chat.py`
- `settings.json`  (首次运行自动生成)
- `settings.py`
- `demo_data.json` (数据文件，首次运行自动生成)

## 🎮 使用指南

### 首次运行
1. 将exe和所有配套文件放在同一目录
2. 双击运行exe
3. 首次会创建默认 `settings.json`（USE_MOCK=false）
4. 在"设置"中配置API Key（如果尚未设置.env）

### 开启自动对话
1. 菜单 → 设置 → API配置
2. 勾选"开启自动对话"
3. 设置轮数（如10轮）
4. 保存并重启
5. 重启后自动聊天将在30秒间隔后开始

### 流式输出体验
- 发送消息后，回复会逐字符显示
- 模拟模式和真实API都支持
- 自动聊天的回复同样流式显示

## ⚠️ 注意事项

- 修改 `settings.json` 后需要重启应用才能生效
- 自动对话会持续消耗API配额（如果使用真实API）
- 流式输出在自动聊天线程中使用 `after` 避免阻塞GUI
- `settings.json` 已加入 `.gitignore`，避免密钥泄露

## 🔄 版本升级路径

- 从 v1.0.3.12 及更早版本升级：替换exe和配套文件即可
- 用户数据（`demo_data.json`）保持兼容
- 首次运行会自动迁移配置

## 🐛 已知问题

- 流式输出在极快网络环境下可能显示过快（暂未限流）
- 自动聊天仅支持单轮（用户→导师），不支持多轮自对话
- 设置对话框不支持即时预览修改效果

## 💡 下一步计划

- 流式速度可调（慢/中/快）
- 自动聊天支持多导师轮换
- 设置界面实时生效（无需重启）
- 主题切换（深色/浅色模式）

---

**构建信息**
- Build: 1.0.3.13 (13)
- Build Date: 2026-04-06
- Python: 3.11.9
- PyInstaller: 6.19.0
