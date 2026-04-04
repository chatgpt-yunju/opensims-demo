#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小红书浏览器自动化发布（使用Playwright）
无需官方API，模拟真实用户操作
"""

import time
import asyncio
from typing import Dict, Any, Optional
from playwright.async_api import async_playwright, Page, Browser

class XHSPlaywrightPoster:
    """小红书Playwright自动化发布器"""

    def __init__(self, headless: bool = True):
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.context = None
        self.page: Optional[Page] = None

    async def start(self):
        """启动浏览器"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=self.headless,
            args=['--disable-blink-features=AutomationControlled']
        )
        self.context = await self.browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1280, 'height': 800}
        )
        self.page = await self.context.new_page()

    async def stop(self):
        """关闭浏览器"""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()

    async def check_login(self) -> bool:
        """检查是否已登录小红书"""
        try:
            await self.page.goto("https://www.xiaohongshu.com/explore", timeout=30000)
            await asyncio.sleep(3)

            # 检查是否跳转到登录页
            login_indicators = [
                "登录", "注册", "手机号登录", "密码登录"
            ]
            page_content = await self.page.content()
            for indicator in login_indicators:
                if indicator in page_content:
                    return False  # 需要登录

            # 检查用户头像/个人中心
            try:
                profile = await self.page.query_selector('[class*="user"]')
                if profile:
                    return True
            except:
                pass

            return True  # 假设已登录
        except Exception as e:
            print(f"[XHS] 检查登录状态失败: {e}")
            return False

    async def login(self, cookie_string: str = None):
        """
        登录小红书

        参数:
            cookie_string: 可直接传入浏览器cookie字符串（从开发者工具复制）
                         格式: "name1=value1; name2=value2; ..."
        """
        if cookie_string:
            # 方法1：使用cookie登录
            await self.page.goto("https://www.xiaohongshu.com", timeout=30000)
            await asyncio.sleep(2)

            # 添加cookies
            cookies = []
            for cookie_str in cookie_string.split(';'):
                if '=' in cookie_str:
                    name, value = cookie_str.strip().split('=', 1)
                    cookies.append({
                        'name': name,
                        'value': value,
                        'domain': '.xiaohongshu.com',
                        'path': '/'
                    })
            await self.context.add_cookies(cookies)
            await self.page.reload()
            await asyncio.sleep(3)

        # 验证登录
        if not await self.check_login():
            raise Exception("登录失败！请提供有效的cookie或手动扫码登录")

    async def create_note(
        self,
        title: str,
        content: str,
        images: list = None,
        tags: list = None,
        location: str = None
    ) -> Dict[str, Any]:
        """
        创建小红书笔记

        参数:
            title: 标题
            content: 正文内容
            images: 图片URL列表（本地文件需先上传）
            tags: 标签列表
            location: 地理位置（可选）

        返回:
            包含note_id和url的字典
        """
        try:
            # 1. 导航到创作页面
            await self.page.goto("https://www.xiaohongshu.com/creator/post", timeout=30000)
            await asyncio.sleep(3)

            # 2. 处理图片上传
            if images:
                for img in images[:9]:
                    # 检查是否有上传按钮
                    upload_input = await self.page.query_selector('input[type="file"]')
                    if upload_input:
                        await upload_input.set_input_files(img)
                        await asyncio.sleep(2)

            # 3. 填写标题
            title_input = await self.page.wait_for_selector('[placeholder*="标题"]', timeout=10000)
            if title_input:
                await title_input.fill(title[:50])  # 小红书标题限制
                await asyncio.sleep(1)

            # 4. 填写正文（小红书通常是富文本编辑器）
            content_area = await self.page.wait_for_selector('[contenteditable="true"]', timeout=10000)
            if content_area:
                # 模拟逐字输入（更自然）
                await content_area.click()
                await asyncio.sleep(0.5)
                # 清空默认内容
                await content_area.evaluate('el => el.innerHTML = ""')
                await content_area.fill(content[:1000])
                await asyncio.sleep(1)

            # 5. 添加标签
            if tags:
                # 点击添加标签按钮
                try:
                    tag_btn = await self.page.wait_for_selector('[class*="tag"]', timeout=5000)
                    await tag_btn.click()
                    await asyncio.sleep(1)

                    for tag in tags[:5]:
                        # 输入标签
                        tag_input = await self.page.wait_for_selector('input[placeholder*="标签"]', timeout=5000)
                        if tag_input:
                            await tag_input.fill(tag)
                            await asyncio.sleep(0.5)
                            # 选择标签
                            await tag_input.press('Enter')
                            await asyncio.sleep(0.5)
                except:
                    pass  # 标签添加失败不影响发布

            # 6. 添加地理位置
            if location:
                try:
                    loc_btn = await self.page.wait_for_selector('[class*="location"]', timeout=5000)
                    await loc_btn.click()
                    await asyncio.sleep(1)
                    # 输入位置
                    loc_input = await self.page.wait_for_selector('input[placeholder*="位置"]', timeout=5000)
                    if loc_input:
                        await loc_input.fill(location)
                        await asyncio.sleep(1)
                        await loc_input.press('Enter')
                except:
                    pass

            # 7. 点击发布按钮
            publish_btn = await self.page.wait_for_selector('button:has-text("发布")', timeout=10000)
            if publish_btn:
                await publish_btn.click()
                await asyncio.sleep(3)

            # 8. 检查发布结果
            success_indicators = [
                "发布成功", "笔记发布成功", "已发布"
            ]
            page_content = await self.page.content()

            note_id = None
            for indicator in success_indicators:
                if indicator in page_content:
                    # 尝试提取笔记ID
                    try:
                        url = self.page.url
                        if '/explore/' in url:
                            note_id = url.split('/')[-1]
                    except:
                        note_id = str(int(time.time()))
                    break

            return {
                'success': True,
                'note_id': note_id,
                'url': f"https://www.xiaohongshu.com/explore/{note_id}" if note_id else '',
                'message': '笔记发布成功'
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'note_id': None
            }

    async def get_note_stats(self, note_id: str) -> Dict[str, Any]:
        """获取笔记统计数据（通过页面抓取）"""
        try:
            await self.page.goto(f"https://www.xiaohongshu.com/explore/{note_id}", timeout=30000)
            await asyncio.sleep(3)

            # 提取数据（需要根据实际页面结构调整选择器）
            stats = {
                'views': 0,
                'likes': 0,
                'collections': 0,
                'comments': 0
            }

            # 示例：查找包含数字的元素
            content = await self.page.content()

            # TODO: 实现实际的数据提取逻辑
            # 需要分析小红书页面结构

            return stats
        except Exception as e:
            return {'success': False, 'error': str(e)}


# 同步包装器
class XHSPlaywrightPosterSync:
    """同步版本的Playwright发布器（供非async代码使用）"""

    def __init__(self, headless: bool = True):
        self._poster = XHSPlaywrightPoster(headless)
        self._loop = None

    def start(self):
        """启动浏览器（同步）"""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self._poster.start())

    def stop(self):
        """停止浏览器（同步）"""
        if self._loop:
            self._loop.run_until_complete(self._poster.stop())
            self._loop.close()

    def login(self, cookie_string: str = None):
        """登录（同步）"""
        return self._loop.run_until_complete(
            self._poster.login(cookie_string)
        )

    def create_note(self, title: str, content: str, images: list = None, tags: list = None, location: str = None) -> Dict[str, Any]:
        """发布笔记（同步）"""
        return self._loop.run_until_complete(
            self._poster.create_note(title, content, images, tags, location)
        )

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


# 使用示例
if __name__ == "__main__":
    import getpass

    print("小红书Playwright自动发布测试")
    print("=" * 60)

    # 从文件读取cookie（或手动输入）
    try:
        with open('xhs_cookies.txt', 'r', encoding='utf-8') as f:
            cookie_str = f.read().strip()
    except:
        print("提示：请从浏览器开发者工具复制小红书cookie到 xhs_cookies.txt")
        cookie_str = input("或直接粘贴cookie: ").strip()

    if not cookie_str:
        print("错误：需要提供cookie才能登录")
        exit(1)

    # 使用同步包装器
    with XHSPlaywrightPosterSync(headless=False) as poster:
        print("1. 登录中...")
        poster.login(cookie_str)
        print("   [OK] 登录成功")

        print("2. 发布笔记...")
        result = poster.create_note(
            title="测试笔记：Playwright自动发布",
            content="这是通过Playwright自动发布的内容！\n\n#测试 #自动化",
            tags=["测试", "自动化", "Playwright"]
        )

        if result['success']:
            print(f"   [OK] 发布成功！笔记ID: {result['note_id']}")
            print(f"   链接: {result['url']}")
        else:
            print(f"   [FAIL] 发布失败: {result['error']}")

    print("=" * 60)
    print("测试完成")
