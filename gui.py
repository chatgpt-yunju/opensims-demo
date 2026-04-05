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
        """构建导师引导为中心的界面"""
        # 顶部工具栏
        toolbar = tk.Frame(self.root, bd=1, relief=tk.RAISED)
        toolbar.pack(side=tk.TOP, fill=tk.X)

        tk.Button(toolbar, text="💬 与导师对话", command=self.focus_chat, width=12).pack(side=tk.LEFT, padx=2, pady=2)
        tk.Button(toolbar, text="📊 成长轨迹", command=self.show_guidance_log, width=12).pack(side=tk.LEFT, padx=2, pady=2)
        tk.Button(toolbar, text="👥 所有角色", command=self.list_all_virtual_humans, width=12).pack(side=tk.LEFT, padx=2, pady=2)
        tk.Button(toolbar, text="🔄 切换角色", command=self.switch_character, width=12).pack(side=tk.LEFT, padx=2, pady=2)
        tk.Button(toolbar, text="➕ 创建角色", command=self.create_character_dialog, width=12).pack(side=tk.LEFT, padx=2, pady=2)
        tk.Button(toolbar, text="⚙️ 更多", command=self.show_more_menu, width=10).pack(side=tk.RIGHT, padx=2, pady=2)

        # 主内容区 - 三栏布局
        main_pane = tk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 左侧：导师列表 (显示所有教师/贵人)
        self.mentor_frame = tk.Frame(main_pane, width=250)
        main_pane.add(self.mentor_frame, stretch="never")

        tk.Label(self.mentor_frame, text="导师列表", font=('Arial', 10, 'bold')).pack(pady=5)
        self.mentor_listbox = tk.Listbox(self.mentor_frame, height=30, width=30)
        self.mentor_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.mentor_listbox.bind('<<ListboxSelect>>', self.on_mentor_select)

        # 显示选中导师的关系度
        self.mentor_status_label = tk.Label(self.mentor_frame, text="请选择导师", font=('Arial', 9))
        self.mentor_status_label.pack(pady=5)

        # 中间：聊天区（主区域）
        chat_frame = tk.Frame(main_pane)
        main_pane.add(chat_frame, stretch="always")

        # 聊天标题
        title_frame = tk.Frame(chat_frame)
        title_frame.pack(fill=tk.X, pady=(0, 5))
        self.chat_title_label = tk.Label(title_frame, text="对话区域", font=('Arial', 12, 'bold'))
        self.chat_title_label.pack(side=tk.LEFT)
        tk.Button(title_frame, text="清空", command=self.clear_chat, width=6).pack(side=tk.RIGHT)

        # 聊天显示区
        self.chat_text = scrolledtext.ScrolledText(chat_frame, wrap=tk.WORD, state='disabled', height=20, font=('Consolas', 10))
        self.chat_text.pack(fill=tk.BOTH, expand=True)

        # 配置标签样式
        self.chat_text.tag_config('user', foreground='blue', font=('Arial', 10, 'bold'))
        self.chat_text.tag_config('assistant', foreground='green', font=('Arial', 10, 'bold'))
        self.chat_text.tag_config('system', foreground='gray', font=('Arial', 9, 'italic'))
        self.chat_text.tag_config('mentor_name', foreground='purple', font=('Arial', 11, 'bold'))

        # 输入区
        input_frame = tk.Frame(chat_frame)
        input_frame.pack(fill=tk.X, pady=5)

        self.input_entry = tk.Entry(input_frame, font=('Arial', 10))
        self.input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.input_entry.bind('<Return>', lambda e: self.send_message())
        self.input_entry.focus()

        send_btn = tk.Button(input_frame, text="发送", command=self.send_message, width=10)
        send_btn.pack(side=tk.RIGHT, padx=(5, 0))

        # 右侧：成长轨迹概览
        growth_frame = tk.Frame(main_pane, width=200)
        main_pane.add(growth_frame, stretch="never")

        tk.Label(growth_frame, text="成长轨迹", font=('Arial', 10, 'bold')).pack(pady=5)

        # 成长指标显示
        self.growth_text = scrolledtext.ScrolledText(growth_frame, wrap=tk.WORD, height=20, width=30, font=('Consolas', 9))
        self.growth_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 底部状态栏
        self.status_label = tk.Label(self.root, text="就绪", anchor="w", font=("Consolas", 9))
        self.status_label.pack(fill=tk.X, padx=10, pady=2)

    def refresh_display(self):
        """刷新界面显示 - 导师列表、聊天、成长轨迹"""
        # 更新导师列表
        self.refresh_mentor_list()

        # 更新当前聊天标题
        if self.demo.vh:
            self.chat_title_label.config(text=f"与 {self.demo.vh.name} 对话" + (" [导师]" if getattr(self.demo.vh, 'is_mentor', False) else ""))

        # 重新加载聊天记录（如果当前有虚拟人）
        if self.demo.vh:
            self.chat_text.config(state='normal')
            self.chat_text.delete(1.0, tk.END)

            # 显示最近记忆
            for mem in self.demo.vh.memory[-30:]:  # 显示最近30条
                role = mem['role']
                content = mem['content']
                timestamp = time.strftime("%m-%d %H:%M", time.localtime(mem['timestamp']))

                if role == 'user':
                    self.chat_text.insert(tk.END, f"[{timestamp}] 你:\n", 'user')
                else:
                    speaker = mem.get('speaker', self.demo.vh.name)
                    if speaker != self.demo.vh.name:
                        self.chat_text.insert(tk.END, f"[{timestamp}] {speaker}:\n", 'mentor_name')
                    else:
                        self.chat_text.insert(tk.END, f"[{timestamp}] {speaker}:\n", 'assistant')
                self.chat_text.insert(tk.END, f"{content}\n\n", role)

            self.chat_text.config(state='disabled')
            self.chat_text.see(tk.END)

        # 更新成长轨迹显示
        self.refresh_growth_summary()

        # 更新状态栏
        if self.demo.vh:
            status = f"当前: {self.demo.vh.name} | 年龄: {getattr(self.demo.vh, 'age', '?'):.1f}"
            if hasattr(self.demo, 'player_growth') and self.demo.player_growth:
                summary = self.demo.player_growth.get_growth_summary()
                status += f" | 使命线索: {summary['mission_clues_count']} | 引导: {summary['total_guidance_sessions']}次"
            self.status_label.config(text=status)

    def refresh_mentor_list(self):
        """刷新导师列表"""
        self.mentor_listbox.delete(0, tk.END)
        vhs = self.demo.agent_manager.list_virtual_humans()

        mentors = []
        for vh_dict in vhs:
            if vh_dict.get('is_mentor', False):
                name = vh_dict['name']
                rel = vh_dict.get('relationship_with_player', 50)
                job = vh_dict.get('job', '?')
                vh_id = vh_dict['id']
                display = f"{name} ({job}) - 关系:{rel}"
                if vh_dict.get('id') == self.demo.agent_manager.active_vh_id:
                    display = f"▶ {display}"
                self.mentor_listbox.insert(tk.END, display)
                mentors.append((vh_id, rel))

        if not mentors:
            self.mentor_listbox.insert(tk.END, "（暂无导师）")

    def refresh_growth_summary(self):
        """刷新成长轨迹概览"""
        self.growth_text.config(state='normal')
        self.growth_text.delete(1.0, tk.END)

        if not hasattr(self.demo, 'player_growth') or not self.demo.player_growth:
            self.growth_text.insert(tk.END, "成长数据未初始化")
            self.growth_text.config(state='disabled')
            return

        growth = self.demo.player_growth
        summary = growth.get_growth_summary()

        # 格式化显示
        lines = [
            f"=== 玩家成长概况 ===",
            f"当前使命: {summary['life_mission'] or summary['current_status'] or '未确认'}",
            f"已发现兴趣: {len(summary['discovered_interests'])} 个",
            f"使命线索: {summary['mission_clues_count']} 条",
            f"完成挑战: {summary['challenges_completed']} 个",
            f"引导次数: {summary['total_guidance_sessions']} 次",
            f"人生事件: {len(growth.life_events)} 条\n",
            f"=== 技能熟练度 (Top 5) ==="
        ]

        # top_skills is a list of (skill, level)
        for skill, level in summary['top_skills']:
            bar = "█" * int(level/10) + "░" * int(10 - level/10)
            lines.append(f"{skill:15} {bar} {level:.0f}")

        if growth.mission_clues:
            lines.append("\n=== 使命线索 ===")
            for clue in growth.mission_clues[:3]:
                lines.append(f"• {clue[:40]}")

        self.growth_text.insert(tk.END, "\n".join(lines))
        self.growth_text.config(state='disabled')
        self.growth_text.see(tk.END)

    def send_message(self):
        """发送消息 - 支持引导系统"""
        user_input = self.input_entry.get().strip()
        if not user_input or not self.demo.vh:
            return

        # 显示用户消息
        self.chat_text.config(state='normal')
        timestamp = time.strftime("%H:%M")
        self.chat_text.insert(tk.END, f"[{timestamp}] 你: ", 'user')
        self.chat_text.insert(tk.END, f"{user_input}\n\n", 'user')
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
            speaker_name = self.demo.vh.name
            tag = 'assistant' if not getattr(self.demo.vh, 'is_mentor', False) else 'mentor_name'
            self.chat_text.insert(tk.END, f"[{timestamp}] {speaker_name}: ", tag)
            self.chat_text.insert(tk.END, f"{reply}\n\n", tag)
            self.chat_text.config(state='disabled')
            self.chat_text.see(tk.END)

            # 刷新所有面板
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

    def focus_chat(self):
        """聚焦到聊天输入框"""
        self.input_entry.focus()

    def on_mentor_select(self, event):
        """选择导师"""
        selection = self.mentor_listbox.curselection()
        if not selection:
            return

        idx = selection[0]
        vhs = self.demo.agent_manager.list_virtual_humans()
        mentors = [vh for vh in vhs if vh.get('is_mentor', False)]

        if idx < len(mentors):
            vh_id = mentors[idx]['id']
            self.demo.select_virtual_human(vh_id)
            self.refresh_display()

            # 更新导师关系标签
            mentor = mentors[idx]
            rel = mentor.get('relationship_with_player', 50)
            name = mentor['name']
            self.mentor_status_label.config(text=f"已选择: {name} (关系度: {rel})")

    def switch_character(self):
        """切换当前角色对话对象"""
        # 复用对话选择逻辑，但保留在当前列表中
        self.chat_with_vh()

    def create_character_dialog(self):
        """创建新角色对话框"""
        dialog = tk.Toplevel(self.root)
        dialog.title("创建AI角色")
        dialog.geometry("350x300")
        dialog.transient(self.root)
        dialog.grab_set()

        # 昵称
        tk.Label(dialog, text="角色昵称:").pack(pady=5)
        name_entry = tk.Entry(dialog, width=30)
        name_entry.pack(pady=5)
        name_entry.insert(0, "新角色")

        # 性格类型
        tk.Label(dialog, text="性格类型:").pack(pady=5)
        from config import PERSONALITY_PRESETS
        types = list(PERSONALITY_PRESETS.keys())
        type_var = tk.StringVar(value=types[0])
        type_combo = ttk.Combobox(dialog, textvariable=type_var, values=types, state="readonly", width=20)
        type_combo.pack(pady=5)

        # 职业选择
        tk.Label(dialog, text="职业 (教师/贵人会成为导师):").pack(pady=5)
        from config import PROFESSIONS
        prof_var = tk.StringVar(value=PROFESSIONS[0] if PROFESSIONS else "学生")
        prof_combo = ttk.Combobox(dialog, textvariable=prof_var, values=PROFESSIONS, state="readonly", width=20)
        prof_combo.pack(pady=5)

        # 标记为玩家角色
        is_player_var = tk.BooleanVar(value=False)
        tk.Checkbutton(dialog, text="标记为玩家角色", variable=is_player_var).pack(pady=5)

        def on_create():
            name = name_entry.get().strip()
            ptype = type_var.get()
            job = prof_var.get()
            is_player = is_player_var.get()

            if not name:
                messagebox.showwarning("警告", "请输入昵称")
                return

            try:
                # 创建虚拟人
                self.demo.create_virtual_human(name, ptype)
                # 设置职业
                if self.demo.vh:
                    self.demo.vh.job = job
                    self.demo.vh._update_mentor_status_from_job()
                    # 如果是教师或贵人，自动标记为导师
                    if job in ["教师", "贵人"]:
                        self.demo.vh.is_mentor = True

                    self.demo.agent_manager.save_virtual_human(self.demo.vh.id)

                dialog.destroy()
                messagebox.showinfo("成功", f"已创建角色: {name} ({job})")
                self.refresh_display()

            except Exception as e:
                messagebox.showerror("错误", f"创建失败: {e}")

        btn_frame = tk.Frame(dialog)
        btn_frame.pack(pady=15)
        tk.Button(btn_frame, text="创建", command=on_create, width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="取消", command=dialog.destroy, width=10).pack(side=tk.RIGHT, padx=5)

        dialog.wait_window()

    def show_more_menu(self):
        """显示"更多"选项菜单"""
        menu = Menu(self.root, tearoff=0)

        # 模拟人生行动
        menu.add_command(label="🍔 吃饭", command=lambda: self.do_sim_action('eat'))
        menu.add_command(label="💤 睡觉", command=lambda: self.do_sim_action('sleep'))
        menu.add_command(label="💼 工作", command=lambda: self.do_sim_action('work'))
        menu.add_command(label="🔍 找工作", command=lambda: self.do_sim_action('find_job'))
        menu.add_command(label="🎮 娱乐", command=lambda: self.do_sim_action('relax'))
        menu.add_command(label="👥 社交", command=lambda: self.do_sim_action('socialize'))
        menu.add_command(label="🛒 购物", command=lambda: self.do_sim_action('shop'))
        menu.add_separator()
        menu.add_command(label="📅 结束今天", command=lambda: self.do_sim_action('day_pass'))

        # 工具
        menu.add_separator()
        menu.add_command(label="📕 小红书发布", command=self.xiaohongshu_publish)
        menu.add_command(label="📰 掘金文章提取", command=self.extract_juejin)
        menu.add_command(label="🔄 自动发布流程", command=self.auto_publish)

        # 系统
        menu.add_separator()
        menu.add_command(label="💾 保存数据", command=self.save_data)
        menu.add_command(label="📋 查看版本", command=self.show_version)
        menu.add_command(label="❓ 关于", command=self.show_about)

        # 显示菜单
        try:
            menu.tk_popup(self.root.winfo_pointerx(), self.root.winfo_pointery())
        finally:
            menu.grab_release()

    def show_guidance_log(self):
        """显示完整成长日志（GUI窗口）"""
        if not hasattr(self.demo, 'player_growth') or not self.demo.player_growth:
            messagebox.showwarning("警告", "成长数据未初始化")
            return

        growth = self.demo.player_growth
        summary = growth.get_growth_summary()

        # 创建日志窗口
        log_window = tk.Toplevel(self.root)
        log_window.title("成长轨迹 - 完整日志")
        log_window.geometry("800x600")
        log_window.transient(self.root)

        # 标题
        tk.Label(log_window, text="=== 完整成长记录 ===", font=('Arial', 12, 'bold')).pack(pady=10)

        # 文本显示区
        log_text = scrolledtext.ScrolledText(log_window, wrap=tk.WORD, font=('Consolas', 9))
        log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # 构建完整日志内容
        content_lines = [
            f"当前使命: {summary['life_mission'] or summary['current_status'] or '未确认'}",
            f"已发现兴趣领域: {', '.join(summary['discovered_interests']) if summary['discovered_interests'] else '无'}",
            f"使命线索收集: {summary['mission_clues_count']} 条",
            f"完成挑战: {summary['challenges_completed']} 个",
            f"引导总次数: {summary['total_guidance_sessions']} 次",
            f"人生事件数: {len(growth.life_events)} 条\n"
        ]

        # 添加人生事件（最近10条）
        if growth.life_events:
            content_lines.append("=== 人生事件时间线 ===")
            for event in growth.life_events[-10:]:
                content_lines.append(f"  • {event['time']}: {event['description']}")
            content_lines.append("")

        # 最近引导记录（最近10条）
        if growth.guidance_history:
            content_lines.append("=== 最近引导记录 ===")
            for record in growth.guidance_history[-10:]:
                # record has: date, mentor, question, focus, mission_clues_added
                content_lines.append(f"\n[{record.get('date', '?')}] 导师: {record.get('mentor', '?')}")
                q = record.get('question', '')
                if q:
                    content_lines.append(f"问题: {q[:60]}{'...' if len(q)>60 else ''}")
                content_lines.append(f"引导方向: {record.get('focus', '?')}")
                if record.get('mission_clues_added'):
                    content_lines.append(f"新增线索: {', '.join(record['mission_clues_added'])}")

        # 所有使命线索
        if growth.mission_clues:
            content_lines.append("\n=== 所有使命线索 ===")
            for i, clue in enumerate(growth.mission_clues, 1):
                content_lines.append(f"{i}. {clue}")

        log_text.insert(tk.END, "\n".join(content_lines))
        log_text.config(state='disabled')

        # 关闭按钮
        tk.Button(log_window, text="关闭", command=log_window.destroy, width=10).pack(pady=10)

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