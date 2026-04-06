import tkinter as tk
from tkinter import ttk, scrolledtext, Menu, messagebox
from main import OpenSimsDemo
import threading
import time
import sys
import os
from datetime import datetime

# 动态导入 settings（支持PyInstaller）
try:
    import settings as gui_settings
except ImportError:
    # 添加当前目录到路径并重试
    current_dir = os.path.dirname(os.path.abspath(__file__)) or '.'
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    import settings as gui_settings

class MentorChatGUI:
    """极简导师对话GUI - 只保留核心对话功能"""

    def __init__(self):
        self.demo = OpenSimsDemo()
        self.root = tk.Tk()
        self.root.title("OpenSims - 导师对话")
        self.root.geometry("700x500")
        self.root.resizable(True, True)
        # 设置最小窗口尺寸，确保控件可见
        self.root.minsize(600, 400)

        # 自动聊天控制
        self.auto_chat_thread = None
        self.auto_chat_stop = threading.Event()
        self.auto_chat_remaining = 0

        # 虚拟人对话监控窗口
        self.vh_monitor_window = None
        self.vh_monitor_text = None

        # 构建界面（必须先创建控件，setup_system会用到chat_display）
        self.create_widgets()

        # 初始化系统
        self.setup_system()

        # 欢迎消息
        self.add_system_message("欢迎！只保留导师对话模式。")

        # 自动聚焦输入框
        self.input_entry.focus()

        # 注册虚拟人互聊回调
        if self.demo.auto_chat_scheduler:
            self.demo.auto_chat_scheduler.message_callback = self.on_virtual_chat_message

        # 启动自动聊天（如果设置中启用）
        self.start_auto_chat_if_enabled()

    def setup_system(self):
        """初始化系统"""
        if not self.demo.load_or_create():
            self.show_setup_dialog()
        else:
            vh = self.demo.vh
            if vh:
                self.add_system_message(f"当前导师: {vh.name} (关系度: {vh.get_relationship_with_player():.0f})")

    def show_setup_dialog(self):
        """创建虚拟人对话框（简化）"""
        dialog = tk.Toplevel(self.root)
        dialog.title("选择导师")
        dialog.geometry("350x200")
        dialog.transient(self.root)
        dialog.grab_set()

        tk.Label(dialog, text="创建或选择一位导师：", font=("Arial", 10, "bold")).pack(pady=10)

        tk.Label(dialog, text="昵称:").pack(pady=5)
        name_entry = tk.Entry(dialog, width=20)
        name_entry.pack(pady=5)
        name_entry.insert(0, "导师小柔")

        tk.Label(dialog, text="性格:").pack(pady=5)
        from config import PERSONALITY_PRESETS
        types = list(PERSONALITY_PRESETS.keys())
        type_var = tk.StringVar(value=types[0])
        type_combo = ttk.Combobox(dialog, textvariable=type_var, values=types, state="readonly", width=18)
        type_combo.pack(pady=5)

        def on_create():
            name = name_entry.get().strip() or "导师"
            ptype = type_var.get()
            # 创建为导师（教师或贵人职业自动标记为导师）
            vh = self.demo.create_virtual_human(name, ptype, is_player=False)
            # 自动设为导师（如果尚未自动识别）
            if not vh.is_mentor:
                vh.is_mentor = True
                vh.mentor_type = vh._assign_mentor_type()
            self.demo.select_virtual_human(vh.id)
            dialog.destroy()
            self.refresh_info()
            self.add_system_message(f"导师 {vh.name} 已就位！开始对话吧～")

        tk.Button(dialog, text="开始对话", command=on_create, bg="#4CAF50", fg="white", width=15).pack(pady=15)

        dialog.wait_window()

    def create_widgets(self):
        """创建界面组件"""
        # 顶部信息栏
        self.info_frame = tk.Frame(self.root, bg="#f0f0f0", height=30)
        self.info_frame.pack(fill=tk.X, side=tk.TOP)

        # 左侧信息标签
        self.info_label = tk.Label(self.info_frame, text="就绪", bg="#f0f0f0", anchor="w", padx=10)
        self.info_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 右侧设置按钮
        settings_btn = tk.Button(
            self.info_frame,
            text="⚙️ 设置",
            command=self.show_settings_dialog,
            bg="#e0e0e0",
            font=("Microsoft YaHei", 9),
            width=8,
            relief=tk.FLAT
        )
        settings_btn.pack(side=tk.RIGHT, padx=(0, 10), pady=5)

        # 聊天显示区域
        self.chat_frame = tk.Frame(self.root)
        self.chat_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.chat_display = scrolledtext.ScrolledText(
            self.chat_frame,
            wrap=tk.WORD,
            state=tk.DISABLED,
            font=("Microsoft YaHei", 11),
            bg="#fafafa"
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True)

        # 配置标签样式
        self.chat_display.tag_config("user", foreground="#0078D4", font=("Microsoft YaHei", 11, "bold"))
        self.chat_display.tag_config("assistant", foreground="#2E7D32", font=("Microsoft YaHei", 11))
        self.chat_display.tag_config("system", foreground="#9E9E9E", font=("Microsoft YaHei", 10, "italic"))

        # 自动聊天控制面板
        self.auto_chat_frame = tk.Frame(self.root, bg="#f5f5f5", height=45)
        self.auto_chat_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=(0, 5))
        # 不禁止propagate，让布局自适应

        # 左侧：控制选项
        control_frame = tk.Frame(self.auto_chat_frame, bg="#f5f5f5")
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(5, 0))

        tk.Label(control_frame, text="自动对话:", bg="#f5f5f5", font=("Microsoft YaHei", 9)).pack(side=tk.LEFT, padx=(0, 5))

        # 轮数设置
        tk.Label(control_frame, text="轮数:", bg="#f5f5f5", font=("Microsoft YaHei", 9)).pack(side=tk.LEFT, padx=(5, 2))
        self.auto_rounds_var = tk.IntVar(value=10)
        rounds_spin = tk.Spinbox(control_frame, from_=1, to=100, textvariable=self.auto_rounds_var, width=5, font=("Microsoft YaHei", 9))
        rounds_spin.pack(side=tk.LEFT, padx=(0, 10))

        # 间隔设置
        tk.Label(control_frame, text="间隔(秒):", bg="#f5f5f5", font=("Microsoft YaHei", 9)).pack(side=tk.LEFT, padx=(5, 2))
        self.auto_interval_var = tk.IntVar(value=30)
        interval_spin = tk.Spinbox(control_frame, from_=5, to=300, textvariable=self.auto_interval_var, width=5, font=("Microsoft YaHei", 9))
        interval_spin.pack(side=tk.LEFT, padx=(0, 10))

        # 中间：状态显示
        self.auto_status_label = tk.Label(control_frame, text="就绪", bg="#f5f5f5", fg="#666666", font=("Microsoft YaHei", 9))
        self.auto_status_label.pack(side=tk.LEFT, padx=10)

        # 右侧：按钮
        btn_frame = tk.Frame(control_frame, bg="#f5f5f5")
        btn_frame.pack(side=tk.RIGHT, padx=(10, 0))

        self.auto_start_btn = tk.Button(
            btn_frame,
            text="▶ 开始自动",
            command=self.start_auto_chat_manual,
            bg="#4CAF50",
            fg="white",
            font=("Microsoft YaHei", 9),
            width=10
        )
        self.auto_start_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.auto_stop_btn = tk.Button(
            btn_frame,
            text="■ 停止",
            command=self.stop_auto_chat_manual,
            bg="#f44336",
            fg="white",
            font=("Microsoft YaHei", 9),
            width=8,
            state=tk.DISABLED
        )
        self.auto_stop_btn.pack(side=tk.LEFT)

        # 底部输入区域
        self.input_frame = tk.Frame(self.root, height=60, pady=5)
        self.input_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=(0, 10))

        self.input_entry = tk.Entry(self.input_frame, font=("Microsoft YaHei", 11))
        self.input_entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        self.input_entry.bind("<Return>", lambda e: self.send_message())

        send_btn = tk.Button(
            self.input_frame,
            text="发送",
            command=self.send_message,
            bg="#0078D4",
            fg="white",
            font=("Microsoft YaHei", 10, "bold"),
            width=10
        )
        send_btn.pack(side=tk.RIGHT)

    def refresh_info(self):
        """更新顶部信息"""
        vh = self.demo.vh
        if vh:
            rel = vh.get_relationship_with_player()
            info = f"导师: {vh.name} | 情绪: {vh.state['mood']} | 能量: {vh.state['energy']} | 关系度: {rel:.0f}"
            self.info_label.config(text=info)

    def add_message(self, role: str, content: str):
        """添加消息到聊天框"""
        self.chat_display.config(state=tk.NORMAL)

        if role == "user":
            prefix = "你: "
            tag = "user"
        elif role == "assistant":
            prefix = f"{self.demo.vh.name}: " if self.demo.vh else "导师: "
            tag = "assistant"
        else:
            prefix = "[系统] "
            tag = "system"

        self.chat_display.insert(tk.END, prefix, tag)
        self.chat_display.insert(tk.END, content + "\n\n")
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)

    def add_system_message(self, msg: str):
        """添加系统消息"""
        self.add_message("system", msg)

    def send_message(self):
        """发送消息"""
        msg = self.input_entry.get().strip()
        if not msg:
            return

        self.input_entry.delete(0, tk.END)
        self.add_message("user", msg)

        # 在新线程中处理回复，避免界面卡顿
        threading.Thread(target=self.get_reply, args=(msg,), daemon=True).start()

    def get_reply(self, user_msg: str):
        """获取导师回复（在后台线程，支持流式）"""
        try:
            # 流式回调函数
            def stream_callback(chunk):
                self.root.after(0, lambda c=chunk: self._append_to_last_message(c))

            # 使用 APIClient 的流式功能
            reply = self.demo.api_client.generate_reply(self.demo.vh, user_msg, stream_callback=stream_callback)

            # 流式完成后刷新信息
            if reply is not None:
                # 非流式回退（应该不会发生）
                self.root.after(0, lambda: self.add_message("assistant", reply.get("reply", "")))
                self.root.after(0, self.refresh_info)
            else:
                # 流式完成，添加换行并刷新
                self.root.after(0, lambda: self._finish_stream_message())
                self.root.after(0, self.refresh_info)
        except Exception as e:
            self.root.after(0, lambda: self.add_system_message(f"错误: {e}"))

    def _append_to_last_message(self, text_chunk: str):
        """向最后一个助手的消息追加文本（流式效果）"""
        self.chat_display.config(state=tk.NORMAL)
        # 移动到末尾
        self.chat_display.see(tk.END)
        # 插入文本块
        self.chat_display.insert(tk.END, text_chunk, "assistant")
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)

    def _finish_stream_message(self):
        """完成流式消息 - 添加换行"""
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, "\n\n")
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)

    def start_auto_chat_if_enabled(self):
        """根据设置启动自动聊天（应用启动时）"""
        s = gui_settings.load_settings()
        if s.get("auto_chat_enabled", False):
            rounds = s.get("auto_chat_rounds", 10)
            interval = s.get("auto_chat_interval", 30)
            # 更新界面控件
            self.auto_rounds_var.set(rounds)
            self.auto_interval_var.set(interval)
            # 启动用户↔导师自动聊天
            self._start_auto_chat_thread(rounds, interval)
            # 更新按钮状态
            self._set_auto_buttons_state(False)
            self.auto_status_label.config(text=f"已启用，剩余{rounds}轮")
        else:
            self.auto_status_label.config(text="就绪")
            self._set_auto_buttons_state(True)

        # 自动启动虚拟人互聊调度器（独立控制）
        if self.demo.auto_chat_scheduler and not self.demo.auto_chat_scheduler.running:
            self.demo.auto_chat_scheduler.start()
            print("[GUI] 虚拟人互聊调度器已启动")

    def start_auto_chat_manual(self):
        """手动开启自动聊天（按钮点击）"""
        rounds = self.auto_rounds_var.get()
        interval = self.auto_interval_var.get()

        if rounds <= 0:
            messagebox.showwarning("参数错误", "轮数必须大于0")
            return
        if interval < 5:
            messagebox.showwarning("参数错误", "间隔不能小于5秒")
            return

        # 停止之前的自动聊天（如果有）
        self.stop_auto_chat()

        # 启动新线程
        self._start_auto_chat_thread(rounds, interval)
        self.add_system_message(f"自动对话已手动开启（{rounds}轮，间隔{interval}秒）")

        # 更新按钮状态
        self.auto_start_btn.config(state=tk.DISABLED)
        self.auto_stop_btn.config(state=tk.NORMAL)

    def _start_auto_chat_thread(self, rounds: int, interval: int):
        """启动自动聊天线程"""
        self.auto_chat_remaining = rounds
        self.auto_chat_stop.clear()
        self.auto_chat_thread = threading.Thread(
            target=self._auto_chat_worker,
            args=(interval,),
            daemon=True
        )
        self.auto_chat_thread.start()
        self._update_auto_status()

    def stop_auto_chat_manual(self):
        """手动停止自动聊天"""
        self.stop_auto_chat()
        self.add_system_message("自动对话已停止")
        self.auto_status_label.config(text="已停止")
        self.auto_start_btn.config(state=tk.NORMAL)
        self.auto_stop_btn.config(state=tk.DISABLED)

    def stop_auto_chat(self):
        """停止自动聊天（内部方法）"""
        if self.auto_chat_thread and self.auto_chat_thread.is_alive():
            self.auto_chat_stop.set()
            self.auto_chat_thread.join(timeout=1)
    def _auto_chat_worker(self, interval: int):
        """自动聊天后台线程 - 模拟用户与导师的完整对话"""
        import time
        import random

        # 模拟用户的话题（自动聊天的用户消息）
        user_topics = [
            "你好，最近怎么样？",
            "在做什么呢？",
            "你觉得我该怎么赚钱？",
            "我最近有点困惑，该怎么办？",
            "有什么建议可以给我吗？",
            "我的工作不顺利，怎么办？",
            "我想学点新技能，有什么推荐？",
            "你觉得人生最重要的是什么？",
            "如何提升自己？",
            "可以陪我聊聊吗？",
            "我对未来很迷茫",
            "怎么才能成功？",
            "你觉得我适合做什么？"
        ]

        while not self.auto_chat_stop.is_set() and self.auto_chat_remaining > 0:
            # 更新状态：等待中
            self.root.after(0, lambda r=self.auto_chat_remaining: self._update_auto_status(f"等待下一轮... 剩余{r}轮"))

            time.sleep(interval)

            if self.auto_chat_stop.is_set():
                break

            # 检查是否有导师
            mentors = [vh for vh in self.demo.agent_manager.virtual_humans.values()
                      if getattr(vh, 'is_mentor', False)]
            if not mentors:
                self.root.after(0, lambda: self.add_system_message("[自动] 没有可用的导师，自动对话停止"))
                break

            # 更新状态：正在对话
            self.root.after(0, lambda r=self.auto_chat_remaining: self._update_auto_status(f"对话中... 剩余{r}轮"))

            # 随机选择一位导师
            mentor = random.choice(mentors)

            # 自动聊一轮：模拟用户发送一条消息
            user_msg = random.choice(user_topics)

            # 显示用户消息（标记为自动）
            self.root.after(0, lambda u=user_msg: self._show_auto_user_message(u))

            # 延时一下，让界面响应
            time.sleep(0.5)

            # 调用 API 生成导师回复（流式）
            try:
                reply = self.demo.api_client.generate_reply(mentor, user_msg)
                if reply:
                    reply_text = reply.get("reply", "")
                    # 在GUI线程中显示回复（流式效果）
                    self.root.after(0, lambda r=reply_text, m=mentor: self._stream_assistant_message(r, m))
            except Exception as e:
                self.root.after(0, lambda e=e: self.add_system_message(f"[自动] 对话错误: {e}"))

            self.auto_chat_remaining -= 1

        # 结束
        if self.auto_chat_stop.is_set():
            self.root.after(0, lambda: self.auto_status_label.config(text="已停止"))
        else:
            self.root.after(0, lambda: self.auto_status_label.config(text="已完成"))
            self.root.after(0, lambda: self._set_auto_buttons_state(True))

    def _show_auto_user_message(self, message: str):
        """显示自动聊天中的用户消息"""
        self.chat_display.config(state=tk.NORMAL)
        prefix = "[自动] 你: "
        self.chat_display.insert(tk.END, prefix, "user")
        self.chat_display.insert(tk.END, message + "\n\n")
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)

    def _stream_assistant_message(self, full_text: str, mentor):
        """流式显示助手消息（自动聊天专用）- 使用 after 实现打字效果"""
        # 防御：兼容 mentor 可能是字典的情况（从某些数据源加载）
        if isinstance(mentor, dict):
            mentor_name = mentor.get('name', '导师')
        else:
            mentor_name = getattr(mentor, 'name', '导师')

        self.chat_display.config(state=tk.NORMAL)
        prefix = f"[自动] {mentor_name}: "
        self.chat_display.insert(tk.END, prefix, "assistant")
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)

        index = 0
        def stream_next():
            nonlocal index
            if index < len(full_text):
                ch = full_text[index]
                index += 1
                self.chat_display.config(state=tk.NORMAL)
                self.chat_display.insert(tk.END, ch, "assistant")
                self.chat_display.see(tk.END)
                self.chat_display.config(state=tk.DISABLED)
                self.root.after(30, stream_next)
            else:
                self.chat_display.config(state=tk.NORMAL)
                self.chat_display.insert(tk.END, "\n\n")
                self.chat_display.see(tk.END)
                self.chat_display.config(state=tk.DISABLED)

        stream_next()

    def _update_auto_status(self, status_text: str = None):
        """更新自动聊天状态显示"""
        if status_text:
            self.auto_status_label.config(text=status_text)
        else:
            if self.auto_chat_remaining > 0:
                self.auto_status_label.config(text=f"运行中... 剩余{self.auto_chat_remaining}轮")
            else:
                self.auto_status_label.config(text="已完成")

    def _set_auto_buttons_state(self, start_enabled: bool):
        """设置自动聊天按钮状态"""
        self.auto_start_btn.config(state=tk.NORMAL if start_enabled else tk.DISABLED)
        self.auto_stop_btn.config(state=tk.DISABLED if start_enabled else tk.NORMAL)

    def stop_auto_chat(self):
        """停止自动聊天"""
        if self.auto_chat_thread and self.auto_chat_thread.is_alive():
            self.auto_chat_stop.set()
            self.auto_chat_thread.join(timeout=1)
        # 重置按钮状态
        self.root.after(0, lambda: self._set_auto_buttons_state(True))
        self.root.after(0, lambda: self.auto_status_label.config(text="已停止"))
        self.refresh_info()
        # 可以加载历史消息（如果需要）

    def show_status(self):
        """显示当前导师状态"""
        vh = self.demo.vh
        if not vh:
            messagebox.showwarning("警告", "没有可用的导师")
            return

        status_lines = [
            f"=== {vh.name} 的状态 ===",
            f"年龄: {vh.age:.1f}岁 | 职业: {vh.job}",
            f"情绪: {vh.state['mood']} | 能量: {vh.state['energy']}/100",
            f"关系度: {vh.get_relationship_with_player():.0f}/100",
            f"今日行动: {vh.actions_today}次"
        ]
        if vh.is_mentor:
            status_lines.append(f"导师类型: {vh.mentor_type}")
        messagebox.showinfo("状态", "\n".join(status_lines))

    def list_mentors(self):
        """列出所有导师"""
        mentors = [vh for vh in self.demo.agent_manager.virtual_humans.values() if vh.is_mentor]
        if not mentors:
            messagebox.showinfo("导师列表", "暂无导师")
            return

        lines = [f"{m.name} (关系: {m.get_relationship_with_player():.0f})" for m in mentors]
        messagebox.showinfo("导师列表", "\n".join(lines))

    def create_menu(self):
        """创建简化菜单"""
        menubar = Menu(self.root)
        self.root.config(menu=menubar)

        # 文件菜单
        file_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="保存数据", command=self.demo.agent_manager.save_all)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.root.quit)

        # 设置菜单（新增）
        settings_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="设置", menu=settings_menu)
        settings_menu.add_command(label="API配置...", command=self.show_settings_dialog)

        # 视图菜单（虚拟人互聊监控）
        view_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="视图", menu=view_menu)
        view_menu.add_command(label="虚拟人对话监控", command=self.create_vh_monitor_window)

        # 导师菜单（核心）
        mentor_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="导师", menu=mentor_menu)
        mentor_menu.add_command(label="查看导师状态", command=self.show_status)
        mentor_menu.add_command(label="导师列表", command=self.list_mentors)
        mentor_menu.add_separator()
        mentor_menu.add_command(label="选择导师", command=self.switch_mentor)

        # 帮助菜单
        help_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="关于", command=self.show_about)

    def switch_mentor(self):
        """切换导师对话框"""
        dialog = tk.Toplevel(self.root)
        dialog.title("选择导师")
        dialog.geometry("300x200")
        dialog.transient(self.root)
        dialog.grab_set()

        tk.Label(dialog, text="选择当前对话导师：").pack(pady=10)

        mentors = [vh for vh in self.demo.agent_manager.virtual_humans.values() if vh.is_mentor]
        if not mentors:
            tk.Label(dialog, text="暂无导师，请先创建").pack(pady=20)
            return

        listbox = tk.Listbox(dialog, height=6)
        for m in mentors:
            listbox.insert(tk.END, f"{m.name} (关系: {m.get_relationship_with_player():.0f})")
        listbox.pack(pady=10, fill=tk.X, padx=20)

        def on_select():
            idx = listbox.curselection()
            if idx:
                mentor = mentors[idx[0]]
                self.demo.select_virtual_human(mentor.id)
                self.refresh_info()
                self.add_system_message(f"已切换到导师: {mentor.name}")
            dialog.destroy()

        tk.Button(dialog, text="切换", command=on_select).pack(pady=10)

    def show_about(self):
        """显示关于信息（包含路径）"""
        try:
            from build_info import __version__
            ver = __version__
        except:
            ver = "1.0.3.2"

        # 获取程序路径
        program_dir = os.path.dirname(os.path.abspath(sys.argv[0])) if sys.argv[0] else "Unknown"
        settings_path = os.path.join(program_dir, "settings.json")
        config_path = os.path.join(program_dir, "config.py")

        about_text = f"""OpenSims - 导师对话模式
版本: {ver}

【路径信息】
程序目录: {program_dir}
配置文件: {config_path}
用户设置: {settings_path}

【功能】
• 导师对话（流式输出）
• 自动对话（可配置轮数/间隔）
• 虚拟人互聊监控
• Human-like Chat增强

【技术支持】
.github: chatgpt-yunju/opensims-demo"""

        messagebox.showinfo("关于", about_text)

    def show_settings_dialog(self):
        """显示设置对话框"""
        dialog = tk.Toplevel(self.root)
        dialog.title("设置")
        dialog.geometry("450x350")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)

        # 加载当前设置
        current_settings = gui_settings.load_settings()

        # 创建表单
        form_frame = ttk.Frame(dialog, padding="20")
        form_frame.pack(fill=tk.BOTH, expand=True)

        # API Endpoint
        ttk.Label(form_frame, text="API Endpoint:").grid(row=0, column=0, sticky=tk.W, pady=5)
        endpoint_var = tk.StringVar(value=current_settings.get("api_endpoint", ""))
        endpoint_entry = ttk.Entry(form_frame, textvariable=endpoint_var, width=50)
        endpoint_entry.grid(row=0, column=1, pady=5, padx=(10, 0))

        # API Key
        ttk.Label(form_frame, text="API Key:").grid(row=1, column=0, sticky=tk.W, pady=5)
        api_key_var = tk.StringVar(value=current_settings.get("api_key", ""))
        api_key_entry = ttk.Entry(form_frame, textvariable=api_key_var, width=50, show="*")
        api_key_entry.grid(row=1, column=1, pady=5, padx=(10, 0))

        # Model
        ttk.Label(form_frame, text="Model:").grid(row=2, column=0, sticky=tk.W, pady=5)
        model_var = tk.StringVar(value=current_settings.get("model", "step-3.5-flash"))
        model_entry = ttk.Entry(form_frame, textvariable=model_var, width=50)
        model_entry.grid(row=2, column=1, pady=5, padx=(10, 0))

        # Separator
        ttk.Separator(form_frame, orient=tk.HORIZONTAL).grid(row=3, column=0, columnspan=2, sticky=tk.EW, pady=15)

        # Use Mock checkbox
        use_mock_var = tk.BooleanVar(value=current_settings.get("use_mock", False))
        mock_check = ttk.Checkbutton(form_frame, text="使用模拟模式 (Use Mock)", variable=use_mock_var)
        mock_check.grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=5)

        # Auto Chat checkbox
        auto_chat_var = tk.BooleanVar(value=current_settings.get("auto_chat_enabled", False))
        auto_chat_check = ttk.Checkbutton(form_frame, text="开启自动对话 (Auto Chat)", variable=auto_chat_var)
        auto_chat_check.grid(row=5, column=0, columnspan=2, sticky=tk.W, pady=5)

        # Auto Chat Rounds
        ttk.Label(form_frame, text="自动对话轮数:").grid(row=6, column=0, sticky=tk.W, pady=5)
        rounds_var = tk.IntVar(value=current_settings.get("auto_chat_rounds", 10))
        rounds_spinbox = ttk.Spinbox(form_frame, from_=1, to=100, textvariable=rounds_var, width=10)
        rounds_spinbox.grid(row=6, column=1, sticky=tk.W, pady=5, padx=(10, 0))

        # Buttons
        btn_frame = ttk.Frame(form_frame)
        btn_frame.grid(row=7, column=0, columnspan=2, pady=10)

        def on_save():
            new_settings = {
                "api_endpoint": endpoint_var.get().strip(),
                "api_key": api_key_var.get().strip(),
                "model": model_var.get().strip(),
                "use_mock": use_mock_var.get(),
                "auto_chat_enabled": auto_chat_var.get(),
                "auto_chat_rounds": rounds_var.get(),
                "auto_chat_interval": self.auto_interval_var.get()  # 从主界面控件获取
            }
            # 验证
            if not new_settings["api_endpoint"]:
                messagebox.showerror("错误", "API Endpoint 不能为空")
                return
            if not new_settings["model"]:
                messagebox.showerror("错误", "Model 不能为空")
                return
            try:
                rounds = int(new_settings["auto_chat_rounds"])
                interval = int(new_settings["auto_chat_interval"])
                if rounds < 1 or interval < 5:
                    raise ValueError
            except:
                messagebox.showerror("错误", "轮数必须≥1，间隔必须≥5秒")
                return

            if gui_settings.save_settings(new_settings):
                # 热更新APIClient配置（无需重启）
                self.demo.api_client.update_config(
                    endpoint=new_settings["api_endpoint"],
                    api_key=new_settings["api_key"],
                    model=new_settings["model"],
                    use_mock=new_settings["use_mock"]
                )
                # 同步自动聊天设置到控制面板
                self.auto_rounds_var.set(new_settings["auto_chat_rounds"])
                self.auto_interval_var.set(new_settings["auto_chat_interval"])

                # 根据设置的状态自动启停
                if new_settings["auto_chat_enabled"]:
                    if not (self.auto_chat_thread and self.auto_chat_thread.is_alive()):
                        self.start_auto_chat_manual()
                else:
                    if self.auto_chat_thread and self.auto_chat_thread.is_alive():
                        self.stop_auto_chat_manual()

                messagebox.showinfo("成功", "设置已保存并应用！")
                dialog.destroy()
            else:
                messagebox.showerror("错误", "保存设置失败")

        def on_cancel():
            dialog.destroy()

        ttk.Button(btn_frame, text="保存", command=on_save, width=10).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="取消", command=on_cancel, width=10).pack(side=tk.LEFT, padx=5)

    def run(self):
        """运行GUI"""
        # 窗口关闭时清理
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

    def on_closing(self):
        """窗口关闭事件"""
        self.stop_auto_chat()
        if self.demo.auto_chat_scheduler:
            self.demo.auto_chat_scheduler.stop()
        self.root.quit()
        self.root.destroy()

    def create_vh_monitor_window(self):
        """创建虚拟人对话监控窗口"""
        if self.vh_monitor_window is None or not self.vh_monitor_window.winfo_exists():
            self.vh_monitor_window = tk.Toplevel(self.root)
            self.vh_monitor_window.title("虚拟人对话监控")
            self.vh_monitor_window.geometry("600x400")
            self.vh_monitor_window.transient(self.root)
            self.vh_monitor_window.resizable(True, True)

            # 文本框
            self.vh_monitor_text = scrolledtext.ScrolledText(
                self.vh_monitor_window,
                wrap=tk.WORD,
                state=tk.NORMAL,
                font=("Microsoft YaHei", 10),
                bg="#f5f5f5"
            )
            self.vh_monitor_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            self.vh_monitor_text.config(state=tk.DISABLED)

            # 关闭时隐藏
            self.vh_monitor_window.protocol("WM_DELETE_WINDOW", self.on_close_monitor)
        else:
            self.vh_monitor_window.deiconify()
            self.vh_monitor_window.lift()

    def on_close_monitor(self):
        """关闭监控窗口（隐藏）"""
        if self.vh_monitor_window:
            self.vh_monitor_window.withdraw()

    def on_virtual_chat_message(self, speaker_name: str, message: str, is_group: bool = False):
        """处理虚拟人互聊消息（回调）"""
        # 如果监控窗口未打开，自动创建并显示（可选）
        if self.vh_monitor_window is None or not self.vh_monitor_window.winfo_exists():
            self.create_vh_monitor_window()

        if self.vh_monitor_text:
            timestamp = datetime.now().strftime("%H:%M:%S")
            prefix = f"[{timestamp}] "
            if is_group:
                prefix += "[群聊] "
            prefix += f"{speaker_name}: "

            self.vh_monitor_text.config(state=tk.NORMAL)
            self.vh_monitor_text.insert(tk.END, prefix + message + "\n\n")
            self.vh_monitor_text.see(tk.END)
            self.vh_monitor_text.config(state=tk.DISABLED)


if __name__ == "__main__":
    app = MentorChatGUI()
    app.run()
