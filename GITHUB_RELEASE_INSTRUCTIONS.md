# GitHub Release 上传指南

## 📦 Release v1.0.0 文件清单

在GitHub上创建Release时，请上传以下文件：

### 主要可执行文件
- `dist/OpenSims_1.0.0.exe` (约90MB) - 主程序（控制台模式）

### 便携包（可选）
- `OpenSims_v1.0.0_20260405.zip` - 包含exe、文档、启动脚本

### 文档
- `RELEASE_NOTES_v1.0.0.md` - 版本发布说明
- `README.md` - 主文档
- `MCP_README.md` - MCP集成指南
- `XIAOHONGSHU_IMPLEMENTATION.md` - 小红书实现详情
- `JUEJIN_EXTRACTOR.md` - 掘金提取器指南

---

## 🚀 上传步骤

1. 访问：https://github.com/chatgpt-yunju/opensims-demo/releases/new
2. 选择标签：`v1.0.0`（已创建）
3. 标题：`OpenSims v1.0.0 - 小红书自动发布完整版`
4. 描述：复制 `RELEASE_NOTES_v1.0.0.md` 内容
5. 拖动上传文件：
   - `G:\opensims_demo\dist\OpenSims_1.0.0.exe`
   - `G:\opensims_demo\OpenSims_v1.0.0_20260405.zip`
6. 点击「发布release」

---

## 📋 Release 说明摘要

```
OpenSims v1.0.0 - 小红书自动发布完整版

主要特性：
✅ 小红书博主系统（模拟/API/Playwright三种发布模式）
✅ OpenClaw Skill标准接口
✅ MCP插件（Claude Desktop集成）
✅ 掘金文章提取器
✅ 自动发布流水线（掘金→小红书）
✅ 完整文档与打包分发

完整功能列表见RELEASE_NOTES_v1.0.0.md
```

---

上传完成后，用户可以在Release页面下载exe直接运行，无需安装Python！
