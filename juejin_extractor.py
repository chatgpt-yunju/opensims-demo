#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用Playwright提取掘金文章内容
完整提取：标题、作者、发布时间、正文、标签、阅读数、点赞数等
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional
from playwright.async_api import async_playwright, Page, Browser

class JuejinExtractor:
    """掘金文章提取器"""

    def __init__(self, headless: bool = True, timeout: int = 30000):
        self.headless = headless
        self.timeout = timeout
        self.browser: Optional[Browser] = None
        self.context = None
        self.page: Optional[Page] = None

    async def start(self):
        """启动浏览器"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--disable-gpu'
            ]
        )
        self.context = await self.browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
            locale='zh-CN',
            extra_http_headers={
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
        )
        # 隐藏自动化特征
        await self.context.add_init_script("""
            // 隐藏webdriver特征
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            // 模拟插件
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            // 模拟语言
            Object.defineProperty(navigator, 'languages', {
                get: () => ['zh-CN', 'zh', 'en-US', 'en']
            });
        """)
        self.page = await self.context.new_page()

    async def stop(self):
        """关闭浏览器"""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()

    async def extract_article(self, url: str) -> Dict[str, Any]:
        """
        提取掘金文章完整内容

        参数:
            url: 掘金文章URL（支持带参数的URL）

        返回:
            包含文章信息的字典
        """
        try:
            print(f"[Juejin] 开始提取: {url}")

            # 1. 导航到页面
            await self.page.goto(url, timeout=self.timeout)
            await asyncio.sleep(3)  # 等待初始加载

            # 2. 等待页面主要元素加载
            try:
                # 等待文章标题出现
                await self.page.wait_for_selector('[class*="article-title"], h1, .title', timeout=10000)
            except:
                print("[Juejin] 警告：未找到标题元素，继续尝试...")

            # 3. 滚动加载完整内容
            await self._scroll_to_load_all()

            # 4. 提取数据
            data = await self._extract_all_data(url)

            print(f"[Juejin] 提取完成: {data['title'][:50]}...")
            return data

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'url': url
            }

    async def _scroll_to_load_all(self):
        """滚动页面以加载所有内容（包括懒加载）"""
        try:
            # 获取初始高度
            last_height = await self.page.evaluate('() => document.documentElement.scrollHeight || document.body.scrollHeight')
            max_scrolls = 15
            scrolls = 0

            while scrolls < max_scrolls:
                # 滚动到80%位置（不是100%，避免无限加载）
                await self.page.evaluate('window.scrollTo(0, document.documentElement.scrollHeight * 0.8)')
                await asyncio.sleep(1.0)

                # 等待可能的动态加载
                try:
                    await self.page.wait_for_load_state('networkidle', timeout=2000)
                except:
                    pass

                # 检查高度变化
                new_height = await self.page.evaluate('() => document.documentElement.scrollHeight || document.body.scrollHeight')
                if new_height == last_height:
                    # 再等一次确认
                    await asyncio.sleep(1)
                    new_height = await self.page.evaluate('() => document.documentElement.scrollHeight || document.body.scrollHeight')
                    if new_height == last_height:
                        break
                last_height = new_height
                scrolls += 1

            # 等待最后加载完成
            await asyncio.sleep(2)
        except Exception as e:
            print(f"[DEBUG] 滚动异常: {e}")

    async def _extract_all_data(self, url: str) -> Dict[str, Any]:
        """提取所有数据字段"""

        # 获取页面HTML用于解析
        html_content = await self.page.content()

        # 提取标题（多种选择器）
        title = await self._extract_title()

        # 提取作者信息
        author_info = await self._extract_author()

        # 提取发布时间
        publish_time = await self._extract_publish_time()

        # 提取正文内容
        content = await self._extract_content()

        # 提取标签
        tags = await self._extract_tags()

        # 提取统计数据（阅读、点赞、评论）
        stats = await self._extract_stats()

        # 提取文章ID
        article_id = self._extract_article_id_from_url(url)

        return {
            'success': True,
            'url': url,
            'article_id': article_id,
            'title': title,
            'author': author_info,
            'publish_time': publish_time,
            'content': content,
            'tags': tags,
            'stats': stats,
            'extracted_at': datetime.now().isoformat(),
            'html_length': len(html_content)
        }

    async def _extract_title(self) -> str:
        """提取文章标题"""
        # 掘金文章标题选择器（多版本兼容）
        selectors = [
            'h1.article-title',
            'h1.title',
            'h1[class*="title"]',
            '.article-header h1',
            '.title-area h1',
            'h1',  # 最后一个 resort
            '.entry-title',
            'h1.entry-title'
        ]

        for selector in selectors:
            try:
                elements = await self.page.query_selector_all(selector)
                for elem in elements:
                    text = await elem.text_content()
                    if text and len(text.strip()) > 5:  # 至少5个字符
                        return text.strip()
            except:
                continue

        # 回退：获取页面标题（不含site name）
        page_title = await self.page.title()
        if page_title and "掘金" in page_title:
            return page_title.replace(" - 掘金", "").strip()

        return "未知标题"

    async def _extract_author(self) -> Dict[str, str]:
        """提取作者信息"""
        author = {
            'name': '',
            'avatar': '',
            'url': '',
            'bio': ''
        }

        try:
            # 查找作者链接（包含/user/的链接）
            user_links = await self.page.query_selector_all('a[href*="/user/"]')
            if user_links:
                # 选择最可能是作者链接的（通常第一个是头像链接）
                for link in user_links[:5]:
                    href = await link.get_attribute('href') or ''
                    # 过滤掉机器人等非作者链接
                    if '/robots' in href or '/settings' in href:
                        continue
                    if '/user/' in href:
                        author['url'] = href
                        # 从URL提取用户名
                        username_part = href.split('/user/')[-1]
                        username = username_part.split('?')[0].split('/')[0]
                        if username and len(username) > 2:
                            author['name'] = username
                            break

                # 如果URL没提取到名字，尝试链接文本
                if not author['name']:
                    for link in user_links[:5]:
                        text = await link.text_content()
                        if text and 2 < len(text.strip()) < 20:
                            author['name'] = text.strip()
                            break

            # 获取作者头像
            if not author['avatar']:
                imgs = await self.page.query_selector_all('img[src*="avatar"], img[class*="avatar"], .author-avatar img')
                for img in imgs:
                    src = await img.get_attribute('src')
                    if src and ('avatar' in src or 'profile' in src):
                        author['avatar'] = src
                        break

        except Exception as e:
            print(f"[DEBUG] 提取作者异常: {e}")

        return author

    async def _extract_publish_time(self) -> str:
        """提取发布时间"""
        try:
            # 查找时间元素
            time_selectors = [
                'time',
                '[class*="time"]',
                '[class*="date"]',
                'span:has-text("日")',
                'span:has-text("月")',
                'span:has-text(":")'
            ]

            for selector in time_selectors:
                elements = await self.page.query_selector_all(selector)
                for elem in elements:
                    text = await elem.text_content()
                    if text and any(char in text for char in ['日', '月', ':', '-', '/']):
                        # 检查是否是相对时间（如"3天前"）
                        if any(word in text for word in ['前', '天', '小时', '分钟']):
                            return text.strip()
                        # 尝试提取datetime属性
                        datetime_attr = await elem.get_attribute('datetime')
                        if datetime_attr:
                            return datetime_attr
                        return text.strip()
        except:
            pass

        return ""

    async def _extract_content(self) -> str:
        """提取文章正文内容"""
        content_parts = []

        # 掘金内容选择器（多版本）
        content_selectors = [
            '.article-content',
            '.markdown-body',
            '[class*="markdown-body"]',
            '[class*="article-content"]',
            'main.markdown-body',
            '.content-main',
            'article .content',
            '.entry-content'
        ]

        main_content = None
        for selector in content_selectors:
            try:
                # 不等待，直接查询
                elem = await self.page.query_selector(selector)
                if elem:
                    main_content = elem
                    print(f"[DEBUG] 找到内容容器: {selector}")
                    break
            except:
                continue

        if main_content:
            # 方法1：按顺序提取所有子元素，保持文档流
            children = await main_content.query_selector_all('*')
            current_section = []
            headings = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'pre', 'ul', 'ol', 'blockquote']

            for child in children:
                tag = await child.evaluate('el => el.tagName.toLowerCase()')
                text = await child.text_content()
                text = text.strip() if text else ''

                if not text:
                    continue

                if tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    # 保存之前的段落
                    if current_section:
                        content_parts.append('\n'.join(current_section))
                        current_section = []
                    # 添加标题
                    content_parts.append(f"\n{text}\n{'='*min(len(text), 50)}")
                elif tag == 'p':
                    current_section.append(text)
                elif tag == 'pre':
                    # 代码块
                    code = await child.text_content()
                    if code:
                        content_parts.append(f"\n```\n{code.strip()}\n```")
                elif tag in ['ul', 'ol']:
                    # 列表
                    items = await child.query_selector_all('li')
                    for li in items:
                        li_text = await li.text_content()
                        if li_text:
                            content_parts.append(f"  • {li_text.strip()}")
                elif tag == 'blockquote':
                    content_parts.append(f"\n> {text}\n")

            # 添加最后一段
            if current_section:
                content_parts.append('\n'.join(current_section))

            result = '\n'.join(filter(None, content_parts))
            if result and len(result) > 100:
                return result

        # 回退方案：提取所有可见文本
        print("[DEBUG] 使用回退提取方案")
        all_paragraphs = await self.page.query_selector_all('p, pre, blockquote, h1, h2, h3, h4, h5, h6, li')
        for elem in all_paragraphs:
            text = await elem.text_content()
            if text and len(text.strip()) > 5:
                content_parts.append(text.strip())

        result = '\n'.join(content_parts)
        if not result or len(result) < 200:
            # 更激进的回退：提取整个body文本
            body_text = await self.page.evaluate('() => document.body.innerText')
            lines = [line.strip() for line in body_text.split('\n') if len(line.strip()) > 10]
            result = '\n'.join(lines[:100])  # 只取前100行

        return result or "无法提取正文内容"

    async def _extract_tags(self) -> list:
        """提取文章标签"""
        tags = []

        # 掘金标签选择器
        tag_selectors = [
            'a[href*="/tag/"]',
            '.tags a',
            '.tag-list span',
            '[class*="tag-item"]',
            'a:has-text("#")'
        ]

        for selector in tag_selectors:
            try:
                elements = await self.page.query_selector_all(selector)
                for elem in elements:
                    text = await elem.text_content()
                    if text:
                        # 清理标签文本
                        tag = text.strip().lstrip('#').strip()
                        if 1 <= len(tag) <= 20 and tag not in tags:
                            tags.append(tag)
            except:
                continue

        # 去重并限制数量
        unique_tags = []
        for tag in tags:
            if tag and tag not in unique_tags:
                unique_tags.append(tag)

        return unique_tags[:10]

    async def _extract_stats(self) -> Dict[str, Any]:
        """提取统计数据（阅读、点赞、评论）"""
        stats = {
            'views': 0,
            'likes': 0,
            'comments': 0,
            'collections': 0
        }

        try:
            # 掘金统计数据显示在 .action-item 或 .user-action-bar 中
            action_items = await self.page.query_selector_all('.action-item, [class*="action"], [class*="stat"]')

            for item in action_items:
                text = await item.text_content()
                if not text:
                    continue

                text_lower = text.lower()
                import re

                # 提取所有数字
                numbers = re.findall(r'(\d+\.?\d*[km万]?)', text_lower)
                if not numbers:
                    continue

                # 判断类型
                if any(kw in text_lower for kw in ['阅读', 'view', '浏览']):
                    stats['views'] = max(stats['views'], self._parse_number(numbers[0]))
                if '点赞' in text_lower or 'like' in text_lower:
                    stats['likes'] = max(stats['likes'], self._parse_number(numbers[0]))
                if any(kw in text_lower for kw in ['评论', 'comment', '讨论']):
                    stats['comments'] = max(stats['comments'], self._parse_number(numbers[0]))
                if any(kw in text_lower for kw in ['收藏', 'collect', '保存']):
                    stats['collections'] = max(stats['collections'], self._parse_number(numbers[0]))

        except Exception as e:
            print(f"[Juejin] 提取统计数据异常: {e}")

        return stats

    def _parse_number(self, num_str: str) -> int:
        """解析数字（处理 1.2k, 3.5万 等格式）"""
        num_str = num_str.lower().strip()

        # 直接数字
        try:
            return int(num_str)
        except:
            pass

        # 处理小数
        try:
            return int(float(num_str))
        except:
            pass

        # 处理千位符
        if 'k' in num_str:
            try:
                return int(float(num_str.replace('k', '')) * 1000)
            except:
                pass

        # 处理万（中文）
        if '万' in num_str:
            try:
                return int(float(num_str.replace('万', '')) * 10000)
            except:
                pass

        return 0

    def _extract_article_id_from_url(self, url: str) -> str:
        """从URL提取文章ID"""
        try:
            # https://juejin.cn/post/7623681583884075017
            parts = url.split('/post/')
            if len(parts) > 1:
                return parts[1].split('?')[0].split('#')[0]
        except:
            pass
        return ""

    async def save_to_json(self, data: Dict[str, Any], filename: str = None):
        """保存提取结果到JSON文件"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            article_id = data.get('article_id', 'unknown')
            filename = f"juejin_article_{article_id}_{timestamp}.json"

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"[Juejin] 已保存JSON: {filename}")
        return filename

    async def save_to_txt(self, data: Dict[str, Any], filename: str = None) -> str:
        """
        保存为纯文本格式（适合阅读/导入Markdown编辑器）

        格式：
        标题
        作者：xxx 发布时间：xxx
        标签：tag1, tag2, tag3

        正文内容...
        """
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            article_id = data.get('article_id', 'unknown')
            filename = f"juejin_article_{article_id}_{timestamp}.txt"

        lines = []

        # 标题
        lines.append("=" * 80)
        lines.append(data.get('title', '无标题'))
        lines.append("=" * 80)
        lines.append("")

        # 元信息
        author_name = data.get('author', {}).get('name', '未知')
        publish_time = data.get('publish_time', '未知')
        lines.append(f"作者：{author_name}")
        lines.append(f"发布时间：{publish_time}")
        lines.append(f"原文链接：{data.get('url', '')}")
        lines.append("")

        # 标签
        tags = data.get('tags', [])
        if tags:
            lines.append(f"标签：{', '.join(tags)}")
            lines.append("")

        # 统计数据
        stats = data.get('stats', {})
        lines.append(f"阅读：{stats.get('views', 0)}  点赞：{stats.get('likes', 0)}  评论：{stats.get('comments', 0)}  收藏：{stats.get('collections', 0)}")
        lines.append("")
        lines.append("-" * 80)
        lines.append("")

        # 正文
        content = data.get('content', '')
        if content:
            lines.append(content)
        else:
            lines.append("[无法提取正文内容]")

        lines.append("")
        lines.append("-" * 80)
        lines.append(f"提取时间：{data.get('extracted_at', '未知')}")
        lines.append(f"数据来源：掘金 (juejin.cn)")
        lines.append(f"文章ID：{data.get('article_id', 'unknown')}")

        # 写入文件
        with open(filename, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

        print(f"[Juejin] 已保存TXT: {filename}")
        return filename


# 同步包装器
class JuejinExtractorSync:
    """同步版本的掘金提取器"""

    def __init__(self, headless: bool = True, timeout: int = 30000):
        self._extractor = JuejinExtractor(headless, timeout)
        self._loop = None

    def extract(self, url: str) -> Dict[str, Any]:
        """同步提取（自动管理浏览器生命周期）"""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._extractor.start())
            result = self._loop.run_until_complete(
                self._extractor.extract_article(url)
            )
            return result
        finally:
            # 提取完成后关闭浏览器
            if self._extractor:
                self._loop.run_until_complete(self._extractor.stop())
            self._loop.close()

    def extract_and_save(self, url: str, filename: str = None, format: str = 'json') -> Dict[str, Any]:
        """
        提取并保存（会自动管理浏览器生命周期）

        参数:
            filename: 文件名（自动生成如果为None）
            format: 'json' 或 'txt'
        """
        # 启动事件循环和浏览器
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            # 启动浏览器
            self._loop.run_until_complete(self._extractor.start())

            # 提取数据
            data = self._loop.run_until_complete(
                self._extractor.extract_article(url)
            )

            # 保存数据
            if data.get('success'):
                if format == 'txt':
                    self._loop.run_until_complete(
                        self._extractor.save_to_txt(data, filename)
                    )
                else:
                    self._extractor.save_to_json(data, filename)

            return data
        finally:
            # 关闭浏览器和循环
            if self._extractor:
                self._loop.run_until_complete(self._extractor.stop())
            self._loop.close()

    def __enter__(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self._extractor.start())
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._loop:
            self._loop.run_until_complete(self._extractor.stop())
            self._loop.close()


# 命令行使用
if __name__ == "__main__":
    import sys

    # 默认URL（可命令行参数覆盖）
    test_url = "https://juejin.cn/post/7623681583884075017?push_animated=1&webview_progress_bar=1&show_loading=0&theme=light"

    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        print(f"用法: python juejin_extractor.py <文章URL>")
        print(f"示例: python juejin_extractor.py {test_url}")
        url = test_url

    print("=" * 60)
    print("掘金文章提取器")
    print("=" * 60)

    extractor = JuejinExtractorSync(headless=False)  # 设为False查看浏览器操作

    try:
        print(f"\n开始提取: {url}")
        result = extractor.extract_and_save(url)

        if result['success']:
            print("\n" + "=" * 60)
            print("提取结果摘要:")
            print(f"  标题: {result['title'][:60]}...")
            print(f"  作者: {result['author'].get('name', '未知')}")
            print(f"  发布时间: {result['publish_time']}")
            print(f"  标签: {', '.join(result['tags'][:5])}")
            print(f"  统计: 阅读{result['stats']['views']}, 点赞{result['stats']['likes']}, 评论{result['stats']['comments']}")
            print(f"  正文长度: {len(result['content'])} 字符")
            print(f"  已保存JSON")
        else:
            print(f"\n❌ 提取失败: {result.get('error')}")

    except KeyboardInterrupt:
        print("\n[!] 用户中断")
    except Exception as e:
        print(f"\n❌ 异常: {e}")
        import traceback
        traceback.print_exc()

    print("=" * 60)
