#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小红书开放平台API客户端
文档：https://open.xiaohongshu.com/
"""

import time
import json
import hashlib
import hmac
import base64
import requests
from typing import Dict, Any, Optional
from config import XIAOHONGSHU_CONFIG

class XHSAPIError(Exception):
    """小红书API错误"""
    pass

class XHSClient:
    """小红书开放平台API客户端"""

    def __init__(self):
        self.app_id = XIAOHONGSHU_CONFIG["app_id"]
        self.app_secret = XIAOHONGSHU_CONFIG["app_secret"]
        self.access_token = XIAOHONGSHU_CONFIG["access_token"]
        self.api_endpoint = XIAOHONGSHU_CONFIG["api_endpoint"]
        self.enabled = XIAOHONGSHU_CONFIG["api_enabled"]

        if not self.enabled:
            print("[XHS] 小红书API未启用（使用模拟模式）")
            return

        if not all([self.app_id, self.app_secret, self.access_token]):
            print("[XHS] 警告：小红书API配置不完整，请设置app_id、app_secret、access_token")
            self.enabled = False
            return

        print(f"[XHS] 小红书API客户端已初始化 (App ID: {self.app_id})")

    def _sign(self, method: str, path: str, params: Dict = None, data: Dict = None) -> str:
        """
        生成小红书API签名
        签名算法：HMAC-SHA256
        """
        # 构建待签名字符串
        timestamp = str(int(time.time()))
        nonce = str(hashlib.md5(str(time.time()).encode()).hexdigest()[:32])

        # 参数排序
        all_params = {}
        if params:
            all_params.update(params)
        if data:
            all_params.update(data)
        all_params['access_token'] = self.access_token
        all_params['app_key'] = self.app_id
        all_params['timestamp'] = timestamp
        all_params['nonce'] = nonce

        # 按键名字典序排序
        sorted_keys = sorted(all_params.keys())
        sign_str = method.upper() + path
        for key in sorted_keys:
            sign_str += key + str(all_params[key])

        # HMAC-SHA256签名
        signature = hmac.new(
            self.app_secret.encode('utf-8'),
            sign_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        return signature

    def _request(self, method: str, endpoint: str, params: Dict = None, data: Dict = None) -> Dict:
        """发送HTTP请求到小红书API"""
        if not self.enabled:
            raise XHSAPIError("小红书API未启用")

        url = self.api_endpoint + endpoint
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'app-key': self.app_id,
            'signature': self._sign(method, endpoint, params, data),
            'timestamp': str(int(time.time())),
            'nonce': hashlib.md5(str(time.time()).encode()).hexdigest()[:32],
            'access-token': self.access_token
        }

        try:
            if method.upper() == 'GET':
                response = requests.get(url, params=params, headers=headers, timeout=10)
            elif method.upper() == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            else:
                raise XHSAPIError(f"不支持的HTTP方法: {method}")

            response.raise_for_status()
            result = response.json()

            if result.get('code') != 0:
                error_msg = result.get('msg', 'Unknown error')
                raise XHSAPIError(f"小红书API错误: {error_msg}")

            return result.get('data', {})

        except requests.RequestException as e:
            raise XHSAPIError(f"网络请求失败: {str(e)}")

    def publish_note(self, title: str, content: str, images: list = None, tags: list = None) -> Dict[str, Any]:
        """
        发布小红书笔记

        参数:
            title: 标题
            content: 正文内容
            images: 图片列表（可选），每个元素是图片URL或本地路径
            tags: 标签列表（可选）

        返回:
            包含笔记ID、状态等信息的字典
        """
        if not self.enabled:
            raise XHSAPIError("小红书API未启用")

        # 构建笔记数据
        note_data = {
            'title': title[:XIAOHONGSHU_CONFIG['max_title_length']],
            'content': content[:XIAOHONGSHU_CONFIG['max_content_length']],
            'topic_list': tags or [],
            'image_list': [],
            'video_info': None,
            'location': None,  # 可选：地理位置
            'is_private': False,  # 是否私密
            'post_time': None,  # 可选：定时发布时间（时间戳）
        }

        # 处理图片
        if images:
            for img in images[:9]:  # 小红书上限9张图
                if img.startswith('http'):
                    # 外部图片URL - 需要先下载上传到小红书CDN？
                    # 小红书API可能需要先上传图片获取image_id
                    # 这里简化：直接传URL（可能不工作，需根据实际API调整）
                    note_data['image_list'].append({'url': img, 'image_type': 1})
                else:
                    # 本地图片路径 - 需要上传
                    # TODO: 实现图片上传逻辑
                    pass

        # 调用发布接口
        # 实际API endpoint可能是 /api/gxapi/note/publish 或类似
        endpoint = 'note/publish'  # 需要根据小红书开放平台实际文档调整

        try:
            result = self._request('POST', endpoint, data=note_data)
            return {
                'success': True,
                'note_id': result.get('note_id') or result.get('id'),
                'url': result.get('url', ''),
                'message': '笔记发布成功'
            }
        except XHSAPIError as e:
            return {
                'success': False,
                'error': str(e),
                'note_id': None
            }

    def get_note_stats(self, note_id: str) -> Dict[str, Any]:
        """获取笔记数据（阅读、点赞、收藏等）"""
        if not self.enabled:
            raise XHSAPIError("小红书API未启用")

        endpoint = f'note/detail/{note_id}'
        try:
            result = self._request('GET', endpoint)
            return {
                'success': True,
                'views': result.get('view_count', 0),
                'likes': result.get('like_count', 0),
                'collections': result.get('collect_count', 0),
                'comments': result.get('comment_count', 0),
                'share': result.get('share_count', 0)
            }
        except XHSAPIError as e:
            return {
                'success': False,
                'error': str(e)
            }

    def get_user_stats(self) -> Dict[str, Any]:
        """获取博主数据（粉丝数、笔记总数等）"""
        if not self.enabled:
            raise XHSAPIError("小红书API未启用")

        endpoint = 'user/info'
        try:
            result = self._request('GET', endpoint)
            return {
                'success': True,
                'followers': result.get('fans_count', 0),
                'following': result.get('follow_count', 0),
                'posts': result.get('note_count', 0),
                'likes_received': result.get('like_count', 0)
            }
        except XHSAPIError as e:
            return {
                'success': False,
                'error': str(e)
            }

    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        刷新Access Token
        需要提供refresh_token（来自首次授权）
        """
        if not self.enabled:
            raise XHSAPIError("小红书API未启用")

        endpoint = 'oauth/refresh_token'
        data = {
            'refresh_token': refresh_token,
            'app_id': self.app_id,
            'secret': self.app_secret
        }

        try:
            result = self._request('POST', endpoint, data=data)
            self.access_token = result.get('access_token')
            return {
                'success': True,
                'access_token': self.access_token,
                'expires_in': result.get('expires_in')
            }
        except XHSAPIError as e:
            return {
                'success': False,
                'error': str(e)
            }


# 全局客户端实例
_xhs_client = None

def get_xhs_client() -> XHSClient:
    """获取小红书API客户端（单例）"""
    global _xhs_client
    if _xhs_client is None:
        _xhs_client = XHSClient()
    return _xhs_client
