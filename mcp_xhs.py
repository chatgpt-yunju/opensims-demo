#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小红书发布MCP插件 (适配 MCP 1.27.0)
符合Model Context Protocol规范
可用于Claude Desktop等MCP客户端
"""

import os
import asyncio
from typing import Any, Dict, List
from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.models import InitializationOptions

# 导入我们的小红书API
from xhs_api import get_xhs_client
from config import XIAOHONGSHU_CONFIG

# 创建MCP服务器
server = Server("opensims-xiaohongshu")

@server.list_tools()
async def list_tools() -> List[Tool]:
    """列出可用工具"""
    return [
        Tool(
            name="xhs_publish",
            description="发布小红书笔记（支持官方API和Playwright自动化）",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "笔记标题（20字以内）"
                    },
                    "content": {
                        "type": "string",
                        "description": "笔记正文内容（1000字以内）"
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "标签列表（最多5个）"
                    },
                    "images": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "图片URL列表（可选）"
                    },
                    "use_playwright": {
                        "type": "boolean",
                        "description": "使用Playwright浏览器自动化（绕过API审核）",
                        "default": False
                    }
                },
                "required": ["title", "content"]
            }
        ),
        Tool(
            name="xhs_get_stats",
            description="获取小红书博主统计数据",
            inputSchema={
                "type": "object",
                "properties": {
                    "character_id": {
                        "type": "string",
                        "description": "OpenSims角色ID"
                    },
                    "full": {
                        "type": "boolean",
                        "description": "详细统计",
                        "default": False
                    }
                },
                "required": ["character_id"]
            }
        ),
        Tool(
            name="xhs_config_info",
            description="查看小红书配置",
            inputSchema={"type": "object", "properties": {}}
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """处理工具调用"""
    if name == "xhs_publish":
        return await xhs_publish(arguments)
    elif name == "xhs_get_stats":
        return await xhs_get_stats(arguments)
    elif name == "xhs_config_info":
        return await xhs_config_info()
    else:
        raise ValueError(f"Unknown tool: {name}")

async def xhs_publish(args: Dict[str, Any]) -> List[TextContent]:
    """发布小红书笔记"""
    title = args.get("title", "").strip()
    content = args.get("content", "").strip()
    tags = args.get("tags", [])
    images = args.get("images", [])
    use_playwright = args.get("use_playwright", False)

    if not title or not content:
        return [TextContent(type="text", text="错误：标题和内容不能为空")]

    # 使用官方API
    if not use_playwright:
        try:
            client = get_xhs_client()
            if not client.enabled:
                return [TextContent(type="text", text="""小红书API未启用。

配置方法：
1. 编辑 config.py
2. 设置:
   XIAOHONGSHU_CONFIG["api_enabled"] = True
   XIAOHONGSHU_CONFIG["app_id"] = "your_app_id"
   XIAOHONGSHU_CONFIG["app_secret"] = "your_app_secret"
   XIAOHONGSHU_CONFIG["access_token"] = "user_token"

或使用 use_playwright=true 通过浏览器自动化发布。""")]

            result = client.publish_note(
                title=title[:XIAOHONGSHU_CONFIG['max_title_length']],
                content=content[:XIAOHONGSHU_CONFIG['max_content_length']],
                images=images,
                tags=tags
            )

            if result.get('success'):
                note_id = result.get('note_id', 'unknown')
                note_url = result.get('url', '')
                response = f"✅ 发布成功！\n标题：{title}\n标签：{', '.join(tags) if tags else '无'}\nNote ID：{note_id}"
                if note_url:
                    response += f"\n链接：{note_url}"
                return [TextContent(type="text", text=response)]
            else:
                return [TextContent(type="text", text=f"❌ 发布失败：{result.get('error', 'Unknown error')}")]

        except Exception as e:
            return [TextContent(type="text", text=f"API异常：{str(e)}")]

    # 使用Playwright
    else:
        try:
            from xhs_playwright import XHSPlaywrightPosterSync

            cookie_path = 'xhs_cookies.txt'
            if not os.path.exists(cookie_path):
                return [TextContent(type="text", text="""需要先登录小红书。

步骤：
1. Chrome登录 https://www.xiaohongshu.com
2. F12 → Application → Cookies → 复制所有cookie
3. 保存到 xhs_cookies.txt（单行：name1=value1; name2=value2）

或使用官方API。""")]

            with XHSPlaywrightPosterSync(headless=True) as poster:
                with open(cookie_path, 'r', encoding='utf-8') as f:
                    cookie_str = f.read().strip()
                poster.login(cookie_str)
                result = poster.create_note(title=title, content=content, images=images, tags=tags)

                if result['success']:
                    response = f"✅ 发布成功（Playwright）！\n标题：{title}\n标签：{', '.join(tags) if tags else '无'}\nNote ID：{result.get('note_id', 'unknown')}"
                    if result.get('url'):
                        response += f"\n链接：{result['url']}"
                    return [TextContent(type="text", text=response)]
                else:
                    return [TextContent(type="text", text=f"❌ 发布失败：{result.get('error', 'Unknown error')}")]

        except ImportError:
            return [TextContent(type="text", text="""缺少Playwright依赖。

安装：
pip install playwright
playwright install chromium
""")]

async def xhs_get_stats(args: Dict[str, Any]) -> List[TextContent]:
    """获取统计数据"""
    character_id = args.get("character_id")
    full = args.get("full", False)

    if not character_id:
        return [TextContent(type="text", text="错误：需要character_id参数")]

    try:
        import requests
        resp = requests.get(f"http://localhost:8000/api/v1/characters/{character_id}", timeout=5)
        if resp.status_code != 200:
            return [TextContent(type="text", text=f"HTTP错误：{resp.status_code}")]

        char = resp.json()
        xs = char.get('xiaohongshu', {})

        if not xs:
            return [TextContent(type="text", text=f"角色 {char['name']} 不是小红书博主")]

        if full:
            text = f"""📊 {char['name']} 详细数据：
粉丝：{xs.get('followers', 0)}
总阅读：{xs.get('total_views', 0)}
总点赞：{xs.get('total_likes', 0)}
总收藏：{xs.get('total_collections', 0)}
总评论：{xs.get('total_comments', 0)}
笔记数：{xs.get('posts_published', 0)}
爆款：{xs.get('hot_posts', 0)}
互动率：{xs.get('engagement_rate', 0):.2%}
金钱：${char.get('money', 0)}"""
        else:
            text = f"📈 {char['name']}：粉丝 {xs.get('followers', 0)}人，笔记 {xs.get('posts_published', 0)}篇，互动率 {xs.get('engagement_rate', 0):.2%}"

        return [TextContent(type="text", text=text)]

    except requests.ConnectionError:
        return [TextContent(type="text", text="无法连接OpenSims API，请确保 web_api.py 运行中")]
    except Exception as e:
        return [TextContent(type="text", text=f"查询异常：{str(e)}")]

async def xhs_config_info() -> List[TextContent]:
    """显示配置信息"""
    cfg = XIAOHONGSHU_CONFIG
    text = f"""小红书配置：

官方API:
  enabled: {cfg.get('api_enabled', False)}
  app_id: {"****" if cfg.get('app_id') else "未设置"}
  app_secret: {"****" if cfg.get('app_secret') else "未设置"}
  access_token: {"****" if cfg.get('access_token') else "未设置"}

模拟参数:
  初始粉丝: {cfg.get('base_followers', 100)}
  爆款概率: {cfg.get('hot_probability', 0.05)}
  每千阅读收入: ${cfg.get('income_per_1000_views', 10)}

Playwright:
  cookie文件: {cfg.get('playwright_cookie_file', 'xhs_cookies.txt')}
  无头模式: {cfg.get('playwright_headless', True)}

提示：配置官方API后可以真实发布到小红书账户。
"""
    return [TextContent(type="text", text=text)]

async def main():
    """MCP服务器主入口"""
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="opensims-xiaohongshu",
                server_version="1.0.0",
                capabilities=server.get_capabilities(read_stream, write_stream)
            )
        )

if __name__ == "__main__":
    asyncio.run(main())
