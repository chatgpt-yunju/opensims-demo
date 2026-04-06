import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, Menu
from main import OpenSimsDemo
import time
import json
from datetime import datetime

class OpenSimsGUI:
    """Tkinter图形界面 - 聊天模式为主"""

    def __init__(self):
        self.demo = OpenSimsDemo()
        self.root = tk.Tk()
        self.root.title("OpenSims - 模拟人生")
        self.root.geometry("800x600")

        # 加载或创建虚拟人
        self.setup_virtual_human()

        # 构建界面
        self.create_menu()
        self.create_widgets()

        # 刷新显示
        self.refresh_display()

        # 自动聚焦输入框
        self.input_entry.focus()

    def setup_virtual_human(self):
        """初始化虚拟人"""
        if not self.demo.load_or_create():
            # 弹出设置窗口
            self.show_setup_dialog()
        else:
            print(f"[GUI] 已加载虚拟人: {self.demo.vh.name}")

    def show_setup_dialog(self):
        """显示虚拟人创建对话框"""
        dialog = tk.Toplevel(self.root)
        dialog.title("创建虚拟人")
        dialog.geometry("300x200")
        dialog.transient(self.root)
        dialog.grab_set()

        tk.Label(dialog, text="虚拟人昵称:").pack(pady=5)
        name_entry = tk.Entry(dialog)
        name_entry.pack(pady=5)
        name_entry.insert(0, "小美")

        tk.Label(dialog, text="性格选择:").pack(pady=5)
        from config import PERSONALITY_PRESETS
        types = list(PERSONALITY_PRESETS.keys())
        type_var = tk.StringVar(value=types[0])
        type_combo = ttk.Combobox(dialog, textvariable=type_var, values=types, state="readonly")
        type_combo.pack(pady=5)

        def on_create():
            name = name_entry.get().strip() or "小美"
            ptype = type_var.get()
            self.demo.create_virtual_human(name, ptype)
            dialog.destroy()
            self.refresh_display()

        tk.Button(dialog, text="创建", command=on_create).pack(pady=10)

        dialog.wait_window()

    def create_menu(self):
        """创建菜单栏"""
        menubar = Menu(self.root)
        self.root.config(menu=menubar)

        # 文件菜单
        file_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="保存数据", command=self.save_data)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.root.quit)

        # 虚拟人菜单
        character_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="虚拟人", menu=character_menu)
        character_menu.add_command(label="重新设置虚拟人", command=self.reset_virtual_human)
        character_menu.add_command(label="查看状态", command=self.show_status)
        character_menu.add_command(label="列出所有虚拟人", command=self.list_all_virtual_humans)

        # 行动菜单
        action_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="行动", menu=action_menu)
        action_menu.add_command(label="吃饭", command=lambda: self.do_sim_action('eat'))
        action_menu.add_command(label="睡觉", command=lambda: self.do_sim_action('sleep'))
        action_menu.add_command(label="工作", command=lambda: self.do_sim_action('work'))
        action_menu.add_command(label="找工作", command=lambda: self.do_sim_action('find_job'))
        action_menu.add_command(label="娱乐", command=lambda: self.do_sim_action('relax'))
        action_menu.add_command(label="社交", command=lambda: self.do_sim_action('socialize'))
        action_menu.add_command(label="购物", command=lambda: self.do_sim_action('shop'))
        action_menu.add_separator()
        action_menu.add_command(label="结束今天", command=lambda: self.do_sim_action('day_pass'))
        action_menu.add_command(label="小红书发布", command=self.xiaohongshu_publish)

        # 聊天菜单
        chat_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="聊天", menu=chat_menu)
        chat_menu.add_command(label="清空聊天记录", command=self.clear_chat)
        chat_menu.add_command(label="与指定虚拟人聊天", command=self.chat_with_vh)
        chat_menu.add_separator()
        chat_menu.add_command(label="自动聊天设置", command=self.auto_chat_settings)
        # 保持BooleanVar引用，防止被垃圾回收
        self.auto_chat_var = tk.BooleanVar(value=self.demo.auto_chat_scheduler.running if self.demo.auto_chat_scheduler else False)
        chat_menu.add_checkbutton(label="启用自动聊天", variable=self.auto_chat_var, command=self.toggle_auto_chat)

        # 工具菜单
        tools_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="工具", menu=tools_menu)
        tools_menu.add_command(label="从掘金提取文章", command=self.extract_juejin)
        tools_menu.add_command(label="自动发布流程", command=self.auto_publish)
        tools_menu.add_separator()
        tools_menu.add_command(label="查看版本信息", command=self.show_version)

        # 帮助菜单
        help_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="关于", command=self.show_about)

    def create_widgets(self):
        """构建所有界面组件（聊天模式为主）"""
        # 顶部状态栏
        self.status_label = tk.Label(self.root, text="状态: ", anchor="w", font=("Consolas", 10))
        self.status_label.pack(fill=tk.X, padx=10, pady=5)

        # 分隔线
        ttk.Separator(self.root, orient='horizontal').pack(fill=tk.X)

        # 聊天显示区（主要区域）
        self.chat_frame = tk.Frame(self.root)
        self.chat_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.chat_text = scrolledtext.ScrolledText(self.chat_frame, wrap=tk.WORD, state='disabled', height=20)
        self.chat_text.pack(fill=tk.BOTH, expand=True)

        # 配置标签样式
        self.chat_text.tag_config('user', foreground='blue', font=('Arial', 10, 'bold'))
        self.chat_text.tag_config('assistant', foreground='green', font=('Arial', 10, 'bold'))
        self.chat_text.tag_config('system', foreground='gray', font=('Arial', 9, 'italic'))

        # 输入区
        input_frame = tk.Frame(self.root)
        input_frame.pack(fill=tk.X, padx=10, pady=5)

        self.input_entry = tk.Entry(input_frame, font=('Arial', 10))
        self.input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.input_entry.bind('<Return>', lambda e: self.send_message())
        self.input_entry.focus()

        send_btn = tk.Button(input_frame, text="发送", command=self.send_message, width=10)
        send_btn.pack(side=tk.RIGHT, padx=(5, 0))

        # 底部快捷按钮（保留一些常用操作）
        shortcut_frame = tk.Frame(self.root)
        shortcut_frame.pack(fill=tk.X, padx=10, pady=2)

        tk.Button(shortcut_frame, text="清空", command=self.clear_chat, width=8).pack(side=tk.LEFT, padx=2)
        tk.Button(shortcut_frame, text="查看状态", command=self.show_status, width=10).pack(side=tk.LEFT, padx=2)
        tk.Button(shortcut_frame, text="保存并退出", command=self.root.quit, width=10).pack(side=tk.RIGHT, padx=2)

    def refresh_display(self):
        """刷新界面显示"""
        if not self.demo.vh:
            return

        # 更新状态栏
        self.status_label.config(text=f"虚拟人: {self.demo.vh.name} | {self.demo.vh.get_status_text()}")

        # 重新加载聊天记录
        self.chat_text.config(state='normal')
        self.chat_text.delete(1.0, tk.END)

        for mem in self.demo.vh.memory:
            role = mem['role']
            content = mem['content']
            timestamp = time.strftime("%H:%M", time.localtime(mem['timestamp']))

            if role == 'user':
                self.chat_text.insert(tk.END, f"[{timestamp}] 你: ", 'user')
            else:
                self.chat_text.insert(tk.END, f"[{timestamp}] {self.demo.vh.name}: ", 'assistant')
            self.chat_text.insert(tk.END, f"{content}\n", role)

        self.chat_text.config(state='disabled')
        self.chat_text.see(tk.END)

    def send_message(self):
        """发送消息"""
        user_input = self.input_entry.get().strip()
        if not user_input:
            return

        # 显示用户消息
        self.chat_text.config(state='normal')
        timestamp = time.strftime("%H:%M")
        self.chat_text.insert(tk.END, f"[{timestamp}] 你: ", 'user')
        self.chat_text.insert(tk.END, f"{user_input}\n", 'user')
        self.chat_text.config(state='disabled')

        # 清空输入框
        self.input_entry.delete(0, tk.END)

        # 异步处理（简单版，实际会阻塞，但Demo可以接受）
        self.root.config(cursor="watch")
        self.root.update()

        try:
            reply = self.demo.chat(user_input)

            # 显示回复
            self.chat_text.config(state='normal')
            timestamp = time.strftime("%H:%M")
            self.chat_text.insert(tk.END, f"[{timestamp}] {self.demo.vh.name}: ", 'assistant')
            self.chat_text.insert(tk.END, f"{reply}\n", 'assistant')
            self.chat_text.config(state='disabled')
            self.chat_text.see(tk.END)

            # 刷新状态
            self.refresh_display()
        except Exception as e:
            messagebox.showerror("错误", f"发送失败: {e}")
        finally:
            self.root.config(cursor="")

    def clear_chat(self):
        """清空聊天显示"""
        self.chat_text.config(state='normal')
        self.chat_text.delete(1.0, tk.END)
        self.chat_text.config(state='disabled')

    def reset_virtual_human(self):
        """重置虚拟人"""
        if messagebox.askyesno("确认", "确定要重置虚拟人吗？数据将丢失。"):
            self.demo.storage.clear_data()
            # 清空agent_manager内存数据
            self.demo.agent_manager.virtual_humans.clear()
            self.demo.agent_manager.active_vh_id = None
            self.setup_virtual_human()
            self.refresh_display()

    def save_data(self):
        """保存所有数据"""
        try:
            self.demo.agent_manager.save_all()
            messagebox.showinfo("成功", "数据保存完成！")
        except Exception as e:
            messagebox.showerror("错误", f"保存失败: {e}")

    def show_status(self):
        """显示当前虚拟人状态"""
        if not self.demo.vh:
            messagebox.showwarning("警告", "没有可用的虚拟人")
            return
        status_text = self.demo.vh.get_status_full() if hasattr(self.demo.vh, 'get_status_full') else self.demo.vh.get_status_text()
        messagebox.showinfo(f"{self.demo.vh.name} 的状态", status_text)

    def list_all_virtual_humans(self):
        """列出所有虚拟人"""
        vhs = self.demo.agent_manager.list_virtual_humans()
        if not vhs:
            messagebox.showinfo("虚拟人列表", "当前没有虚拟人")
            return

        lines = []
        for vh_dict in vhs:
            active = " [当前]" if vh_dict.get('is_active', False) else ""
            player = " [玩家]" if vh_dict.get('is_player', False) else ""
            alive = "" if vh_dict.get('alive', True) else " 💀[已去世]"
            lines.append(f"{vh_dict['name']} ({vh_dict['id']}){active}{player}{alive}")
            if vh_dict.get('alive', True):
                age_val = vh_dict.get('age')
                if isinstance(age_val, (int, float)):
                    age_str = f"{age_val:.1f}"
                else:
                    age_str = str(age_val) if age_val is not None else "?"
                lines.append(f"  年龄: {age_str}, 职业: {vh_dict.get('job', '?')}, 金钱: ${vh_dict.get('money', '?')}")
            else:
                age_val = vh_dict.get('age')
                if isinstance(age_val, (int, float)):
                    age_str = f"{age_val:.1f}"
                else:
                    age_str = str(age_val) if age_val is not None else "?"
                lines.append(f"  享年: {age_str}岁, 死因: {vh_dict.get('death_cause','?')}")

        messagebox.showinfo("所有虚拟人", "\n".join(lines))

    def do_sim_action(self, action: str):
        """执行模拟人生行动"""
        if not self.demo.vh:
            messagebox.showwarning("警告", "没有可用的虚拟人")
            return

        if not hasattr(self.demo.vh, action):
            messagebox.showerror("错误", f"虚拟人无法执行: {action}")
            return

        try:
            method = getattr(self.demo.vh, action)
            result = method()
            self.refresh_display()
            messagebox.showinfo("行动结果", f"{self.demo.vh.name}: {result}")
        except Exception as e:
            messagebox.showerror("错误", f"行动失败: {e}")

    def xiaohongshu_publish(self):
        """小红书发布"""
        if not self.demo.vh:
            messagebox.showwarning("警告", "没有可用的虚拟人")
            return

        # 创建发布对话框
        dialog = tk.Toplevel(self.root)
        dialog.title("发布小红书笔记")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()

        tk.Label(dialog, text="标题:").pack(pady=5)
        title_entry = tk.Entry(dialog, width=40)
        title_entry.pack(pady=5)

        tk.Label(dialog, text="内容:").pack(pady=5)
        content_text = scrolledtext.ScrolledText(dialog, wrap=tk.WORD, height=8)
        content_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        tk.Label(dialog, text="标签 (逗号分隔):").pack(pady=5)
        tags_entry = tk.Entry(dialog, width=40)
        tags_entry.pack(pady=5)

        def on_publish():
            title = title_entry.get().strip()
            content = content_text.get(1.0, tk.END).strip()
            tags_str = tags_entry.get().strip()
            tags = [t.strip() for t in tags_str.split(',')] if tags_str else []

            if not title or not content:
                messagebox.showwarning("警告", "标题和内容不能为空")
                return

            try:
                result = self.demo.vh.create_xiaohongshu_post(title, content, tags=tags)
                dialog.destroy()
                messagebox.showinfo("发布结果", result)
                self.refresh_display()
            except Exception as e:
                messagebox.showerror("错误", f"发布失败: {e}")

        btn_frame = tk.Frame(dialog)
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="发布", command=on_publish, width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="取消", command=dialog.destroy, width=10).pack(side=tk.RIGHT, padx=5)

        dialog.wait_window()

    def chat_with_vh(self):
        """与指��虚拟人聊天"""
        vhs = self.demo.agent_manager.list_virtual_humans()
        if len(vhs) < 2:
            messagebox.showinfo("提示", "需要至少2个虚拟人才能切换对话对象")
            return

        # 创建选择对话框
        dialog = tk.Toplevel(self.root)
        dialog.title("选择聊天对象")
        dialog.geometry("300x200")
        dialog.transient(self.root)
        dialog.grab_set()

        tk.Label(dialog, text="选择虚拟人:").pack(pady=10)
        vh_ids = [(vh['id'], vh['name']) for vh in vhs if vh['id'] != self.demo.agent_manager.active_vh_id]
        if not vh_ids:
            messagebox.showinfo("提示", "没有其他虚拟人可选")
            dialog.destroy()
            return

        id_var = tk.StringVar(value=vh_ids[0][0])
        combo = ttk.Combobox(dialog, textvariable=id_var, values=[f"{id_} - {name}" for id_, name in vh_ids], state="readonly", width=30)
        combo.pack(pady=10)

        def on_select():
            target_id = id_var.get().split(' - ')[0]
            dialog.destroy()
            # 切换到目标虚拟人
            self.demo.select_virtual_human(target_id)
            self.refresh_display()
            messagebox.showinfo("切换成功", f"已切换到: {self.demo.vh.name}")

        tk.Button(dialog, text="选择", command=on_select, width=10).pack(pady=10)
        dialog.wait_window()

    def auto_chat_settings(self):
        """自动聊天设置"""
        dialog = tk.Toplevel(self.root)
        dialog.title("自动聊天设置")
        dialog.geometry("300x150")
        dialog.transient(self.root)

        tk.Label(dialog, text="自动聊天功能配置").pack(pady=10)

        from config import AUTO_CHAT_ENABLED, AUTO_CHAT_INTERVAL, AUTO_CHAT_PROBABILITY
        tk.Label(dialog, text=f"当前状态: {'启用' if AUTO_CHAT_ENABLED else '禁用'}").pack()
        tk.Label(dialog, text=f"检查间隔: {AUTO_CHAT_INTERVAL}秒").pack()
        tk.Label(dialog, text=f"触发概率: {AUTO_CHAT_PROBABILITY*100:.0f}%").pack()

        messagebox.showinfo("说明", "自动聊天设置请修改config.py文件中的配置")

    def toggle_auto_chat(self):
        """切换自动聊天开关（临时）"""
        # 注意：实际需要在config中修改并重启调度器
        messagebox.showinfo("提示", "请通过config.py配置自动聊天，或重启程序")

    def extract_juejin(self):
        """从掘金提取文章"""
        dialog = tk.Toplevel(self.root)
        dialog.title("从掘金提取文章")
        dialog.geometry("400x150")
        dialog.transient(self.root)
        dialog.grab_set()

        tk.Label(dialog, text="掘金文章URL:").pack(pady=5)
        url_entry = tk.Entry(dialog, width=50)
        url_entry.pack(pady=5)
        url_entry.insert(0, "https://juejin.cn/post/")

        def on_extract():
            url = url_entry.get().strip()
            if not url:
                messagebox.showerror("错误", "请输入有效的URL")
                return

            dialog.config(cursor="watch")
            dialog.update()

            try:
                import asyncio
                from juejin_extractor import JuejinExtractor

                extractor = JuejinExtractor()
                result = asyncio.run(extractor.extract_article(url))

                if result.get('success'):
                    # 显示结果摘要
                    summary = f"标题: {result.get('title', 'N/A')}\n作者: {result.get('author', 'N/A')}\n字数: {len(result.get('content', ''))}\n标签: {', '.join(result.get('tags', []))}"
                    messagebox.showinfo("提取成功", summary)

                    # 询问是否保存
                    if messagebox.askyesno("保存", "将提取的文章保存为TXT文件吗？"):
                        from datetime import datetime
                        filename = f"juejin_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                        with open(filename, 'w', encoding='utf-8') as f:
                            f.write(f"标题: {result.get('title', '')}\n")
                            f.write(f"作者: {result.get('author', '')}\n")
                            f.write(f"发布时间: {result.get('publish_time', '')}\n")
                            f.write(f"标签: {', '.join(result.get('tags', []))}\n")
                            f.write(f"阅读: {result.get('stats', {}).get('views', 0)} 点赞: {result.get('stats', {}).get('likes', 0)}\n")
                            f.write("="*50 + "\n\n")
                            f.write(result.get('content', ''))
                        messagebox.showinfo("保存成功", f"已保存至: {filename}")
                else:
                    messagebox.showerror("提取失败", result.get('error', '未知错误'))

            except Exception as e:
                messagebox.showerror("错误", f"提取失败: {e}")
            finally:
                dialog.config(cursor="")
                dialog.update()

        tk.Button(dialog, text="提取", command=on_extract, width=10).pack(pady=10)
        dialog.wait_window()

    def auto_publish(self):
        """自动发布流程"""
        if not self.demo.vh:
            messagebox.showwarning("警告", "没有可用的虚拟人")
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("自动发布：掘金→小红书")
        dialog.geometry("400x200")
        dialog.transient(self.root)
        dialog.grab_set()

        tk.Label(dialog, text="掘金文章URL:").pack(pady=5)
        url_entry = tk.Entry(dialog, width=50)
        url_entry.pack(pady=5)
        url_entry.insert(0, "https://juejin.cn/post/")

        tk.Label(dialog, text="重写风格:").pack(pady=5)
        style_var = tk.StringVar(value="xiaohongshu")
        style_combo = ttk.Combobox(dialog, textvariable=style_var, values=["xiaohongshu", "official", "casual"], state="readonly", width=20)
        style_combo.pack(pady=5)

        def on_publish():
            url = url_entry.get().strip()
            style = style_var.get()

            if not url:
                messagebox.showerror("错误", "请输入URL")
                return

            dialog.config(cursor="watch")
            dialog.update()

            try:
                from auto_publisher import AutoPublisher
                publisher = AutoPublisher()

                result = publisher.publish_from_juejin(
                    juejin_url=url,
                    xhs_character_id=str(self.demo.vh.id),
                    rewrite_style=style,
                    publish_immediately=True
                )

                if result.get('success'):
                    msg = f"发布成功！\n标题: {result.get('xhs_title', 'N/A')}\n笔记ID: {result.get('xhs_note_id', 'N/A')}"
                    messagebox.showinfo("完成", msg)
                else:
                    messagebox.showerror("失败", f"错误: {result.get('error', '未知错误')}")

            except Exception as e:
                messagebox.showerror("错误", f"自动发布失败: {e}")
            finally:
                dialog.config(cursor="")
                dialog.update()

        tk.Button(dialog, text="开始发布", command=on_publish, width=15).pack(pady=10)
        dialog.wait_window()

    def show_version(self):
        """显示版本信息"""
        try:
            with open('version.json', 'r', encoding='utf-8') as f:
                ver_data = json.load(f)

            version = f"{ver_data['major']}.{ver_data['minor']}.{ver_data['patch']}.{ver_data['build']}"
            info = f"OpenSims 版本: {version}\n"
            info += f"构建时间: {ver_data['last_updated']}\n\n"
            info += "功能列表:\n"
            info += "  - 模拟人生核心系统\n"
            info += "  - AI虚拟人聊天\n"
            info += "  - 自动聊天调度\n"
            info += "  - 小红书发布（模拟/官方API/Playwright）\n"
            info += "  - 掘金文章提取\n"
            info += "  - MCP技能接口"

            messagebox.showinfo("版本信息", info)
        except Exception as e:
            messagebox.showerror("错误", f"无法读取版本信息: {e}")

    def show_about(self):
        """关于对话框"""
        about_text = """OpenSims - 模拟人生系统

版本: 1.0.0
构建: 自动版本管理

这是一个虚拟人生模拟系统，支持：
- 创建和管理多个虚拟人
- 模拟人生各个阶段
- AI对话和自动互动
- 工具集成（小红书、掘金等）

技术栈：
Python 3.10+, Tkinter, Playwright, FastAPI, MCP

Copyright 2025 OpenSims Team"""
        messagebox.showinfo("关于", about_text)

    def run(self):
        """启动GUI主循环"""
        self.root.mainloop()

if __name__ == "__main__":
    gui = OpenSimsGUI()
    gui.run()