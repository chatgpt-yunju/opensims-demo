#!/usr/bin/env python3
"""
生成OpenSims图标（PNG转ICO）
需要: pip install Pillow
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_icon(size=256, output='static/icon.ico'):
    """创建简单图标"""
    # 创建图像
    img = Image.new('RGB', (size, size), color='#4A90D9')
    draw = ImageDraw.Draw(img)

    # 绘制"OS"字母
    try:
        # 尝试使用系统字体
        font = ImageFont.truetype("arial.ttf", size // 3)
    except:
        font = ImageFont.load_default()

    text = "OS"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    position = ((size - text_w) // 2, (size - text_h) // 2)
    draw.text(position, text, fill='white', font=font)

    # 保存ICO
    if not os.path.exists('static'):
        os.makedirs('static')
    img.save(output, format='ICO', sizes=[(size, size)])
    print(f"[OK] 图标已创建: {output}")

if __name__ == "__main__":
    create_icon()
