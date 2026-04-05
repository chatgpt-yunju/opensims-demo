import tkinter as tk
from tkinter import ttk, scrolledtext, Menu
from main import OpenSimsDemo
import threading
import time

class MentorChatGUI:
    """极简导师对话GUI - 只保留核心对话功能"""

    def __init__(self):
        self.demo = OpenSimsDemo()
        self.root = tk.Tk()
        self.root.title("OpenSims - 导师对话")
        self.root.geometry("700x500")
        self.root.resizable(True, True)

        # 构建界面（必须先创建控件，setup_system会用到chat_display）
        self.create_widgets()

        # 初始化系统
        self.setup_system()

        # 欢迎消息
        self.add_system_message("欢迎！只保留导师对话模式。")

        # 自动聚焦输入框
        self.input_entry.focus()

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
        self.info_label = tk.Label(self.info_frame, text="就绪", bg="#f0f0f0", anchor="w", padx=10)
        self.info_label.pack(fill=tk.X)

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

        # 底部输入区域
        self.input_frame = tk.Frame(self.root, height=60)
        self.input_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=10)
        self.input_frame.pack_propagate(False)

        self.input_entry = tk.Entry(self.input_frame, font=("Microsoft YaHei", 11))
        self.input_entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.input_entry.bind("<Return>", lambda e: self.send_message())

        send_btn = tk.Button(
            self.input_frame,
            text="发送",
            command=self.send_message,
            bg="#0078D4",
            fg="white",
            font=("Microsoft YaHei", 10, "bold"),
            width=8
        )
        send_btn.pack(side=tk.RIGHT, padx=(5, 0))

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
        """获取导师回复（在后台线程）"""
        try:
            reply = self.demo.chat(user_msg)
            self.root.after(0, lambda: self.add_message("assistant", reply))
            self.root.after(0, self.refresh_info)
        except Exception as e:
            self.root.after(0, lambda: self.add_system_message(f"错误: {e}"))

    def refresh_display(self):
        """刷新界面"""
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
        """显示关于信息"""
        try:
            from build_info import __version__
            ver = __version__
        except:
            ver = "1.0.3.2"
        messagebox.showinfo("关于", f"OpenSims - 导师对话模式\n版本: {ver}\n\n专注于导师引导对话")

    def run(self):
        """运行GUI"""
        self.root.mainloop()


if __name__ == "__main__":
    app = MentorChatGUI()
    app.run()
