# 小红书发布 OpenClaw Skill / MCP插件

OpenSims支持三种方式发布小红书笔记：

| 方式 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| **模拟模式** | 无需配置，立即可用 | 数据虚假，不发布到真实平台 | 游戏测试、演示 |
| **官方API** | 稳定、官方支持 | 需要申请开放平台，审核严格 | 正式产品、商业应用 |
| **Playwright** | 绕过审核，真实发布 | 需要提供cookie，可能被风控 | 个人使用、快速验证 |

---

## 方式1：模拟模式（默认）

无需任何配置，直接运行：

```python
from main import OpenSimsDemo
demo = OpenSimsDemo()
vh = demo.agent_manager.get_virtual_human('some_id')
result = vh.create_xiaohongshu_post()
print(result)
```

或通过HTTP API：

```bash
curl -X POST "http://localhost:8000/api/v1/characters/{id}/actions/create_xiaohongshu_post"
```

**特点**：数据纯属模拟，仅用于游戏内展示。

---

## 方式2：官方API（推荐）

### 2.1 申请小红书开放平台

1. 访问 https://open.xiaohongshu.com/
2. 注册开发者账号，创建应用
3. 获取 `app_id` 和 `app_secret`
4. 实现OAuth授权流程，获得用户 `access_token`
5. 将配置填入 `config.py`：

```python
XIAOHONGSHU_CONFIG = {
    "api_enabled": True,
    "app_id": "your_app_id_here",
    "app_secret": "your_app_secret_here",
    "access_token": "user_access_token_here",
    "api_endpoint": "https://api.xiaohongshu.com/api/gxapi/",
}
```

### 2.2 重启服务

```bash
python web_api.py  # 重启API服务器
```

### 2.3 调用

```bash
curl -X POST "http://localhost:8000/api/v1/characters/{id}/actions/create_xiaohongshu_post" \
  -H "Content-Type: application/json" \
  -d '{"title":"真实发布","content":"内容","tags":["标签1","标签2"]}'
```

**特点**：笔记会真实发布到授权的小红书账户。

---

## 方式3：Playwright浏览器自动化（绕过审核）

无需申请官方API，通过模拟浏览器操作实现真实发布。

### 3.1 安装依赖

```bash
# 安装Playwright
pip install playwright

# 安装Chromium浏览器
playwright install chromium

# 或国内源加速
playwright install chromium --with-deps
```

### 3.2 获取小红书Cookie

1. 用Chrome浏览器登录 https://www.xiaohongshu.com/
2. 按F12打开开发者工具
3. 切换到 **Application** → **Cookies** → https://www.xiaohongshu.com
4. 复制所有cookie（每行格式：`name=value`）
5. 保存到 `xhs_cookies.txt`（单行，分号分隔）

**Cookie格式示例**：
```
webId=123456; xhsTracker=...; customerClientId=...; ......
```

### 3.3 使用Playwright发布

**独立脚本**：
```bash
# 测试Playwright自动化
python xhs_playwright.py
```

该脚本会：
1. 从 `xhs_cookies.txt` 读取cookie
2. 启动Chromium浏览器（无头模式）
3. 登录小红书
4. 发布笔记

**通过OpenClaw MCP插件**：
```bash
# 安装MCP依赖
pip install mcp playwright

# 在Claude Desktop配置中添加服务器
# macOS: ~/Library/Application Support/Claude/claude_desktop_config.json
# Windows: %APPDATA%\Claude\claude_desktop_config.json

{
  "mcpServers": {
    "opensims-xiaohongshu": {
      "command": "python",
      "args": ["G:/opensims_demo/mcp_xhs.py"],
      "env": {}
    }
  }
}

**注意**：确保OpenSims服务已运行（python web_api.py）
MCP服务器会连接 http://localhost:8000 获取角色数据
```

然后在Claude中调用：
- 工具面板会出现 `xhs_publish` 工具
- 填写标题、内容、标签即可发布

**通过OpenSims HTTP API集成Playwright**（修改web_api.py）：

```python
# 在 execute_action 中添加 case "create_xiaohongshu_post_playwright":
if action_name == "create_xiaohongshu_post_playwright":
    # 调用Playwright发布
    from xhs_playwright import XHSPlaywrightPosterSync
    with XHSPlaywrightPosterSync(headless=True) as poster:
        # 登录...
        result = poster.create_note(title, content, images, tags)
    return result
```

---

## 三种方式对比与选择

| 维度 | 模拟模式 | 官方API | Playwright |
|------|----------|---------|------------|
| **真实性** | 纯游戏 | 真实发布 | 真实发布 |
| **审核要求** | 无 | 严格 | 绕过 |
| **稳定性** | 高 | 高 | 中（可能被风控） |
| **配置难度** | 极低 | 中（需申请） | 低（需cookie） |
| **长期维护** | 无需 | 需更新Token | 需更新cookie |

**建议**：
- **开发阶段**：使用模拟模式快速迭代
- **正式上线**：申请官方API，稳定可靠
- **个人项目**：使用Playwright，省去审核

---

## 故障排查

### 官方API返回"access_token invalid"

```bash
# 重新获取access_token
# 1. 生成授权URL
auth_url = f"https://www.xiaohongshu.com/creator/oauth?client_id={app_id}&redirect_uri=your_redirect_uri&response_type=code"

# 2. 用户在浏览器授权后，你获得code
# 3. 用code换取token
curl -X POST "https://api.xiaohongshu.com/api/gxapi/oauth/access_token" \
  -d "client_id=xxx&client_secret=xxx&code=xxx&grant_type=authorization_code"
```

### Playwright发布失败："验证码"

小红书可能检测到自动化工具。解决方案：
1. 使用 `headless=False` 先调试，手动完成验证码
2. 等待一段时间再试（避免频繁请求）
3. 切换回官方API

### Cookie过期

Cookie有效期约1-2个月，过期后需重新获取。

---

## 完整示例：Claude Desktop调用

在Claude Desktop中，用户可以直接说：

> "帮我用小红书账号发布一篇笔记，标题：今日探店，内容：今天去了...，标签：探店、美食"

Claude会调用 `xhs_publish` 工具，填写参数，自动完成发布。

---

## 开发路线图

- [ ] 完善Playwright选择器（小红书页面可能变化）
- [ ] 支持图片上传（本地文件到CDN）
- [ ] 定时发布功能
- [ ] 笔记草稿保存
- [ ] 数据统计自动抓取（粉丝数、阅读量）
- [ ] 视频笔记支持

---

**更新日期**：2026-04-05  
**版本**：v1.0 (支持模拟、官方API、Playwright三种方式)
