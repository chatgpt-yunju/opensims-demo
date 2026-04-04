# 掘金文章提取器 (Playwright)

使用Playwright浏览器自动化提取掘金（juejin.cn）文章完整内容。

## 功能

- ✅ 提取文章标题、作者、发布时间
- ✅ 提取正文内容（包含代码块、列表、标题结构）
- ✅ 提取标签
- ✅ 提取统计数据（阅读、点赞、评论、收藏）
- ✅ 保存为JSON格式
- ✅ 处理懒加载（自动滚动）

## 安装依赖

```bash
# 安装Playwright
pip install playwright

# 安装Chromium浏览器
playwright install chromium

# 可选：安装到系统目录（需要管理员）
playwright install chromium --with-deps
```

## 使用方法

### 命令行

```bash
# 提取指定URL
python juejin_extractor.py "https://juejin.cn/post/7623681583884075017"

# 不带参数则使用内置示例URL
python juejin_extractor.py
```

### Python代码

```python
from juejin_extractor import JuejinExtractorSync

# 方式1：使用上下文管理器（自动启动/关闭）
with JuejinExtractorSync(headless=False) as extractor:
    data = extractor.extract("https://juejin.cn/post/7623681583884075017")
    print(data['title'])
    print(data['content'][:200])

# 方式2：单独调用
extractor = JuejinExtractorSync(headless=True)
result = extractor.extract_and_save(
    "https://juejin.cn/post/7623681583884075017",
    filename="my_article.json"
)
```

## 输出格式

```json
{
  "success": true,
  "url": "https://juejin.cn/post/7623681583884075017",
  "article_id": "7623681583884075017",
  "title": "文章标题",
  "author": {
    "name": "作者名",
    "avatar": "头像URL",
    "url": "用户主页URL",
    "bio": "作者简介"
  },
  "publish_time": "2024-01-15 10:30",
  "content": "正文内容...（包含代码块、列表等）",
  "tags": ["前端", "JavaScript", "React"],
  "stats": {
    "views": 1234,
    "likes": 56,
    "comments": 7,
    "collections": 23
  },
  "extracted_at": "2024-01-16 08:30:00",
  "html_length": 45678
}
```

## 参数说明

### JuejinExtractorSync 构造函数

| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `headless` | bool | True | 是否无头模式（不显示浏览器窗口） |
| `timeout` | int | 30000 | 页面加载超时（毫秒） |

### extract_article() 返回

包含以上所有字段的字典。如果 `success=False`，则包含 `error` 字段说明失败原因。

## 注意事项

1. **反爬虫机制**：掘金可能有反爬，建议：
   - 不要频繁请求（间隔至少5秒）
   - 使用 `headless=False` 首次调试，手动完成可能的验证码
   - 添加真实User-Agent和浏览器特征（已内置）

2. **页面结构变化**：掘金前端可能更新，如果提取失败，需要调整CSS选择器：
   - 修改 `_extract_title()` 中的选择器
   - 修改 `_extract_content()` 中的 `content_selectors` 列表

3. **网络问题**：如果加载慢，可增加 `timeout` 参数

## 故障排查

### 问题1：无法加载页面
```python
# 增加超时时间
extractor = JuejinExtractorSync(headless=False, timeout=60000)
```

### 问题2：提取不到内容
- 检查页面是否完全加载（滚动后）
- 使用 `headless=False` 查看浏览器实际显示
- 检查控制台是否有错误

### 问题3：被识别为机器人
- 确保 `_start()` 中设置了真实User-Agent
- 可能需要手动处理验证码
- 降低请求频率

## 扩展功能建议

- [ ] 支持列表页提取（多篇文章）
- [ ] 自动下载文中图片
- [ ] 转换为Markdown格式
- [ ] 提取评论内容
- [ ] 支持登录后提取付费内容

---

**更新**：2026-04-05  
**版本**：1.0
