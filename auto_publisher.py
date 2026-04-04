#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
掘金→小红书自动发布系统
完整流程：抓取掘金文章 → AI改写为小红书风格 → 自动发布
"""

import time
import json
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

# 导入已有模块
from juejin_extractor import JuejinExtractorSync
from xhs_playwright import XHSPlaywrightPosterSync
from api_client import APIClient
from config import XIAOHONGSHU_CONFIG, PERSONALITY_PRESETS

class AutoPublisher:
    """自动发布器：掘金 → 小红书"""

    def __init__(
        self,
        xhs_cookie_path: str = "xhs_cookies.txt",
        use_playwright: bool = True,
        headless: bool = True,
        api_client: APIClient = None
    ):
        """
        初始化自动发布器

        参数:
            xhs_cookie_path: 小红书cookie文件路径
            use_playwright: 是否使用Playwright发布（True）或官方API（False）
            headless: 是否无头模式
            api_client: AI API客户端（用于内容改写）
        """
        self.xhs_cookie_path = xhs_cookie_path
        self.use_playwright = use_playwright
        self.headless = headless
        self.api_client = api_client or APIClient()

        # 检查cookie文件
        import os
        if use_playwright and not os.path.exists(xhs_cookie_path):
            print(f"[警告] 小红书cookie文件不存在: {xhs_cookie_path}")
            print("  请先获取cookie并保存到该文件")
            self.use_playwright = False

    def publish_from_juejin(
        self,
        juejin_url: str,
        xhs_character_id: str = None,
        rewrite_style: str = "xiaohongshu",
        publish_immediately: bool = True
    ) -> Dict[str, Any]:
        """
        从掘金文章自动发布到小红书

        完整流程：
        1. 提取掘金文章内容
        2. AI改写为小红书风格（可选）
        3. 发布到小红书

        参数:
            juejin_url: 掘金文章URL
            xhs_character_id: 小红书博主角色ID（OpenSims内）
            rewrite_style: 改写风格（xiaohongshu/keep_original）
            publish_immediately: 是否立即发布（否则只生成不发布）

        返回:
            包含发布结果的字典
        """
        results = {
            'success': False,
            'juejin': {},
            'xhs_note': {},
            'publish_result': None,
            'errors': []
        }

        print("=" * 60)
        print("自动发布流程开始")
        print("=" * 60)

        # 步骤1：提取掘金文章
        print("\n[步骤1/3] 提取掘金文章内容...")
        try:
            extractor = JuejinExtractorSync(headless=True)
            juejin_data = extractor.extract(juejin_url)

            if not juejin_data.get('success'):
                results['errors'].append(f"提取失败: {juejin_data.get('error')}")
                return results

            results['juejin'] = juejin_data
            print(f"  [OK] 标题: {juejin_data['title'][:50]}...")
            print(f"  [OK] 作者: {juejin_data['author'].get('name', '未知')}")
            print(f"  [OK] 正文: {len(juejin_data['content'])} 字符")
            print(f"  [OK] 标签: {', '.join(juejin_data['tags'][:5])}")

        except Exception as e:
            results['errors'].append(f"提取异常: {str(e)}")
            return results

        # 步骤2：改写为小红书风格
        print("\n[步骤2/3] 转换为小红书风格...")
        try:
            xhs_content = self._rewrite_to_xiaohongshu(
                juejin_data,
                style=rewrite_style
            )
            results['xhs_note'] = xhs_content
            print(f"  [OK] 新标题: {xhs_content['title'][:50]}...")
            print(f"  [OK] 新标签: {', '.join(xhs_content['tags'])}")
            print(f"  [OK] 正文: {len(xhs_content['content'])} 字符")

        except Exception as e:
            results['errors'].append(f"改写失败: {str(e)}")
            # 即使改写失败，使用原文继续
            print("  [!] 改写失败，使用原文继续...")
            results['xhs_note'] = {
                'title': juejin_data['title'],
                'content': self._convert_markdown_to_xhs(juejin_data['content']),
                'tags': juejin_data['tags'][:5] if juejin_data['tags'] else ['技术', '分享'],
                'images': []
            }

        # 步骤3：发布到小红书
        if publish_immediately:
            print("\n[步骤3/3] 发布到小红书...")
            try:
                publish_result = self._publish_to_xiaohongshu(
                    xhs_note=results['xhs_note'],
                    character_id=xhs_character_id
                )
                results['publish_result'] = publish_result

                if publish_result.get('success'):
                    print(f"  [OK] 发布成功！")
                    print(f"    Note ID: {publish_result.get('note_id', 'unknown')}")
                    print(f"    链接: {publish_result.get('url', '无')}")
                else:
                    results['errors'].append(f"发布失败: {publish_result.get('error')}")

            except Exception as e:
                results['errors'].append(f"发布异常: {str(e)}")
        else:
            print("\n[步骤3/3] 跳过发布（仅生成内容）")

        results['success'] = len(results['errors']) == 0
        print("\n" + "=" * 60)
        if results['success']:
            print("[OK] 自动发布流程完成")
        else:
            print(f"[FAIL] 流程失败: {', '.join(results['errors'])}")
        print("=" * 60)

        return results

    def _rewrite_to_xiaohongshu(
        self,
        juejin_data: Dict[str, Any],
        style: str = "xiaohongshu"
    ) -> Dict[str, Any]:
        """
        将掘金文章改写为小红书风格

        策略：
        1. 标题重构（更活泼、带emoji）
        2. 正文精简（小红书风格，段落短）
        3. 标签优化（换成小红书热门标签）
        4. 图片提取（后续扩展）
        """
        # 暂时只使用模板改写（避免API调用问题）
        # TODO: 集成真实AI改写（需要配置API_KEY）
        return self._template_rewrite(juejin_data, style)

    def _ai_rewrite(self, juejin_data: Dict[str, Any], style: str) -> Dict[str, Any]:
        """使用AI API改写"""
        prompt = f"""
你是小红书博主，需要将以下技术文章改写为小红书笔记。

原文信息：
- 标题：{juejin_data['title']}
- 正文：{juejin_data['content'][:2000]}  # 限制长度
- 原标签：{', '.join(juejin_data.get('tags', []))}

改写要求：
1. 标题：15-20字，吸引眼球，可加emoji（如[Fire]、[Idea]、[Rocket]）
2. 正文：300-800字，口语化，轻松活泼
   - 段落简短（每段2-4行）
   - 适当使用emoji点缀
   - 加入个人感受和呼吁互动
3. 标签：3-5个，小红书热门技术标签如：#程序员 #技术分享 #AI #开源 #干货
4. 去掉代码块或简化代码，如果包含代码请简化并加说明

输出格式（JSON）：
{{
  "title": "新标题",
  "content": "正文内容",
  "tags": ["标签1", "标签2", "标签3"]
}}
"""

        response = self.api_client._api_generate(None, prompt)
        # 解析JSON响应（简化：实际需处理）
        import re
        json_match = re.search(r'\{.*\}', response.get('reply', ''), re.DOTALL)
        if json_match:
            try:
                result = json.loads(json_match.group())
                return {
                    'title': result.get('title', juejin_data['title'])[:XIAOHONGSHU_CONFIG['max_title_length']],
                    'content': result.get('content', '')[:XIAOHONGSHU_CONFIG['max_content_length']],
                    'tags': result.get('tags', [])[:XIAOHONGSHU_CONFIG['max_tags']],
                    'images': []
                }
            except:
                pass

        raise Exception("AI改写解析失败")

    def _template_rewrite(self, juejin_data: Dict[str, Any], style: str) -> Dict[str, Any]:
        """模板规则改写（无API时使用）"""
        original_title = juejin_data['title']
        original_content = juejin_data['content']
        original_tags = juejin_data.get('tags', [])

        # 标题模板
        title_templates = [
            f"[Fire]{original_title[:15]}，新手必看！",
            f"[Idea]{original_title[:12]}：我的实战经验分享",
            f"[Rocket]{original_title[:10]}，不看后悔！",
            f"[Star]{original_title[:15]}干货满满"
        ]

        import random
        new_title = random.choice(title_templates)

        # 正文转换（精简+分段落）
        new_content = self._convert_markdown_to_xhs(original_content)

        # 标签映射（技术类通用）
        xhs_tag_map = {
            '前端': ['前端开发', 'Web开发', '前端工程师'],
            '后端': ['后端开发', '后端工程师', 'Java', 'Python'],
            'AI': ['AI', '人工智能', '机器学习', '深度学习'],
            'JavaScript': ['JavaScript', 'JS', '前端开发'],
            'React': ['React', 'ReactJS', '前端框架'],
            'Vue': ['Vue.js', 'Vue', '前端'],
            '编程': ['程序员', '编程', '代码', '开发'],
            '技术': ['技术', '科技', '极客', 'Geek']
        }

        new_tags = ['技术分享', '程序员日常']  # 默认标签
        for tag in original_tags:
            for key, values in xhs_tag_map.items():
                if key in tag or tag in key:
                    new_tags.extend(values[:2])
                    break
        new_tags = list(set(new_tags))[:XIAOHONGSHU_CONFIG['max_tags']]

        return {
            'title': new_title,
            'content': new_content,
            'tags': new_tags,
            'images': []  # TODO: 提取或生成封面图
        }

    def _convert_markdown_to_xhs(self, content: str) -> str:
        """
        将Markdown内容转换为小红书风格
        - 拆分长段落
        - 去掉代码块或简化
        - 添加分隔符和emoji
        """
        lines = content.split('\n')
        result_lines = []
        in_code_block = False
        code_buffer = []

        for line in lines:
            line = line.strip()

            # 处理代码块
            if line.startswith('```'):
                if in_code_block:
                    # 代码块结束
                    if code_buffer:
                        # 简化输出：只保留第一行和最后一行
                        result_lines.append(f"[Code] 代码片段（已简化）：")
                        result_lines.append(code_buffer[0][:50] + "...")
                    code_buffer = []
                in_code_block = not in_code_block
                continue

            if in_code_block:
                code_buffer.append(line)
                continue

            # 跳过空行
            if not line:
                if result_lines and result_lines[-1]:
                    result_lines.append("")
                continue

            # 处理标题
            if line.startswith('#'):
                level = len(line) - len(line.lstrip('#'))
                title = line.lstrip('#').strip()
                if level <= 3:
                    result_lines.append(f"\n{title}\n{'·' * len(title)}\n")
                else:
                    result_lines.append(f"[Loc] {title}")
                continue

            # 处理列表
            if line.startswith(('-', '*', '1.', '2.', '3.')):
                item = line[1:].strip() if line[0] in ['-', '*'] else line.split('.', 1)[1].strip()
                result_lines.append(f"  [Star] {item}")
                continue

            # 普通段落
            if len(line) > 100:
                # 拆分长段落
                words = list(line)
                chunks = [' '.join(words[i:i+50]) for i in range(0, len(words), 50)]
                for chunk in chunks:
                    result_lines.append(chunk)
            else:
                result_lines.append(line)

        # 添加结尾互动
        if result_lines:
            result_lines.append("\n" + "="*40)
            result_lines.append("\n[Comment] 欢迎评论区交流讨论！")
            result_lines.append("[Eye] 如果对你有帮助，记得点赞收藏哦～")
            result_lines.append("[Bell] 关注我，获取更多技术干货！")

        return '\n'.join(filter(None, result_lines))

    def _publish_to_xiaohongshu(
        self,
        xhs_note: Dict[str, Any],
        character_id: str = None
    ) -> Dict[str, Any]:
        """
        发布到小红书

        支持两种方式：
        1. 通过OpenSims API（需要web_api.py运行）
        2. 直接使用Playwright（需要cookie）
        """
        # 方式1：通过OpenSims API
        if character_id and self._check_api_available():
            try:
                import requests
                resp = requests.post(
                    f"http://localhost:8000/api/v1/characters/{character_id}/actions/create_xiaohongshu_post",
                    json={
                        'title': xhs_note['title'],
                        'content': xhs_note['content'],
                        'tags': xhs_note['tags'],
                        'images': xhs_note.get('images', []),
                        'use_playwright': self.use_playwright
                    },
                    timeout=30
                )

                if resp.status_code == 200:
                    result = resp.json()
                    return {
                        'success': result.get('success', False),
                        'note_id': result.get('state', {}).get('xiaohongshu', {}).get('posts_published', 0),
                        'url': result.get('state', {}).get('xiaohongshu', {}).get('note_url', ''),
                        'message': result.get('message', '')
                    }
                else:
                    return {
                        'success': False,
                        'error': f"HTTP {resp.status_code}: {resp.text}"
                    }

            except Exception as e:
                print(f"[警告] API发布失败，尝试直接Playwright: {e}")

        # 方式2：直接Playwright（需要cookie）
        if self.use_playwright:
            try:
                with XHSPlaywrightPosterSync(headless=self.headless) as poster:
                    # 登录
                    with open(self.xhs_cookie_path, 'r', encoding='utf-8') as f:
                        cookie_str = f.read().strip()
                    poster.login(cookie_str)

                    # 发布
                    result = poster.create_note(
                        title=xhs_note['title'],
                        content=xhs_note['content'],
                        images=xhs_note.get('images', []),
                        tags=xhs_note['tags']
                    )

                    return result

            except Exception as e:
                return {
                    'success': False,
                    'error': f"Playwright发布失败: {str(e)}"
                }

        return {
            'success': False,
            'error': "没有可用的发布方式（未配置API或Playwright）"
        }

    def _check_api_available(self) -> bool:
        """检查OpenSims API是否可用"""
        try:
            import requests
            resp = requests.get("http://localhost:8000/api/v1/system/status", timeout=2)
            return resp.status_code == 200
        except:
            return False

    def batch_publish(
        self,
        juejin_urls: List[str],
        xhs_character_id: str = None,
        interval: int = 300  # 间隔5分钟
    ) -> List[Dict[str, Any]]:
        """
        批量自动发布

        参数:
            juejin_urls: 掘金文章URL列表
            xhs_character_id: 小红书博主角色ID
            interval: 发布间隔（秒，建议300+避免风控）

        返回:
            每次发布结果列表
        """
        results = []
        total = len(juejin_urls)

        print(f"开始批量发布: {total} 篇文章，间隔 {interval}秒")

        for i, url in enumerate(juejin_urls, 1):
            print(f"\n[{i}/{total}] 处理: {url}")

            result = self.publish_from_juejin(
                juejin_url=url,
                xhs_character_id=xhs_character_id,
                publish_immediately=True
            )
            results.append(result)

            # 间隔等待（避免风控）
            if i < total:
                print(f"  等待 {interval} 秒...")
                time.sleep(interval)

        return results

    def generate_content_only(
        self,
        juejin_url: str,
        output_format: str = 'txt'
    ) -> Dict[str, Any]:
        """
        仅生成小红书内容，不发布

        返回改写后的内容并保存
        """
        result = self.publish_from_juejin(
            juejin_url=juejin_url,
            publish_immediately=False
        )

        if result['success']:
            # 保存到文件
            import json
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            article_id = result['juejin'].get('article_id', 'unknown')

            if output_format == 'json':
                filename = f"xhs_content_{article_id}_{timestamp}.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
            else:
                filename = f"xhs_content_{article_id}_{timestamp}.txt"
                content = f"""标题：{result['xhs_note']['title']}

标签：{', '.join(result['xhs_note']['tags'])}

正文：
{result['xhs_note']['content']}

原始链接���{result['juejin'].get('url', '')}
生成时间：{datetime.now().isoformat()}
"""
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)

            print(f"[OK] 内容已保存: {filename}")
            result['output_file'] = filename

        return result


# 命令行使用
if __name__ == "__main__":
    import sys

    print("=" * 60)
    print("掘金→小红书自动发布系统")
    print("=" * 60)

    # 参数解析
    if len(sys.argv) < 2:
        print("""
用法:
  python auto_publisher.py <juejin_url> [character_id] [--dry-run]

示例:
  # 仅生成内容（不发布）
  python auto_publisher.py https://juejin.cn/post/123456 --dry-run

  # 生成并发布（需要已配置cookie或API）
  python auto_publisher.py https://juejin.cn/post/123456 abc123

  # 批量发布
  python auto_publisher.py batch urls.txt abc123
""")
        sys.exit(1)

    url = sys.argv[1]
    character_id = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith('--') else None
    dry_run = '--dry-run' in sys.argv

    # 创建发布器
    publisher = AutoPublisher(
        use_playwright=True,  # 默认使用Playwright（需要cookie）
        headless=True
    )

    if dry_run:
        print("[模式] 仅生成内容（不发布）")
        result = publisher.generate_content_only(url, output_format='txt')
    else:
        print("[模式] 生成并发布")
        result = publisher.publish_from_juejin(
            juejin_url=url,
            xhs_character_id=character_id,
            publish_immediately=True
        )

    # 输出结果摘要
    if result['success']:
        print("\n[OK] 流程成功")
        print(f"   掘金文章: {result['juejin']['title'][:50]}")
        print(f"   小红书标题: {result['xhs_note']['title'][:50]}")
        if result.get('publish_result'):
            print(f"   发布状态: {'成功' if result['publish_result'].get('success') else '失败'}")
    else:
        print("\n[FAIL] 流程失败")
        for error in result['errors']:
            print(f"   - {error}")

    print("=" * 60)
