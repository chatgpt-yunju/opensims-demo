# OpenSims v1.0.0 Release Notes

## 🎉 重大更新

这是OpenSims的首个公开发布版本，完整实现小红书自动发布系统，支持三种发布模式，并集成OpenClaw标准Skill接口。

## ✨ 新功能

### 1. 小红书博主系统 (v1.0.0)
- **三种发布模式**：
  - ✅ 模拟模式：快速测试，无真实发布
  - ✅ 官方API：通过小红书开放平台真实发布（需申请）
  - ✅ Playwright自动化：绕过审核，使用cookie真实发布

### 2. OpenClaw Skill 接口
- `opensims_skill.py` - 标准OpenClaw skill封装
- 支持：虚拟人管理、行动、聊天、think、小红书发布

### 3. MCP 插件 (Claude Desktop)
- `mcp_xhs.py` - Model Context Protocol服务器
- Claude Desktop可直接调用小红书发布功能

### 4. 掘金文章提取器
- `juejin_extractor.py` - 基于Playwright的完整抓取
- 提取：标题、作者、时间、正文、标签、统计数据
- 支持保存为JSON/TXT

### 5. 自动发布流水线
- `auto_publisher.py` - 端到端解决方案
- 流程：抓取掘金 → AI改写为小红书风格 → 自动发布

### 6. 打包分发
- `build.py` - 版本化PyInstaller打包
- 生成：`OpenSims_1.0.0.exe` (单文件，~90MB)
- 便携包：`OpenSims_v1.0.0_20260405.zip`

## 📦 文件清单

### 核心代码（23个Python文件）
- `main.py` - CLI主程序
- `virtual_human.py` - SimPerson核心类
- `web_api.py` - FastAPI HTTP服务器
- `config.py` - 配置（含小红书配置）
- `xhs_api.py` - 小红书官方API客户端
- `xhs_playwright.py` - 浏览器自动化
- `mcp_xhs.py` - MCP插件
- `juejin_extractor.py` - 掘金提取器
- `auto_publisher.py` - 自动发布器
- `opensims_skill.py` - OpenClaw Skill接口
- ... 以及 Tests 和 utils

### 文档（5个Markdown）
- `README.md` - 主文档（已更新小红书章节）
- `MCP_README.md` - MCP集成详细指南
- `XIAOHONGSHU_IMPLEMENTATION.md` - 小红书实现总结
- `JUEJIN_EXTRACTOR.md` - 掘金提取器使用指南
- `RELEASE_NOTES_v1.0.0.md` - 本文件

### 配置文件
- `requirements.txt` - 核心依赖
- `requirements_mcp.txt` - MCP依赖
- `config.py` - 所有配置项
- `.gitignore` - Git忽略规则

### 资源文件
- `static/icon.ico` - 应用图标

## 🔧 安装与使用

### 快速开始（CLI）
```bash
# 1. 克隆仓库
git clone https://github.com/chatgpt-yunju/opensims-demo.git
cd opensims-demo

# 2. 安装依赖
pip install -r requirements.txt

# 3. 运行
python main.py
```

### 使用exe（无需安装Python）
1. 下载 `OpenSims_v1.0.0_20260405.zip`
2. 解压到任意目录
3. 运行 `start_opensims_v1.0.0.bat`

### 启动Web API
```bash
python web_api.py
# 访问 http://localhost:8000/docs 查看API文档
```

### Claude Desktop集成（MCP）
1. 安装依赖：`pip install mcp playwright`
2. 编辑Claude Desktop配置文件，添加：
```json
{
  "mcpServers": {
    "opensims-xiaohongshu": {
      "command": "python",
      "args": ["G:/opensims_demo/mcp_xhs.py"]
    }
  }
}
```
3. 重启Claude Desktop，即可在工具面板使用 `xhs_publish`

## 🎯 主要特性说明

### 小红书发布三种方式

| 方式 | 配置 | 优点 | 缺点 |
|------|------|------|------|
| 模拟模式 | 无需配置 | 立即可用，不依赖外部 | 不真实发布 |
| 官方API | `config.py`设置app_id/secret/token | 稳定，官方支持 | 需要审核申请 |
| Playwright | `xhs_cookies.txt` | 绕过审核，真实发布 | 需要cookie，可能风控 |

### 虚拟人系统
- 多角色管理（UUID标识）
- 年龄增长、职业系统
- 状态：健康、精力、饥饿、社交、娱乐、金钱
- 自动聊天（AI ↔ AI）
- Claude Code决策（think接口）

## 📊 统计数据

- **总文件数**：40+（代码+文档）
- **代码行数**：~4000+ LOC
- **支持接口**：CLI / HTTP REST API / MCP / OpenClaw Skill
- **测试覆盖**：6个独立测试脚本

## 🐛 已知问题

1. **Playwright extracts**：某些页面结构可能变化，需要定期更新选择器
2. **MCP插件**：需要在Claude Desktop v1.0+ 才能使用
3. **Exe文件大小**：约90MB（包含所有依赖）

## 🔮 未来计划

- [ ] 图片下载和上传（小红书图文）
- [ ] AI改写集成（使用Claude API）
- [ ] 定时发布队列
- [ ] 多账号管理
- [ ] 支持其他平台（知乎、公众号）
- [ ] Web GUI界面

## 📝 版本历史

### v1.0.0 (2026-04-05)
- 小红书发布系统（3种模式）
- OpenClaw Skill接口
- MCP插件
- 掘金文章提取
- 自动发布流水线
- PyInstaller打包
- 完整文档

---

**Happy Simulating! 🎮**
