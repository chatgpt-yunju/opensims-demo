import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from main import OpenSimsDemo

class OpenSimsGUI:
    """Tkinter图形界面"""

    def __init__(self):
        self.demo = OpenSimsDemo()
        self.root = tk.Tk()
        self.root.title("OpenSims Demo")
        self.root.geometry("600x500")

        # 加载或创建虚拟人
        self.setup_virtual_human()

        # 构建界面
        self.create_widgets()

        # 刷新显示
        self.refresh_display()

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

    def create_widgets(self):
        """构建所有界面组件"""
        # 顶部状态栏
        self.status_frame = tk.Frame(self.root)
        self.status_frame.pack(fill=tk.X, padx=10, pady=5)

        self.status_label = tk.Label(self.root, text="状态: ", anchor="w", font=("Consolas", 10))
        self.status_label.pack(fill=tk.X, padx=10)

        # 分隔线
        ttk.Separator(self.root, orient='horizontal').pack(fill=tk.X)

        # 聊天显示区
        self.chat_frame = tk.Frame(self.root)
        self.chat_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.chat_text = scrolledtext.ScrolledText(self.chat_frame, wrap=tk.WORD, state='disabled')
        self.chat_text.pack(fill=tk.BOTH, expand=True)

        # 配置标签样式
        self.chat_text.tag_config('user', foreground='blue', font=('Arial', 10, 'bold'))
        self.chat_text.tag_config('assistant', foreground='green', font=('Arial', 10, 'bold'))
        self.chat_text.tag_config('system', foreground='gray', font=('Arial', 9, 'italic'))

        # 输入区
        input_frame = tk.Frame(self.root)
        input_frame.pack(fill=tk.X, padx=10, pady=5)

        self.input_entry = tk.Entry(input_frame)
        self.input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.input_entry.bind('<Return>', lambda e: self.send_message())

        send_btn = tk.Button(input_frame, text="发送", command=self.send_message)
        send_btn.pack(side=tk.RIGHT, padx=(5, 0))

        # 底部按钮
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Button(btn_frame, text="清空聊天", command=self.clear_chat).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="重新设置", command=self.reset_virtual_human).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="保存并退出", command=self.root.quit).pack(side=tk.RIGHT, padx=2)

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
            self.demo.vh = None
            self.setup_virtual_human()
            self.refresh_display()

    def run(self):
        """启动GUI主循环"""
        self.root.mainloop()

# 导入time用于时间格式化
import time

if __name__ == "__main__":
    gui = OpenSimsGUI()
    gui.run()