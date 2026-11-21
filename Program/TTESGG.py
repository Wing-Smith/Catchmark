# VERSION: 2.3.0-gen2-support-20260808
import ctypes
import sys
import tkinter as tk
from tkinter import filedialog, messagebox
import json
import os
import re
import subprocess
import platform
from datetime import datetime
from pathlib import Path

# ============ DPI 感知 ============
if sys.platform == 'win32':
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        ctypes.windll.user32.SetProcessDPIAware()

# ============ 偏移量（仅此处出现） ============
OFFSET = 7350

def decrypt(text):
    return "".join(chr(ord(c) - OFFSET) for c in text)

def encrypt(text):
    return "".join(chr(ord(c) + OFFSET) for c in text)

TRANSPARENT = "#010101"

# ============ 配色 ============
PALETTE = {
    "dark": {
        "bg": "#202020", "card": "#2d2d2d", "card_accent": "#1e3a5f",
        "fg": "#ffffff", "muted": "#a0a0a0", "accent": "#4cc2ff",
        "border": "#3a3a3a", "btn_primary": "#0078d4", "btn_secondary": "#3a3a3a",
    },
    "light": {
        "bg": "#f3f3f3", "card": "#ffffff", "card_accent": "#e8f4ff",
        "fg": "#1a1a1a", "muted": "#5f5f5f", "accent": "#0078d4",
        "border": "#e5e5e5", "btn_primary": "#0078d4", "btn_secondary": "#e5e5e5",
    }
}

EDITOR_ITEMS = {
    "fib_10m": {"name": "大整数累加", "row": 2, "col": 0, "group": "classic"},
    "matmul_512": {"name": "矩阵乘法", "row": 2, "col": 1, "group": "classic"},
    "json_200k": {"name": "JSON 混合负载", "row": 2, "col": 2, "group": "classic"},
    "prime_10m": {"name": "素数筛", "row": 3, "col": 0, "group": "neo"},
    "str_regex_100k": {"name": "字符串处理", "row": 3, "col": 1, "group": "neo"},
    "dict_500k": {"name": "字典运算", "row": 3, "col": 2, "group": "neo"},
    "memory_50m": {"name": "内存带宽", "row": 4, "col": 0, "group": "gen2"},
    "list_ops_500k": {"name": "列表操作", "row": 4, "col": 1, "group": "gen2"},
    "io_1m": {"name": "I/O 吞吐", "row": 4, "col": 2, "group": "gen2"},
    "gil": {"name": "GIL 并发", "row": 5, "col": 0, "group": "gen2", "colspan": 3, "no_score": True},
}

EDITOR_CARD_DEFS = {
    "fib_10m": [("耗时 (s)", "fib_time", True), ("结果位数", "fib_digits", True), ("单项得分", "fib_score", False)],
    "matmul_512": [("耗时 (s)", "mat_time", True), ("等效 GFLOPS", "mat_gflops", True), ("校验和", "mat_checksum", True), ("单项得分", "mat_score", False)],
    "json_200k": [("耗时 (s)", "json_time", True), ("JSON 大小 (MB)", "json_size_mb", True), ("SHA256 前缀", "json_sha16", True), ("单项得分", "json_score", False)],
    "prime_10m": [("耗时 (s)", "prime_time", True), ("素数个数", "prime_count", True), ("单项得分", "prime_score", False)],
    "str_regex_100k": [("耗时 (s)", "str_time", True), ("匹配次数", "str_matches", True), ("单项得分", "str_score", False)],
    "dict_500k": [("耗时 (s)", "dict_time", True), ("字典大小", "dict_size", True), ("查找命中", "dict_hits", True), ("单项得分", "dict_score", False)],
    "memory_50m": [("耗时 (s)", "memory_time", True), ("等效带宽 (MB/s)", "memory_bandwidth", True), ("单项得分", "memory_score", False)],
    "list_ops_500k": [("耗时 (s)", "list_time", True), ("最终长度", "list_length", True), ("单项得分", "list_score", False)],
    "io_1m": [("耗时 (s)", "io_time", True), ("二进制大小 (KB)", "io_bin_kb", True), ("文本行数", "io_lines", True), ("单项得分", "io_score", False)],
    "gil": [("单线程耗时 (s)", "gil_single_time", True), ("多线程耗时 (s)", "gil_multi_time", True), ("实际加速比", "gil_speedup", True), ("并发效率", "gil_efficiency", True)],
}

MODE_ITEMS = {
    "classic": ["fib_10m", "matmul_512", "json_200k"],
    "neo": ["fib_10m", "matmul_512", "json_200k", "prime_10m", "str_regex_100k", "dict_500k"],
    "gen2": ["fib_10m", "matmul_512", "json_200k", "prime_10m", "str_regex_100k", "dict_500k", "memory_50m", "list_ops_500k", "io_1m", "gil"],
    "custom": ["fib_10m", "matmul_512", "json_200k", "prime_10m", "str_regex_100k", "dict_500k", "memory_50m", "list_ops_500k", "io_1m", "gil"],
}

# ============ Win11 DWM ============
if sys.platform == 'win32':
    class MARGINS(ctypes.Structure):
        _fields_ = [("cxLeftWidth", ctypes.c_int), ("cxRightWidth", ctypes.c_int),
                    ("cyTopHeight", ctypes.c_int), ("cyBottomHeight", ctypes.c_int)]

    def apply_win11(hwnd):
        try:
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(ctypes.c_int(1)), 4)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 33, ctypes.byref(ctypes.c_int(2)), 4)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 38, ctypes.byref(ctypes.c_int(3)), 4)
            ctypes.windll.dwmapi.DwmExtendFrameIntoClientArea(hwnd, ctypes.byref(MARGINS(-1, -1, -1, -1)))
        except Exception:
            pass

# ============ 系统信息 ============
def get_cpu_name():
    try:
        result = subprocess.run(["wmic", "cpu", "get", "Name"], capture_output=True, text=True, timeout=5)
        lines = [l.strip() for l in result.stdout.splitlines() if l.strip() and l.strip() != "Name"]
        if lines:
            return lines[0]
    except Exception:
        pass
    return "Unknown"

def get_python_version():
    return platform.python_version()

def get_core_count():
    try:
        return str(os.cpu_count())
    except Exception:
        return "Unknown"

# ============ 圆角卡片 ============
class RoundedCard(tk.Canvas):
    def __init__(self, parent, bg_color, radius=16, border_color=None, **grid_kwargs):
        super().__init__(parent, highlightthickness=0, bd=0, bg=parent.cget("bg"), height=1)
        self.bg_color, self.radius, self.border_color = bg_color, radius, border_color
        self.inner = tk.Frame(self, bg=bg_color)
        self.inner_id = self.create_window(0, 0, window=self.inner, anchor="nw")
        if grid_kwargs:
            self.grid(**grid_kwargs)
        self.bind("<Configure>", self._on_resize)

    def _on_resize(self, event=None):
        self.delete("bg")
        w, h, r = self.winfo_width(), self.winfo_height(), self.radius
        points = [r,0, w-r,0, w,0, w,r, w,h-r, w,h, w-r,h, r,h, 0,h, 0,h-r, 0,r, 0,0]
        outline = self.border_color or self.bg_color
        self.create_polygon(points, smooth=True, fill=self.bg_color, outline=outline, width=1, tags="bg")
        self.tag_lower("bg")
        self.itemconfig(self.inner_id, width=max(1, w-2*r), height=max(1, h-2*r))
        self.coords(self.inner_id, r, r)

    def set_color(self, bg_color, border_color=None):
        self.bg_color, self.border_color = bg_color, border_color
        self.inner.configure(bg=bg_color)
        self._on_resize()

    def update_height(self):
        self.update_idletasks()
        self.configure(height=self.inner.winfo_reqheight() + 2*self.radius)
        self._on_resize()

# ============ 主程序 ============
class Viewer:
    def __init__(self, root):
        self.root, self.theme = root, "dark"
        self.c = PALETTE[self.theme]
        self.tracked, self.cards, self.fields = [], [], {}
        self.editor_vars = {}
        self.editor_cards = []
        self.editor_selected_items = set(MODE_ITEMS["classic"])
        self.active_page = "dashboard"
        self.editor_vars = {}
        self.editor_cards = []
        self.active_page = "dashboard"

        root.title("Catchmark Result Viewer")
        root.configure(bg=TRANSPARENT)
        root.wm_attributes('-transparentcolor', TRANSPARENT)

        # 加载自定义图标（支持 Nuitka onefile 嵌入资源）
        self._load_icon(root, "Catchmark_Viewer.png")

        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
        w = min(int(sw * 0.90), 2560)
        h = min(int(w * 9 / 16), int(sh * 0.90))
        root.geometry(f"{w}x{h}")
        root.minsize(1600, 900)

        if sys.platform == 'win32':
            root.update_idletasks()
            apply_win11(ctypes.windll.user32.GetParent(root.winfo_id()))

        root.grid_columnconfigure(1, weight=1)
        root.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_main()

    def _load_icon(self, root, filename):
        """从脚本目录或 exe 目录加载图标，支持 Nuitka onefile 嵌入资源"""
        candidates = []
        try:
            candidates.append(Path(__file__).resolve().parent / filename)
        except NameError:
            pass
        if getattr(sys, 'frozen', False):
            candidates.append(Path(sys.executable).resolve().parent / filename)
        for path in candidates:
            if not path.exists():
                continue
            try:
                img = tk.PhotoImage(file=str(path))
                root.iconphoto(True, img)
                return
            except Exception:
                try:
                    from PIL import Image, ImageTk
                    img = ImageTk.PhotoImage(Image.open(str(path)))
                    root.iconphoto(True, img)
                    return
                except Exception:
                    continue

    def _track(self, widget, attr, role):
        self.tracked.append((widget, attr, role))
        widget.configure(**{attr: self.c[role]})
        return widget

    def _build_sidebar(self):
        self.sidebar = tk.Frame(self.root, width=320, bg=TRANSPARENT)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        tk.Label(self.sidebar, text="Catchmark", font=("Segoe UI", 26, "bold"),
                 bg=TRANSPARENT, fg=self.c["fg"]).pack(anchor="w", padx=30, pady=(40, 4))
        tk.Label(self.sidebar, text="Benchmark Viewer", font=("Segoe UI", 10),
                 bg=TRANSPARENT, fg=self.c["fg"]).pack(anchor="w", padx=30, pady=(0, 40))

        self.btn_dashboard = self._btn("结果面板", self._show_dashboard, "btn_primary")
        self.btn_dashboard.pack(fill="x", padx=20, pady=4)
        self.btn_editor = self._btn("制作结果", self._show_editor, "btn_secondary")
        self.btn_editor.pack(fill="x", padx=20, pady=4)
        self.btn_convert = self._btn("转换工具", self._show_convert, "btn_secondary")
        self.btn_convert.pack(fill="x", padx=20, pady=4)
        self.btn_theme = self._btn("切换主题", self.toggle_theme, "btn_secondary")
        self.btn_theme.pack(fill="x", padx=20, pady=4)
        self.btn_exit = self._btn("退出", self.root.destroy, "btn_secondary")
        self.btn_exit.pack(fill="x", padx=20, pady=4)

        self.path_var = tk.StringVar(value="未选择文件")
        tk.Label(self.sidebar, textvariable=self.path_var, font=("Segoe UI", 9),
                 bg=TRANSPARENT, fg=self.c["fg"], wraplength=260).pack(
                     side="bottom", anchor="w", padx=30, pady=30)

    def _btn(self, text, cmd, bg_role):
        return tk.Button(self.sidebar, text=text, command=cmd, font=("Segoe UI", 10),
                         bg=self.c[bg_role], fg=self.c["fg"], activebackground=self.c["accent"],
                         activeforeground=self.c["fg"], bd=0, padx=12, pady=12, cursor="hand2")

    def _build_main(self):
        self.main = tk.Frame(self.root, bg=self.c["bg"])
        self.main.grid(row=0, column=1, sticky="nsew")
        self.main.grid_columnconfigure(0, weight=1)
        self.main.grid_rowconfigure(0, weight=1)
        self._track(self.main, "bg", "bg")

        # 仪表盘
        self.page_dashboard = tk.Frame(self.main, bg=self.c["bg"])
        self.page_dashboard.grid(row=0, column=0, sticky="nsew", padx=40, pady=40)
        self.page_dashboard.grid_columnconfigure(0, weight=1)
        self.page_dashboard.grid_rowconfigure(1, weight=1)
        self._track(self.page_dashboard, "bg", "bg")

        # 标题和加载按钮行
        title_frame = tk.Frame(self.page_dashboard, bg=self.c["bg"])
        title_frame.grid(row=0, column=0, sticky="ew", pady=(0, 24))
        title_frame.grid_columnconfigure(0, weight=1)
        self._track(title_frame, "bg", "bg")

        dash_title = tk.Label(title_frame, text="结果面板", font=("Segoe UI", 32, "bold"),
                              bg=self.c["bg"], fg=self.c["fg"])
        dash_title.grid(row=0, column=0, sticky="w")
        self._track(dash_title, "bg", "bg")
        self._track(dash_title, "fg", "fg")

        self.dash_load_btn = tk.Button(title_frame, text="📂 加载结果", command=self.open_file,
                  font=("Segoe UI", 10), bg=self.c["btn_primary"], fg=self.c["fg"],
                  activebackground=self.c["accent"], activeforeground=self.c["fg"],
                  bd=0, padx=16, pady=8, cursor="hand2")
        self.dash_load_btn.grid(row=0, column=1, sticky="e")
        self._track(self.dash_load_btn, "bg", "btn_primary")
        self._track(self.dash_load_btn, "fg", "fg")
        self._track(self.dash_load_btn, "activebackground", "accent")
        self._track(self.dash_load_btn, "activeforeground", "fg")

        self._build_dashboard_scroll()

        # 转换工具
        self.page_convert = tk.Frame(self.main, bg=self.c["bg"])
        self.page_convert.grid(row=0, column=0, sticky="nsew", padx=40, pady=40)
        self.page_convert.grid_columnconfigure(0, weight=1)
        self.page_convert.grid_rowconfigure(1, weight=1)
        self._track(self.page_convert, "bg", "bg")

        conv_title = tk.Label(self.page_convert, text="转换工具", font=("Segoe UI", 32, "bold"),
                              bg=self.c["bg"], fg=self.c["fg"])
        conv_title.grid(row=0, column=0, sticky="w", pady=(0, 24))
        self._track(conv_title, "bg", "bg")
        self._track(conv_title, "fg", "fg")

        self._build_convert_content()
        self.page_convert.grid_remove()

        # 制作结果
        self._build_editor()
        self.page_editor.grid_remove()

        # 统一鼠标滚轮处理
        self.root.bind_all("<MouseWheel>", lambda e: self._on_mousewheel(e))

        # 检查命令行参数，自动加载传入的 .wnpbr 文件
        self._check_cli_args()
    def _build_dashboard_scroll(self):
        sw = tk.Frame(self.page_dashboard)
        sw.grid(row=1, column=0, sticky="nsew")
        sw.grid_rowconfigure(0, weight=1)
        sw.grid_columnconfigure(0, weight=1)
        self._track(sw, "bg", "bg")

        self.canvas = tk.Canvas(sw, highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self._track(self.canvas, "bg", "bg")

        sb = tk.Scrollbar(sw, orient="vertical", command=self.canvas.yview)
        sb.grid(row=0, column=1, sticky="ns")
        self.canvas.configure(yscrollcommand=sb.set)

        self.content = tk.Frame(self.canvas)
        self.content_id = self.canvas.create_window((0, 0), window=self.content, anchor="nw")
        self._track(self.content, "bg", "bg")

        self.content.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(self.content_id, width=e.width))

        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_columnconfigure(1, weight=1)
        self.content.grid_columnconfigure(2, weight=1)

        self._build_cards()

    def _build_cards(self):
        self._card("综合评分", 0, 0, colspan=3, accent=True, items=[("综合得分", "total_score")], big=True)
        self._card("系统信息", 1, 0, colspan=3, items=[
            ("CPU 型号", "cpu"), ("Python 版本", "python"),
            ("逻辑核心数", "cores"), ("测试时间", "timestamp")
        ])
        self._card("大整数累加", 2, 0, items=[
            ("耗时 (s)", "fib_time"), ("结果位数", "fib_digits"), ("单项得分", "fib_score")
        ])
        self._card("矩阵乘法", 2, 1, items=[
            ("耗时 (s)", "mat_time"), ("等效 GFLOPS", "mat_gflops"),
            ("校验和", "mat_checksum"), ("单项得分", "mat_score")
        ])
        self._card("JSON 混合负载", 2, 2, items=[
            ("耗时 (s)", "json_time"), ("JSON 大小 (MB)", "json_size_mb"),
            ("SHA256 前缀", "json_sha16"), ("单项得分", "json_score")
        ])


    def _clear_dashboard(self):
        """清空 dashboard 内容区"""
        for w in self.content.winfo_children():
            w.destroy()
        self.cards = []
        self.fields = {}
        self.tracked = [(w, a, r) for w, a, r in self.tracked if w.winfo_exists()]

    def _rebuild_dashboard(self, mode):
        """根据模式重建整个 dashboard 内容"""
        self._clear_dashboard()
        self.current_mode = mode
        if mode == "neo":
            self._build_neo_layout()
        elif mode == "gen2":
            self._build_gen2_layout()
        elif mode == "custom":
            self._build_custom_layout()
        else:
            self._build_classic_layout()
        self.content.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self.canvas.yview_moveto(0)

    def _build_classic_layout(self):
        self._card("综合评分", 0, 0, colspan=3, accent=True, items=[("综合得分", "total_score")], big=True)
        self._card("系统信息", 1, 0, colspan=3, items=[
            ("CPU 型号", "cpu"), ("Python 版本", "python"),
            ("逻辑核心数", "cores"), ("测试时间", "timestamp")
        ])
        self._card("大整数累加", 2, 0, items=[
            ("耗时 (s)", "fib_time"), ("结果位数", "fib_digits"), ("单项得分", "fib_score")
        ])
        self._card("矩阵乘法", 2, 1, items=[
            ("耗时 (s)", "mat_time"), ("等效 GFLOPS", "mat_gflops"),
            ("校验和", "mat_checksum"), ("单项得分", "mat_score")
        ])
        self._card("JSON 混合负载", 2, 2, items=[
            ("耗时 (s)", "json_time"), ("JSON 大小 (MB)", "json_size_mb"),
            ("SHA256 前缀", "json_sha16"), ("单项得分", "json_score")
        ])

    def _build_neo_layout(self):
        self._card("Neo 综合评分", 0, 0, colspan=3, accent=True, items=[("Neo 综合得分", "neo_total_score")], big=True)
        self._card("系统信息", 1, 0, colspan=3, items=[
            ("CPU 型号", "cpu"), ("Python 版本", "python"),
            ("逻辑核心数", "cores"), ("测试时间", "timestamp")
        ])
        self._card("大整数累加", 2, 0, items=[
            ("耗时 (s)", "fib_time"), ("结果位数", "fib_digits"), ("单项得分", "fib_score")
        ])
        self._card("矩阵乘法", 2, 1, items=[
            ("耗时 (s)", "mat_time"), ("等效 GFLOPS", "mat_gflops"),
            ("校验和", "mat_checksum"), ("单项得分", "mat_score")
        ])
        self._card("JSON 混合负载", 2, 2, items=[
            ("耗时 (s)", "json_time"), ("JSON 大小 (MB)", "json_size_mb"),
            ("SHA256 前缀", "json_sha16"), ("单项得分", "json_score")
        ])
        self._card("素数筛", 3, 0, items=[
            ("耗时 (s)", "prime_time"), ("素数个数", "prime_count"), ("单项得分", "prime_score")
        ])
        self._card("字符串处理", 3, 1, items=[
            ("耗时 (s)", "str_time"), ("匹配次数", "str_matches"), ("单项得分", "str_score")
        ])
        self._card("字典运算", 3, 2, items=[
            ("耗时 (s)", "dict_time"), ("字典大小", "dict_size"),
            ("查找命中", "dict_hits"), ("单项得分", "dict_score")
        ])

    def _build_gen2_layout(self):
        self._card("Gen2 综合评分", 0, 0, colspan=3, accent=True, items=[("Gen2 综合得分", "gen2_total_score")], big=True)
        self._card("系统信息", 1, 0, colspan=3, items=[
            ("CPU 型号", "cpu"), ("Python 版本", "python"),
            ("逻辑核心数", "cores"), ("测试时间", "timestamp")
        ])
        # 经典三项
        self._card("大整数累加", 2, 0, items=[
            ("耗时 (s)", "fib_time"), ("结果位数", "fib_digits"), ("单项得分", "fib_score")
        ])
        self._card("矩阵乘法", 2, 1, items=[
            ("耗时 (s)", "mat_time"), ("等效 GFLOPS", "mat_gflops"),
            ("校验和", "mat_checksum"), ("单项得分", "mat_score")
        ])
        self._card("JSON 混合负载", 2, 2, items=[
            ("耗时 (s)", "json_time"), ("JSON 大小 (MB)", "json_size_mb"),
            ("SHA256 前缀", "json_sha16"), ("单项得分", "json_score")
        ])
        # Neo 三项
        self._card("素数筛", 3, 0, items=[
            ("耗时 (s)", "prime_time"), ("素数个数", "prime_count"), ("单项得分", "prime_score")
        ])
        self._card("字符串处理", 3, 1, items=[
            ("耗时 (s)", "str_time"), ("匹配次数", "str_matches"), ("单项得分", "str_score")
        ])
        self._card("字典运算", 3, 2, items=[
            ("耗时 (s)", "dict_time"), ("字典大小", "dict_size"),
            ("查找命中", "dict_hits"), ("单项得分", "dict_score")
        ])
        # Gen2 三项
        self._card("内存带宽", 4, 0, items=[
            ("耗时 (s)", "memory_time"), ("等效带宽 (MB/s)", "memory_bandwidth"), ("单项得分", "memory_score")
        ])
        self._card("列表操作", 4, 1, items=[
            ("耗时 (s)", "list_time"), ("最终长度", "list_length"), ("单项得分", "list_score")
        ])
        self._card("I/O 吞吐", 4, 2, items=[
            ("耗时 (s)", "io_time"), ("二进制大小 (KB)", "io_bin_kb"),
            ("文本行数", "io_lines"), ("单项得分", "io_score")
        ])
        # GIL 并发（独立展示）
        self._card("GIL 并发", 5, 0, colspan=3, items=[
            ("单线程耗时 (s)", "gil_single_time"), ("多线程耗时 (s)", "gil_multi_time"),
            ("实际加速比", "gil_speedup"), ("并发效率", "gil_efficiency")
        ])
    def _build_custom_layout(self):
        self._card("客制化综合评分", 0, 0, colspan=3, accent=True,
                   items=[("客制化综合得分", "custom_total_score")], big=True)
        self._card("系统信息", 1, 0, colspan=3, items=[
            ("CPU 型号", "cpu"), ("Python 版本", "python"),
            ("逻辑核心数", "cores"), ("测试时间", "timestamp")
        ])
        # 经典三项
        self._card("大整数累加", 2, 0, items=[
            ("耗时 (s)", "fib_time"), ("结果位数", "fib_digits"), ("单项得分", "fib_score")
        ])
        self._card("矩阵乘法", 2, 1, items=[
            ("耗时 (s)", "mat_time"), ("等效 GFLOPS", "mat_gflops"),
            ("校验和", "mat_checksum"), ("单项得分", "mat_score")
        ])
        self._card("JSON 混合负载", 2, 2, items=[
            ("耗时 (s)", "json_time"), ("JSON 大小 (MB)", "json_size_mb"),
            ("SHA256 前缀", "json_sha16"), ("单项得分", "json_score")
        ])
        # Neo 三项
        self._card("素数筛", 3, 0, items=[
            ("耗时 (s)", "prime_time"), ("素数个数", "prime_count"), ("单项得分", "prime_score")
        ])
        self._card("字符串处理", 3, 1, items=[
            ("耗时 (s)", "str_time"), ("匹配次数", "str_matches"), ("单项得分", "str_score")
        ])
        self._card("字典运算", 3, 2, items=[
            ("耗时 (s)", "dict_time"), ("字典大小", "dict_size"),
            ("查找命中", "dict_hits"), ("单项得分", "dict_score")
        ])
        # Gen2 三项
        self._card("内存带宽", 4, 0, items=[
            ("耗时 (s)", "memory_time"), ("等效带宽 (MB/s)", "memory_bandwidth"), ("单项得分", "memory_score")
        ])
        self._card("列表操作", 4, 1, items=[
            ("耗时 (s)", "list_time"), ("最终长度", "list_length"), ("单项得分", "list_score")
        ])
        self._card("I/O 吞吐", 4, 2, items=[
            ("耗时 (s)", "io_time"), ("二进制大小 (KB)", "io_bin_kb"),
            ("文本行数", "io_lines"), ("单项得分", "io_score")
        ])
        # GIL 并发（独立展示）
        self._card("GIL 并发", 5, 0, colspan=3, items=[
            ("单线程耗时 (s)", "gil_single_time"), ("多线程耗时 (s)", "gil_multi_time"),
            ("实际加速比", "gil_speedup"), ("并发效率", "gil_efficiency")
        ])

    def _card(self, title, row, col, items, colspan=1, accent=False, big=False):
        bg_role = "card_accent" if accent else "card"
        card = RoundedCard(self.content, bg_color=self.c[bg_role], radius=16,
                           border_color=self.c["border"],
                           row=row, column=col, columnspan=colspan, sticky="nsew", padx=12, pady=12)
        self.cards.append((card, bg_role))
        inner = card.inner

        title_fg = "accent" if accent else "fg"
        tf = ("Segoe UI", 18, "bold") if accent else ("Segoe UI", 14, "bold")
        lbl = tk.Label(inner, text=title, font=tf)
        lbl.pack(anchor="w", pady=(0, 16))
        self._track(lbl, "bg", bg_role)
        self._track(lbl, "fg", title_fg)

        sep = tk.Frame(inner, height=1)
        sep.pack(fill="x", pady=(0, 12))
        self._track(sep, "bg", "border")

        for i, (label, key) in enumerate(items):
            rf = tk.Frame(inner)
            rf.pack(fill="x", pady=4)
            self._track(rf, "bg", bg_role)

            ln = tk.Label(rf, text=label, font=("Segoe UI", 11))
            ln.pack(side="left")
            self._track(ln, "bg", bg_role)
            self._track(ln, "fg", "muted")

            var = tk.StringVar(value="-")
            self.fields[key] = var

            vf = ("Segoe UI", 22, "bold") if (accent and big) else ("Segoe UI", 11, "bold")
            vf_fg = "accent" if (accent and big) else "fg"
            lv = tk.Label(rf, textvariable=var, font=vf)
            lv.pack(side="right")
            self._track(lv, "bg", bg_role)
            self._track(lv, "fg", vf_fg)

            if i < len(items) - 1:
                s2 = tk.Frame(inner, height=1)
                s2.pack(fill="x", pady=(8, 0))
                self._track(s2, "bg", "border")

        card.update_height()


    def _build_editor(self):
        self.page_editor = tk.Frame(self.main, bg=self.c["bg"])
        self.page_editor.grid(row=0, column=0, sticky="nsew", padx=40, pady=40)
        self.page_editor.grid_columnconfigure(0, weight=1)
        self.page_editor.grid_rowconfigure(2, weight=1)
        self._track(self.page_editor, "bg", "bg")

        # 标题行
        title_frame = tk.Frame(self.page_editor, bg=self.c["bg"])
        title_frame.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        self._track(title_frame, "bg", "bg")

        ed_title = tk.Label(title_frame, text="制作结果文件", font=("Segoe UI", 32, "bold"),
                            bg=self.c["bg"], fg=self.c["fg"])
        ed_title.pack(side="left")
        self._track(ed_title, "bg", "bg")
        self._track(ed_title, "fg", "fg")

        # 模式切换按钮
        self.editor_mode_var = tk.StringVar(value="classic")
        self.editor_mode_btns = {}
        mode_frame = tk.Frame(title_frame, bg=self.c["bg"])
        mode_frame.pack(side="right")
        self._track(mode_frame, "bg", "bg")

        for val, name in [("classic", "经典版"), ("neo", "Neo 版"), ("gen2", "Gen2 版"), ("custom", "客制化版")]:
            btn = tk.Button(mode_frame, text=name, font=("Segoe UI", 10),
                            bg=self.c["btn_primary"] if val == "classic" else self.c["btn_secondary"],
                            fg=self.c["fg"], activebackground=self.c["accent"],
                            activeforeground=self.c["fg"], bd=0, padx=14, pady=6, cursor="hand2",
                            command=lambda v=val: self._set_editor_mode(v))
            btn.pack(side="left", padx=(8, 0))
            self.editor_mode_btns[val] = btn

        # 项目选择区域
        self.selection_frame = tk.Frame(self.page_editor, bg=self.c["bg"])
        self.selection_frame.grid(row=1, column=0, sticky="ew", pady=(0, 16))
        self._track(self.selection_frame, "bg", "bg")
        self._build_selection_ui("classic")

        # 卡片容器（带滚动）
        editor_scroll = tk.Frame(self.page_editor, bg=self.c["bg"])
        editor_scroll.grid(row=2, column=0, sticky="nsew")

        editor_scroll.grid_rowconfigure(0, weight=1)
        editor_scroll.grid_columnconfigure(0, weight=1)
        self._track(editor_scroll, "bg", "bg")

        self.editor_canvas = tk.Canvas(editor_scroll, highlightthickness=0, bg=self.c["bg"])
        self.editor_canvas.grid(row=0, column=0, sticky="nsew")
        self._track(self.editor_canvas, "bg", "bg")

        editor_sb = tk.Scrollbar(editor_scroll, orient="vertical", command=self.editor_canvas.yview)
        editor_sb.grid(row=0, column=1, sticky="ns")
        self.editor_canvas.configure(yscrollcommand=editor_sb.set)

        self.editor_cards_frame = tk.Frame(self.editor_canvas, bg=self.c["bg"])
        self.editor_cards_frame_id = self.editor_canvas.create_window((0, 0), window=self.editor_cards_frame, anchor="nw")
        self._track(self.editor_cards_frame, "bg", "bg")

        self.editor_cards_frame.bind("<Configure>", lambda e: self.editor_canvas.configure(scrollregion=self.editor_canvas.bbox("all")))
        self.editor_canvas.bind("<Configure>", lambda e: self.editor_canvas.itemconfig(self.editor_cards_frame_id, width=e.width))

        def _ed_wheel(event):
            self.editor_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        # 统一由 root bind_all 处理，此处不再单独绑定

        self.editor_cards_frame.grid_columnconfigure(0, weight=1)
        self.editor_cards_frame.grid_columnconfigure(1, weight=1)
        self.editor_cards_frame.grid_columnconfigure(2, weight=1)

        self.editor_vars = {}
        self.editor_cards = []

        # 初始构建经典版
        self._build_editor_cards("classic")

        # 按钮行 —— 紧凑底部卡片条，宽度自适应
        btn_frame = tk.Frame(self.page_editor, bg=self.c["bg"])
        btn_frame.grid(row=3, column=0, sticky="s", pady=(12, 0))
        self._track(btn_frame, "bg", "bg")

        # 仅比按钮稍宽的卡片条
        btn_inner = tk.Frame(btn_frame, bg=self.c["card"], padx=12, pady=6)
        btn_inner.pack()
        self._track(btn_inner, "bg", "card")

        self.editor_btn_load = tk.Button(btn_inner, text="📂 加载已有文件", command=self._load_existing_to_editor,
                           font=("Segoe UI", 10), bg=self.c["btn_secondary"], fg=self.c["fg"],
                           activebackground=self.c["accent"], activeforeground=self.c["fg"],
                           bd=0, padx=12, pady=8, cursor="hand2")
        self.editor_btn_load.pack(side="left", padx=(0, 8))
        self._track(self.editor_btn_load, "bg", "btn_secondary")
        self._track(self.editor_btn_load, "fg", "fg")
        self._track(self.editor_btn_load, "activebackground", "accent")
        self._track(self.editor_btn_load, "activeforeground", "fg")

        self.editor_btn_gen = tk.Button(btn_inner, text="🔒 生成加密文件", command=self._do_generate,
                          font=("Segoe UI", 10, "bold"), bg=self.c["btn_primary"], fg=self.c["fg"],
                          activebackground=self.c["accent"], activeforeground=self.c["fg"],
                          bd=0, padx=16, pady=8, cursor="hand2")
        self.editor_btn_gen.pack(side="left")
        self._track(self.editor_btn_gen, "bg", "btn_primary")
        self._track(self.editor_btn_gen, "fg", "fg")
        self._track(self.editor_btn_gen, "activebackground", "accent")
        self._track(self.editor_btn_gen, "activeforeground", "fg")

    def _build_selection_ui(self, mode):
        """根据模式构建项目选择按钮（选中蓝色 / 未选中灰色）"""
        for w in self.selection_frame.winfo_children():
            w.destroy()

        # 外层卡片容器
        card = tk.Frame(self.selection_frame, bg=self.c["card"], padx=28, pady=20)
        card.pack(fill="x", expand=True)
        self._track(card, "bg", "card")

        # 标题行
        header = tk.Frame(card, bg=self.c["card"])
        header.pack(fill="x", pady=(0, 14))
        self._track(header, "bg", "card")

        lbl = tk.Label(header, text="选择测试项目", font=("Segoe UI", 16, "bold"),
                       bg=self.c["card"], fg=self.c["accent"])
        lbl.pack(side="left")
        self._track(lbl, "bg", "card")
        self._track(lbl, "fg", "accent")

        # 分隔线
        sep = tk.Frame(card, height=2, bg=self.c["border"])
        sep.pack(fill="x", pady=(0, 16))
        self._track(sep, "bg", "border")

        # 按钮容器
        btn_container = tk.Frame(card, bg=self.c["card"])
        btn_container.pack(fill="x")
        self._track(btn_container, "bg", "card")

        self.editor_item_vars = {}
        self._sel_buttons = {}

        def _toggle(k):
            """切换选中状态并更新外观"""
            var = self.editor_item_vars[k]
            var.set(not var.get())
            self._refresh_sel_button(k)
            self._on_item_selection_changed(k)

        for key in MODE_ITEMS.get(mode, MODE_ITEMS["classic"]):
            item = EDITOR_ITEMS[key]
            var = tk.BooleanVar(value=(key in self.editor_selected_items))
            self.editor_item_vars[key] = var

            btn = tk.Button(btn_container, text=item["name"], font=("Segoe UI", 12),
                            bg=self.c["btn_primary"] if var.get() else self.c["btn_secondary"],
                            fg=self.c["fg"], activebackground=self.c["accent"],
                            activeforeground=self.c["fg"], bd=0,
                            padx=18, pady=8, cursor="hand2",
                            command=lambda k=key: _toggle(k))
            btn.pack(side="left", padx=(0, 10), pady=(0, 8))
            self._track(btn, "bg", "btn_primary" if var.get() else "btn_secondary")
            self._track(btn, "fg", "fg")
            self._track(btn, "activebackground", "accent")
            self._track(btn, "activeforeground", "fg")
            self._sel_buttons[key] = btn

    def _refresh_sel_button(self, key):
        """刷新单个选择按钮的外观"""
        btn = self._sel_buttons.get(key)
        if not btn:
            return
        is_sel = self.editor_item_vars[key].get()
        role = "btn_primary" if is_sel else "btn_secondary"
        btn.configure(bg=self.c[role])
        # 更新 tracked 列表中的记录
        for i, (w, attr, r) in enumerate(self.tracked):
            if w is btn and attr == "bg":
                self.tracked[i] = (w, attr, role)
                break

    def _on_item_selection_changed(self, key):
        """根据模式构建项目选择复选框（卡片式大气布局）"""
        for w in self.selection_frame.winfo_children():
            w.destroy()

        # 外层卡片容器
        card = tk.Frame(self.selection_frame, bg=self.c["card"], padx=28, pady=20)
        card.pack(fill="x", expand=True)
        self._track(card, "bg", "card")

        # 标题行
        header = tk.Frame(card, bg=self.c["card"])
        header.pack(fill="x", pady=(0, 14))
        self._track(header, "bg", "card")

        lbl = tk.Label(header, text="选择测试项目", font=("Segoe UI", 16, "bold"),
                       bg=self.c["card"], fg=self.c["accent"])
        lbl.pack(side="left")
        self._track(lbl, "bg", "card")
        self._track(lbl, "fg", "accent")

        # 分隔线
        sep = tk.Frame(card, height=2, bg=self.c["border"])
        sep.pack(fill="x", pady=(0, 16))
        self._track(sep, "bg", "border")

        # 复选框容器（自动换行）
        cb_container = tk.Frame(card, bg=self.c["card"])
        cb_container.pack(fill="x")
        self._track(cb_container, "bg", "card")

        self.editor_item_vars = {}
        row_frame = tk.Frame(cb_container, bg=self.c["card"])
        row_frame.pack(fill="x")
        self._track(row_frame, "bg", "card")
        col = 0

        for key in MODE_ITEMS.get(mode, MODE_ITEMS["classic"]):
            item = EDITOR_ITEMS[key]
            var = tk.BooleanVar(value=(key in self.editor_selected_items))
            self.editor_item_vars[key] = var

            # 每项独立卡片式按钮
            item_frame = tk.Frame(row_frame, bg=self.c["card"], padx=6, pady=4)
            item_frame.pack(side="left", padx=(0, 10), pady=(0, 8))
            self._track(item_frame, "bg", "card")

            cb = tk.Checkbutton(item_frame, text=item["name"], variable=var,
                                font=("Segoe UI", 12), bg=self.c["card"], fg=self.c["fg"],
                                selectcolor=self.c["bg"], activebackground=self.c["card"],
                                activeforeground=self.c["fg"], cursor="hand2")
            cb.pack()
            self._track(cb, "bg", "card")
            self._track(cb, "fg", "fg")

            var.trace_add("write", lambda *args, k=key: self._on_item_selection_changed(k))
        """根据模式构建项目选择复选框"""
        for w in self.selection_frame.winfo_children():
            w.destroy()

        lbl = tk.Label(self.selection_frame, text="选择要制作的测试项目：", font=("Segoe UI", 11, "bold"),
                       bg=self.c["bg"], fg=self.c["fg"])
        lbl.pack(side="left", padx=(0, 16))
        self._track(lbl, "bg", "bg")
        self._track(lbl, "fg", "fg")

        self.editor_item_vars = {}
        for key in MODE_ITEMS.get(mode, MODE_ITEMS["classic"]):
            item = EDITOR_ITEMS[key]
            var = tk.BooleanVar(value=(key in self.editor_selected_items))
            self.editor_item_vars[key] = var

            cb = tk.Checkbutton(self.selection_frame, text=item["name"], variable=var,
                                font=("Segoe UI", 10), bg=self.c["bg"], fg=self.c["fg"],
                                selectcolor=self.c["card"], activebackground=self.c["bg"],
                                activeforeground=self.c["fg"], cursor="hand2")
            cb.pack(side="left", padx=(0, 12))
            self._track(cb, "bg", "bg")
            self._track(cb, "fg", "fg")

            var.trace_add("write", lambda *args, k=key: self._on_item_selection_changed(k))

    def _on_item_selection_changed(self, key):
        """当项目选择状态变化时，更新选中集合并重绘卡片"""
        if self.editor_item_vars[key].get():
            self.editor_selected_items.add(key)
        else:
            self.editor_selected_items.discard(key)
        self._build_editor_cards(self.editor_mode_var.get())
        self._update_editor_calc()

    def _set_editor_mode(self, mode):
        self.editor_mode_var.set(mode)
        for v, btn in self.editor_mode_btns.items():
            btn.configure(bg=self.c["btn_primary"] if v == mode else self.c["btn_secondary"])
        # 切换模式时重置为全选
        self.editor_selected_items = set(MODE_ITEMS.get(mode, MODE_ITEMS["classic"]))
        self._build_selection_ui(mode)
        self._build_editor_cards(mode)
        for v, btn in self.editor_mode_btns.items():
            btn.configure(bg=self.c["btn_primary"] if v == mode else self.c["btn_secondary"])
        self._build_editor_cards(mode)

    def _clear_editor_cards(self):
        for w in self.editor_cards_frame.winfo_children():
            w.destroy()
        self.editor_cards = []
        # 保留所有 editor_vars，不清除（由调用方在重建前后负责保存/恢复）
        for w in self.editor_cards_frame.winfo_children():
            w.destroy()
        self.editor_cards = []
        # 保留系统信息字段，清除测试相关字段
        keep = {"cpu", "python", "cores", "timestamp"}
        self.editor_vars = {k: v for k, v in self.editor_vars.items() if k in keep}

    def _build_editor_cards(self, mode):
        # 保存当前所有变量值
        saved_values = {k: v.get() for k, v in self.editor_vars.items()}
        self._clear_editor_cards()

        # 综合评分
        if mode == "gen2":
            self._editor_card("Gen2 综合评分", 0, 0, colspan=3, accent=True, items=[
                ("Gen2 综合得分", "gen2_total_score", False)
            ], big=True)
        elif mode == "neo":
            self._editor_card("Neo 综合评分", 0, 0, colspan=3, accent=True, items=[
                ("Neo 综合得分", "neo_total_score", False)
            ], big=True)
        elif mode == "custom":
            self._editor_card("客制化综合评分", 0, 0, colspan=3, accent=True, items=[
                ("客制化综合得分", "custom_total_score", False)
            ], big=True)
        else:
            self._editor_card("综合评分", 0, 0, colspan=3, accent=True, items=[
                ("综合得分", "total_score", False)
            ], big=True)

        # 系统信息
        self._editor_card("系统信息", 1, 0, colspan=3, items=[
            ("CPU 型号", "cpu", True),
            ("Python 版本", "python", True),
            ("逻辑核心数", "cores", True),
            ("测试时间", "timestamp", True)
        ])

        # 动态构建选中的测试项卡片
        for key in self.editor_selected_items:
            if key not in EDITOR_ITEMS:
                continue
            item = EDITOR_ITEMS[key]
            defs = EDITOR_CARD_DEFS.get(key, [])
            self._editor_card(item["name"], item["row"], item["col"],
                              items=defs,
                              colspan=item.get("colspan", 1))

        # 恢复之前保存的值
        for k, val in saved_values.items():
            if k in self.editor_vars:
                self.editor_vars[k].set(val)

        # 设置系统信息的默认值
        if "cpu" not in self.editor_vars or not self.editor_vars["cpu"].get():
            self.editor_vars["cpu"] = tk.StringVar(value=get_cpu_name())
        if "python" not in self.editor_vars or not self.editor_vars["python"].get():
            self.editor_vars["python"] = tk.StringVar(value=get_python_version())
        if "cores" not in self.editor_vars or not self.editor_vars["cores"].get():
            self.editor_vars["cores"] = tk.StringVar(value=get_core_count())
        if "timestamp" not in self.editor_vars or not self.editor_vars["timestamp"].get():
            self.editor_vars["timestamp"] = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        self.editor_cards_frame.update_idletasks()
        self.editor_canvas.configure(scrollregion=self.editor_canvas.bbox("all"))
        self._clear_editor_cards()

        # 综合评分
        if mode == "gen2":
            self._editor_card("Gen2 综合评分", 0, 0, colspan=3, accent=True, items=[
                ("Gen2 综合得分", "gen2_total_score", False)
            ], big=True)
        elif mode == "neo":
            self._editor_card("Neo 综合评分", 0, 0, colspan=3, accent=True, items=[
                ("Neo 综合得分", "neo_total_score", False)
            ], big=True)
        elif mode == "custom":
            self._editor_card("客制化综合评分", 0, 0, colspan=3, accent=True, items=[
                ("客制化综合得分", "custom_total_score", False)
            ], big=True)
        else:
            self._editor_card("综合评分", 0, 0, colspan=3, accent=True, items=[
                ("综合得分", "total_score", False)
            ], big=True)

        # 系统信息
        self._editor_card("系统信息", 1, 0, colspan=3, items=[
            ("CPU 型号", "cpu", True),
            ("Python 版本", "python", True),
            ("逻辑核心数", "cores", True),
            ("测试时间", "timestamp", True)
        ])

        # 经典三项
        self._editor_card("大整数累加", 2, 0, items=[
            ("耗时 (s)", "fib_time", True),
            ("结果位数", "fib_digits", True),
            ("单项得分", "fib_score", False)
        ])
        self._editor_card("矩阵乘法", 2, 1, items=[
            ("耗时 (s)", "mat_time", True),
            ("等效 GFLOPS", "mat_gflops", True),
            ("校验和", "mat_checksum", True),
            ("单项得分", "mat_score", False)
        ])
        self._editor_card("JSON 混合负载", 2, 2, items=[
            ("耗时 (s)", "json_time", True),
            ("JSON 大小 (MB)", "json_size_mb", True),
            ("SHA256 前缀", "json_sha16", True),
            ("单项得分", "json_score", False)
        ])

        # Neo 扩展项
        if mode in ("neo", "gen2"):
            self._editor_card("素数筛", 3, 0, items=[
                ("耗时 (s)", "prime_time", True),
                ("素数个数", "prime_count", True),
                ("单项得分", "prime_score", False)
            ])
            self._editor_card("字符串处理", 3, 1, items=[
                ("耗时 (s)", "str_time", True),
                ("匹配次数", "str_matches", True),
                ("单项得分", "str_score", False)
            ])
            self._editor_card("字典运算", 3, 2, items=[
                ("耗时 (s)", "dict_time", True),
                ("字典大小", "dict_size", True),
                ("查找命中", "dict_hits", True),
                ("单项得分", "dict_score", False)
            ])

        # Gen2 扩展项
        if mode == "gen2":
            self._editor_card("内存带宽", 4, 0, items=[
                ("耗时 (s)", "memory_time", True),
                ("等效带宽 (MB/s)", "memory_bandwidth", True),
                ("单项得分", "memory_score", False)
            ])
            self._editor_card("列表操作", 4, 1, items=[
                ("耗时 (s)", "list_time", True),
                ("最终长度", "list_length", True),
                ("单项得分", "list_score", False)
            ])
            self._editor_card("I/O 吞吐", 4, 2, items=[
                ("耗时 (s)", "io_time", True),
                ("二进制大小 (KB)", "io_bin_kb", True),
                ("文本行数", "io_lines", True),
                ("单项得分", "io_score", False)
            ])
            self._editor_card("GIL 并发", 5, 0, colspan=3, items=[
                ("单线程耗时 (s)", "gil_single_time", True),
                ("多线程耗时 (s)", "gil_multi_time", True),
                ("实际加速比", "gil_speedup", True),
                ("并发效率", "gil_efficiency", True)
            ])

        # 设置默认值
        if "cpu" not in self.editor_vars or not self.editor_vars["cpu"].get():
            self.editor_vars["cpu"] = tk.StringVar(value=get_cpu_name())
        if "python" not in self.editor_vars or not self.editor_vars["python"].get():
            self.editor_vars["python"] = tk.StringVar(value=get_python_version())
        if "cores" not in self.editor_vars or not self.editor_vars["cores"].get():
            self.editor_vars["cores"] = tk.StringVar(value=get_core_count())
        if "timestamp" not in self.editor_vars or not self.editor_vars["timestamp"].get():
            self.editor_vars["timestamp"] = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        self.editor_cards_frame.update_idletasks()
        self.editor_canvas.configure(scrollregion=self.editor_canvas.bbox("all"))

    def _editor_card(self, title, row, col, items, colspan=1, accent=False, big=False):
        bg_role = "card_accent" if accent else "card"
        card = RoundedCard(self.editor_cards_frame, bg_color=self.c[bg_role], radius=16,
                           border_color=self.c["border"],
                           row=row, column=col, columnspan=colspan, sticky="nsew", padx=12, pady=12)
        self.editor_cards.append((card, bg_role))
        inner = card.inner

        title_fg = "accent" if accent else "fg"
        tf = ("Segoe UI", 18, "bold") if accent else ("Segoe UI", 14, "bold")
        lbl = tk.Label(inner, text=title, font=tf)
        lbl.pack(anchor="w", pady=(0, 16))
        self._track(lbl, "bg", bg_role)
        self._track(lbl, "fg", title_fg)

        sep = tk.Frame(inner, height=1)
        sep.pack(fill="x", pady=(0, 12))
        self._track(sep, "bg", "border")

        for i, (label, key, editable) in enumerate(items):
            rf = tk.Frame(inner)
            rf.pack(fill="x", pady=4)
            self._track(rf, "bg", bg_role)

            ln = tk.Label(rf, text=label, font=("Segoe UI", 11))
            ln.pack(side="left")
            self._track(ln, "bg", bg_role)
            self._track(ln, "fg", "muted")

            var = tk.StringVar(value="")
            self.editor_vars[key] = var

            if editable:
                entry = tk.Entry(rf, textvariable=var, font=("Segoe UI", 11, "bold"),
                                 bg=self.c["bg"], fg=self.c["fg"], insertbackground=self.c["fg"],
                                 relief="flat", bd=0, highlightthickness=1,
                                 highlightbackground=self.c["border"], highlightcolor=self.c["accent"],
                                 width=14, justify="right")
                entry.pack(side="right")
                self._track(entry, "bg", "bg")
                self._track(entry, "fg", "fg")
                self._track(entry, "highlightbackground", "border")
                self._track(entry, "highlightcolor", "accent")
                self._track(entry, "insertbackground", "fg")

                if key in ("fib_time", "mat_time", "json_time", "prime_time", "str_time", "dict_time",
                           "memory_time", "list_time", "io_time"):
                    var.trace_add("write", lambda *args, k=key: self._update_editor_calc())
            else:
                vf = ("Segoe UI", 22, "bold") if (accent and big) else ("Segoe UI", 11, "bold")
                vf_fg = "accent" if (accent and big) else "fg"
                lv = tk.Label(rf, textvariable=var, font=vf)
                lv.pack(side="right")
                self._track(lv, "bg", bg_role)
                self._track(lv, "fg", vf_fg)

            if i < len(items) - 1:
                s2 = tk.Frame(inner, height=1)
                s2.pack(fill="x", pady=(8, 0))
                self._track(s2, "bg", "border")

        card.update_height()

    def _update_editor_calc(self):
        BASELINE = {"fib_10m": 300.0, "matmul_512": 5.0, "json_200k": 0.5}
        NEO_BASELINE = {"prime_10m": 2.5, "str_regex_100k": 3.0, "dict_500k": 1.5}
        GEN2_BASELINE = {
            "fib_10m": 300.0, "matmul_512": 5.0, "json_200k": 0.5,
            "prime_10m": 2.5, "str_regex_100k": 3.0, "dict_500k": 1.5,
            "memory_50m": 0.3, "list_ops_500k": 4.0, "io_1m": 1.0
        }
        gen2_weights = {
            "fib_10m": 0.20, "matmul_512": 0.15, "json_200k": 0.10,
            "prime_10m": 0.15, "str_regex_100k": 0.10, "dict_500k": 0.10,
            "memory_50m": 0.10, "list_ops_500k": 0.05, "io_1m": 0.05
        }

        def get_float(key):
            var = self.editor_vars.get(key)
            if not var:
                return 0.0
            try:
                return float(var.get() or 0)
            except ValueError:
                return 0.0

        # 得分映射: baseline_key -> (score_key, time_key, baseline_dict)
        score_map = {
            "fib_10m": ("fib_score", "fib_time", BASELINE),
            "matmul_512": ("mat_score", "mat_time", BASELINE),
            "json_200k": ("json_score", "json_time", BASELINE),
            "prime_10m": ("prime_score", "prime_time", NEO_BASELINE),
            "str_regex_100k": ("str_score", "str_time", NEO_BASELINE),
            "dict_500k": ("dict_score", "dict_time", NEO_BASELINE),
            "memory_50m": ("memory_score", "memory_time", GEN2_BASELINE),
            "list_ops_500k": ("list_score", "list_time", GEN2_BASELINE),
            "io_1m": ("io_score", "io_time", GEN2_BASELINE),
        }

        # 计算所有选中项目的单项得分
        scores = {}
        for key in self.editor_selected_items:
            if key not in score_map:
                continue
            score_key, time_key, baseline = score_map[key]
            t = get_float(time_key)
            score = round((baseline[key] / t) * 1000, 0) if t > 0 else 0
            scores[key] = score
            if score_key in self.editor_vars:
                self.editor_vars[score_key].set(str(int(score)) if score > 0 else "-")

        # 计算归一化总分（按已选项目的 Gen2 权重动态归一化）
        filled_scores = {}
        filled_weights = {}
        for key in self.editor_selected_items:
            if key in scores and scores[key] > 0 and key in gen2_weights:
                filled_scores[key] = scores[key]
                filled_weights[key] = gen2_weights[key]

        total_w = sum(filled_weights.values())
        normalized_total = 0
        if total_w > 0:
            normalized_total = round(
                sum(filled_scores[k] * (filled_weights[k] / total_w) for k in filled_scores), 0)

        mode = self.editor_mode_var.get()
        total_key = {
            "classic": "total_score",
            "neo": "neo_total_score",
            "gen2": "gen2_total_score",
            "custom": "custom_total_score"
        }.get(mode, "total_score")

        if total_key in self.editor_vars:
            self.editor_vars[total_key].set(str(int(normalized_total)) if normalized_total > 0 else "-")
    def _show_editor(self):
        self.page_dashboard.grid_remove()
        self.page_convert.grid_remove()
        self.page_editor.grid()
        self.active_page = "editor"
        self._update_nav_buttons("制作结果")
        self._update_editor_calc()

    def _update_nav_buttons(self, active_text):
        buttons = {
            "结果面板": self.btn_dashboard,
            "制作结果": self.btn_editor,
            "转换工具": self.btn_convert,
            "切换主题": self.btn_theme,
            "退出": self.btn_exit,
        }
        for text, btn in buttons.items():
            role = "btn_primary" if text == active_text else "btn_secondary"
            btn.configure(bg=self.c[role], fg=self.c["fg"], activeforeground=self.c["fg"])

    def _verify_password(self):
        c = self.c
        dlg = tk.Toplevel(self.root)
        dlg.title("安全验证")
        dlg.configure(bg=c["card"])
        dlg.transient(self.root)
        dlg.grab_set()
        dlg.resizable(False, False)

        # 大尺寸对话框
        W, H = 960, 1400
        dlg.geometry(f"{W}x{H}")
        dlg.update_idletasks()
        x = (dlg.winfo_screenwidth() - W) // 2
        y = max(0, (dlg.winfo_screenheight() - H) // 2)
        dlg.geometry(f"+{x}+{y}")

        # 仅标题栏应用 Win11 DWM 毛玻璃效果（不扩展客户区）
        if sys.platform == 'win32':
            try:
                hwnd = ctypes.windll.user32.GetParent(dlg.winfo_id())
                ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(ctypes.c_int(1)), 4)
                ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 33, ctypes.byref(ctypes.c_int(2)), 4)
                ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 38, ctypes.byref(ctypes.c_int(3)), 4)
                # 只扩展顶部边距，让标题栏有毛玻璃，内容区不受影响
                ctypes.windll.dwmapi.DwmExtendFrameIntoClientArea(hwnd, ctypes.byref(MARGINS(0, 0, 1, 0)))
            except Exception:
                pass

        # 主内容区 - 使用 card 纯色背景，覆盖整个客户区
        container = tk.Frame(dlg, bg=c["card"])
        container.pack(fill="both", expand=True, padx=60, pady=(60, 48))

        # 锁图标
        l_icon = tk.Label(container, text="🔒", font=("Segoe UI", 32),
                          bg=c["card"], fg=c["accent"])
        l_icon.pack(anchor="w", pady=(0, 24))

        # 标题 - 使用硬编码深色确保任何主题下都可见
        title_fg = "#1a1a1a" if self.theme == "light" else "#ffffff"
        l_title = tk.Label(container, text="需要密码验证", font=("Segoe UI", 22, "bold"),
                           bg=c["card"], fg=title_fg)
        l_title.pack(anchor="w")

        # 副标题
        sub_fg = "#5f5f5f" if self.theme == "light" else "#a0a0a0"
        l_sub = tk.Label(container, text="输入密码以生成加密结果文件", font=("Segoe UI", 11),
                         bg=c["card"], fg=sub_fg)
        l_sub.pack(anchor="w", pady=(8, 56))

        pwd_var = tk.StringVar()
        result = [False]
        error_var = tk.StringVar(value="")

        # 输入框区域
        input_frame = tk.Frame(container, bg=c["card"])
        input_frame.pack(fill="x", pady=(0, 12))

        entry_fg = "#1a1a1a" if self.theme == "light" else "#ffffff"
        entry = tk.Entry(input_frame, textvariable=pwd_var, show="●", 
                         font=("Segoe UI", 13), bg=c["card"], fg=entry_fg, 
                         insertbackground=c["accent"], insertwidth=2,
                         relief="flat", bd=0, highlightthickness=0)
        entry.pack(fill="x", ipady=10)
        entry.focus()

        # 底部下划线
        underline = tk.Frame(input_frame, bg=c["accent"], height=2)
        underline.pack(fill="x", pady=(4, 0))

        # 错误提示
        error_lbl = tk.Label(container, textvariable=error_var, font=("Segoe UI", 10),
                             bg=c["card"], fg="#ff4444")
        error_lbl.pack(anchor="w", pady=(12, 0))

        def _check():
            if pwd_var.get() == "mxt20060818":
                result[0] = True
                dlg.destroy()
            else:
                error_var.set("密码错误，请重试")
                underline.configure(bg="#ff4444")

        def _on_input(*args):
            if error_var.get():
                error_var.set("")
                underline.configure(bg=c["accent"])

        pwd_var.trace_add("write", _on_input)

        # 按钮区域（固定在底部）
        btn_frame = tk.Frame(container, bg=c["card"])
        btn_frame.pack(fill="x", pady=(80, 0), side="bottom")

        # 取消按钮
        cancel_fg = "#1a1a1a" if self.theme == "light" else "#ffffff"
        tk.Button(btn_frame, text="取消", command=dlg.destroy,
                  font=("Segoe UI", 11), bg=c["card"], fg=cancel_fg,
                  activebackground=c["card"], activeforeground=c["accent"],
                  bd=0, padx=24, pady=10, cursor="hand2").pack(side="right", padx=(12, 0))

        # 确认按钮
        tk.Button(btn_frame, text="确认", command=_check,
                  font=("Segoe UI", 11, "bold"), bg=c["btn_primary"], fg="white",
                  activebackground=c["accent"], activeforeground="white",
                  bd=0, padx=32, pady=10, cursor="hand2").pack(side="right")

        entry.bind("<Return>", lambda e: _check())

        dlg.wait_window(dlg)
        return result[0]


    def _load_existing_to_editor(self):
        """选择已有 .wnpbr 文件，解密后填充到制作结果表单"""
        path = filedialog.askopenfilename(
            filetypes=[("Catchmark 结果文件", "*.wnpbr"), ("所有文件", "*.*")]
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                decrypted = decrypt(f.read())
            data = json.loads(decrypted)

            # 自动切换编辑器模式（必须先切换，否则会清空已填充的数据）
            file_mode = data.get("mode", "classic")
            if file_mode in ("neo", "gen2", "custom"):
                self._set_editor_mode(file_mode)
            else:
                self._set_editor_mode("classic")

            # 填充到 editor_vars（在模式切换重建卡片之后填充）
            for key, var in self.editor_vars.items():
                val = data.get(key)
                if val is not None:
                    var.set(str(val))
                else:
                    var.set("")

            self._update_editor_calc()
            self._update_editor_calc()
            messagebox.showinfo("加载成功", "已加载：" + os.path.basename(path) + chr(10) + "可修改后重新生成加密文件。")
        except Exception as e:
            messagebox.showerror("加载失败", "无法解密或解析该文件：" + chr(10) + str(e))


    def _do_generate(self):
        if not self._verify_password():
            return

        # 只收集系统信息 + 选中项目的字段
        data = {}
        system_keys = {"cpu", "python", "cores", "timestamp"}
        for key, var in self.editor_vars.items():
            if key in system_keys or any(key in [item[1] for item in EDITOR_CARD_DEFS.get(k, [])] for k in self.editor_selected_items):
                data[key] = var.get()

        float_keys = ["fib_time", "mat_time", "json_time", "mat_gflops", "mat_checksum", "json_size_mb",
                      "prime_time", "str_time", "dict_time",
                      "memory_time", "memory_bandwidth", "list_time", "io_time",
                      "gil_single_time", "gil_multi_time", "gil_speedup", "gil_efficiency"]
        int_keys = ["fib_digits", "fib_score", "mat_score", "json_score", "total_score", "cores",
                    "prime_count", "prime_score", "str_matches", "str_score", "dict_size", "dict_hits", "dict_score",
                    "memory_score", "list_length", "list_score", "io_lines", "io_score", "gen2_total_score"]

        for k in float_keys:
            try:
                data[k] = float(data.get(k, 0) or 0)
            except (ValueError, TypeError):
                data[k] = 0.0

        for k in int_keys:
            try:
                data[k] = int(float(data.get(k, 0) or 0))
            except (ValueError, TypeError):
                data[k] = 0

        mode = self.editor_mode_var.get()

        BASELINE = {"fib_10m": 300.0, "matmul_512": 5.0, "json_200k": 0.5}
        NEO_BASELINE = {"prime_10m": 2.5, "str_regex_100k": 3.0, "dict_500k": 1.5}
        GEN2_BASELINE = {
            "fib_10m": 300.0, "matmul_512": 5.0, "json_200k": 0.5,
            "prime_10m": 2.5, "str_regex_100k": 3.0, "dict_500k": 1.5,
            "memory_50m": 0.3, "list_ops_500k": 4.0, "io_1m": 1.0
        }
        gen2_weights = {
            "fib_10m": 0.20, "matmul_512": 0.15, "json_200k": 0.10,
            "prime_10m": 0.15, "str_regex_100k": 0.10, "dict_500k": 0.10,
            "memory_50m": 0.10, "list_ops_500k": 0.05, "io_1m": 0.05
        }

        score_map = {
            "fib_10m": ("fib_score", "fib_time", BASELINE),
            "matmul_512": ("mat_score", "mat_time", BASELINE),
            "json_200k": ("json_score", "json_time", BASELINE),
            "prime_10m": ("prime_score", "prime_time", NEO_BASELINE),
            "str_regex_100k": ("str_score", "str_time", NEO_BASELINE),
            "dict_500k": ("dict_score", "dict_time", NEO_BASELINE),
            "memory_50m": ("memory_score", "memory_time", GEN2_BASELINE),
            "list_ops_500k": ("list_score", "list_time", GEN2_BASELINE),
            "io_1m": ("io_score", "io_time", GEN2_BASELINE),
        }

        # 计算选中项目的单项得分
        for key in self.editor_selected_items:
            if key not in score_map:
                continue
            score_key, time_key, baseline = score_map[key]
            t = data.get(time_key, 0)
            if t > 0 and data.get(score_key, 0) == 0:
                data[score_key] = round((baseline[key] / t) * 1000, 0)

        # 计算归一化总分
        filled_scores = {}
        filled_weights = {}
        for key in self.editor_selected_items:
            if key in score_map:
                score_key, _, _ = score_map[key]
                if data.get(score_key, 0) > 0:
                    filled_scores[key] = data[score_key]
                    filled_weights[key] = gen2_weights[key]

        total_w = sum(filled_weights.values())
        normalized_total = 0
        if total_w > 0:
            normalized_total = round(sum(filled_scores[k] * (filled_weights[k] / total_w) for k in filled_scores), 0)

        data["classic_total_score"] = normalized_total

        if mode == "neo":
            data["mode"] = "neo"
            data["neo_mode"] = True
            data["neo_total_score"] = normalized_total
            save_name = "Benchmark_Result_manual_Neo.wnpbr"
        elif mode == "gen2":
            data["mode"] = "gen2"
            data["gen2_mode"] = True
            data["gen2_total_score"] = normalized_total
            save_name = "Benchmark_Result_manual_Gen2.wnpbr"
        elif mode == "custom":
            data["mode"] = "custom"
            data["custom_mode"] = True
            data["custom_total_score"] = normalized_total
            data["custom_weights"] = {k: round(v / total_w, 4) for k, v in filled_weights.items()} if total_w > 0 else {}
            save_name = "Benchmark_Result_manual_Custom.wnpbr"
        else:
            data["mode"] = "classic"
            save_name = "Benchmark_Result_manual.wnpbr"

        save_path = self._save_encrypted(data, save_name)
        if save_path:
            msg = {"classic": "经典版", "neo": "Neo 版", "gen2": "Gen2 版", "custom": "客制化版"}[mode]
            messagebox.showinfo("生成成功", f"{msg} 加密结果文件已保存：" + chr(10) + save_path)
    def _build_convert_content(self):
        content = tk.Frame(self.page_convert, bg=self.c["bg"])
        content.grid(row=1, column=0, sticky="nsew")
        self._track(content, "bg", "bg")

        # 卡片 1：旧版本结果文件转换
        card1 = tk.Frame(content, bg=self.c["card"], padx=24, pady=20)
        card1.pack(fill="x", pady=(0, 12))
        self._track(card1, "bg", "card")

        t1 = tk.Label(card1, text="旧版本结果文件转换", font=("Segoe UI", 14, "bold"),
                      bg=self.c["card"], fg=self.c["fg"])
        t1.pack(anchor="w")
        self._track(t1, "bg", "card")
        self._track(t1, "fg", "fg")

        desc1 = tk.Label(card1, text="选择旧版本未加密的 .wnpbr 文件，程序将自动识别格式并转换为新版加密文件。",
                         font=("Segoe UI", 11), bg=self.c["card"], fg=self.c["muted"], wraplength=800)
        desc1.pack(anchor="w", pady=(8, 0))
        self._track(desc1, "bg", "card")
        self._track(desc1, "fg", "muted")

        self.convert_path_var = tk.StringVar(value="未选择文件")
        pl = tk.Label(card1, textvariable=self.convert_path_var, font=("Segoe UI", 11),
                      bg=self.c["card"], fg=self.c["fg"])
        pl.pack(anchor="w", pady=(12, 0))
        self._track(pl, "bg", "card")
        self._track(pl, "fg", "fg")

        bf1 = tk.Frame(card1, bg=self.c["card"])
        bf1.pack(fill="x", pady=(12, 0))
        self._track(bf1, "bg", "card")

        self.conv_btn1 = tk.Button(bf1, text="选择旧版文件", command=self._select_old_file,
                       font=("Segoe UI", 10), bg=self.c["btn_secondary"], fg=self.c["fg"],
                       activebackground=self.c["accent"], activeforeground=self.c["fg"],
                       bd=0, padx=12, pady=8, cursor="hand2")
        self.conv_btn1.pack(side="left", padx=(0, 8))
        self._track(self.conv_btn1, "bg", "btn_secondary")
        self._track(self.conv_btn1, "fg", "fg")
        self._track(self.conv_btn1, "activebackground", "accent")
        self._track(self.conv_btn1, "activeforeground", "fg")

        self.conv_btn2 = tk.Button(bf1, text="转换并保存", command=self._do_file_convert,
                       font=("Segoe UI", 10), bg=self.c["btn_primary"], fg=self.c["fg"],
                       activebackground=self.c["accent"], activeforeground=self.c["fg"],
                       bd=0, padx=12, pady=8, cursor="hand2")
        self.conv_btn2.pack(side="left")
        self._track(self.conv_btn2, "bg", "btn_primary")
        self._track(self.conv_btn2, "fg", "fg")
        self._track(self.conv_btn2, "activebackground", "accent")
        self._track(self.conv_btn2, "activeforeground", "fg")

        # 卡片 2：纯文本结果生成标准 wnpbr 文件
        card2 = tk.Frame(content, bg=self.c["card"], padx=24, pady=20)
        card2.pack(fill="x", pady=12)
        self._track(card2, "bg", "card")

        t2 = tk.Label(card2, text="纯文本结果生成标准 wnpbr 文件", font=("Segoe UI", 14, "bold"),
                      bg=self.c["card"], fg=self.c["fg"])
        t2.pack(anchor="w")
        self._track(t2, "bg", "card")
        self._track(t2, "fg", "fg")

        desc2 = tk.Label(card2, text="将纯文本跑分结果粘贴到下方文本框，程序将自动解析并生成标准加密的 .wnpbr 文件。",
                         font=("Segoe UI", 11), bg=self.c["card"], fg=self.c["muted"], wraplength=800)
        desc2.pack(anchor="w", pady=(8, 0))
        self._track(desc2, "bg", "card")
        self._track(desc2, "fg", "muted")

        text_frame = tk.Frame(card2, bg=self.c["border"], padx=1, pady=1)
        text_frame.pack(fill="both", expand=True, pady=(12, 0))
        self._track(text_frame, "bg", "border")

        self.text_input = tk.Text(text_frame, font=("Consolas", 10), wrap="word",
                                  bg=self.c["bg"], fg=self.c["fg"], insertbackground=self.c["fg"],
                                  relief="flat", bd=0, padx=12, pady=12, height=12)
        self.text_input.pack(fill="both", expand=True)
        self._track(self.text_input, "bg", "bg")
        self._track(self.text_input, "fg", "fg")
        self._track(self.text_input, "insertbackground", "fg")

        bf2 = tk.Frame(card2, bg=self.c["card"])
        bf2.pack(fill="x", pady=(12, 0))
        self._track(bf2, "bg", "card")

        self.conv_btn3 = tk.Button(bf2, text="清空", command=lambda: self.text_input.delete("1.0", "end"),
                       font=("Segoe UI", 10), bg=self.c["btn_secondary"], fg=self.c["fg"],
                       activebackground=self.c["accent"], activeforeground=self.c["fg"],
                       bd=0, padx=12, pady=8, cursor="hand2")
        self.conv_btn3.pack(side="left", padx=(0, 8))
        self._track(self.conv_btn3, "bg", "btn_secondary")
        self._track(self.conv_btn3, "fg", "fg")
        self._track(self.conv_btn3, "activebackground", "accent")
        self._track(self.conv_btn3, "activeforeground", "fg")

        self.conv_btn4 = tk.Button(bf2, text="转换并保存", command=self._do_text_convert,
                       font=("Segoe UI", 10), bg=self.c["btn_primary"], fg=self.c["fg"],
                       activebackground=self.c["accent"], activeforeground=self.c["fg"],
                       bd=0, padx=12, pady=8, cursor="hand2")
        self.conv_btn4.pack(side="left")
        self._track(self.conv_btn4, "bg", "btn_primary")
        self._track(self.conv_btn4, "fg", "fg")
        self._track(self.conv_btn4, "activebackground", "accent")
        self._track(self.conv_btn4, "activeforeground", "fg")

        # 状态栏
        self.convert_status_var = tk.StringVar(value="")
        sl = tk.Label(content, textvariable=self.convert_status_var, font=("Segoe UI", 11),
                      bg=self.c["bg"], fg=self.c["accent"])
        sl.pack(anchor="w", pady=12)
        self._track(sl, "bg", "bg")
        self._track(sl, "fg", "accent")

    def _show_dashboard(self):
        self.page_convert.grid_remove()
        self.page_editor.grid_remove()
        self.page_dashboard.grid()
        self.active_page = "dashboard"
        self._update_nav_buttons("结果面板")

    def _show_convert(self):
        self.page_dashboard.grid_remove()
        self.page_editor.grid_remove()
        self.page_convert.grid()
        self.active_page = "convert"
        self._update_nav_buttons("转换工具")

    def _select_old_file(self):
        path = filedialog.askopenfilename(filetypes=[("Catchmark 文件", "*.wnpbr"), ("所有文件", "*.*")])
        if path:
            self.convert_path_var.set(path)
            self.convert_status_var.set("")

    # ============ 关键修正：针对新版终端输出的精确解析 ============
    def _parse_legacy_text(self, text):
        """从终端输出文本中提取数据，兼容经典/Neo/Gen2三种格式"""
        data = {
            "cpu": "Unknown", "python": "Unknown", "cores": "Unknown", "timestamp": "Unknown",
            "fib_time": 0.0, "fib_digits": 0, "fib_score": 0,
            "mat_time": 0.0, "mat_gflops": 0.0, "mat_checksum": 0.0, "mat_score": 0,
            "json_time": 0.0, "json_size_mb": 0.0, "json_sha16": "-", "json_score": 0,
            "total_score": 0
        }

        # 检测模式
        is_gen2 = "Gen2" in text or "G E N 2" in text or "内存带宽" in text or "[7/10]" in text
        is_neo = not is_gen2 and ("Neo 扩展测试" in text or "[4/6]" in text or "素数筛" in text)

        # 1. 系统信息
        m = re.search(r'CPU\s*型号[:：]\s*(.+)', text)
        if m:
            data["cpu"] = m.group(1).strip()

        m = re.search(r'Python[:：]\s*([\d.]+)', text)
        if m:
            data["python"] = m.group(1).strip()

        m = re.search(r'逻辑核心[:：]\s*(\d+)', text)
        if m:
            data["cores"] = m.group(1).strip()

        # 2. 斐波那契
        fib_section = re.search(r'(?:大整数累加|斐波那契).*?(?=(?:矩阵乘法|浮点矩阵|JSON|={10,}|$))', text, re.DOTALL)
        if fib_section:
            sec = fib_section.group(0)
            m = re.search(r'结果位数[:：]\s*([\d,]+)', sec)
            if m:
                data["fib_digits"] = int(m.group(1).replace(',', ''))
            m = re.search(r'耗时[:：]\s*([\d.]+)\s*(?:秒|s)?', sec, re.IGNORECASE)
            if m:
                data["fib_time"] = float(m.group(1))
            m = re.search(r'单项得分[:：]?\s*([\d,]+)', sec)
            if m:
                data["fib_score"] = int(m.group(1).replace(',', ''))

        # 3. 矩阵乘法
        mat_section = re.search(r'(?:矩阵乘法|浮点矩阵).*?(?=(?:JSON|混合负载|={10,}|$))', text, re.DOTALL)
        if mat_section:
            sec = mat_section.group(0)
            m = re.search(r'耗时[:：]\s*([\d.]+)\s*(?:秒|s)?', sec, re.IGNORECASE)
            if m:
                data["mat_time"] = float(m.group(1))
            m = re.search(r'(?:等效\s*)?GFLOPS[:：]\s*([\d.]+)', sec, re.IGNORECASE)
            if m:
                data["mat_gflops"] = float(m.group(1))
            m = re.search(r'校验和[:：]\s*([\d.]+)', sec)
            if m:
                data["mat_checksum"] = float(m.group(1))
            m = re.search(r'单项得分[:：]?\s*([\d,]+)', sec)
            if m:
                data["mat_score"] = int(m.group(1).replace(',', ''))

        # 4. JSON
        json_section = re.search(r'(?:JSON|混合负载).*?(?=(?:综合评分|经典测试|={10,}|$))', text, re.DOTALL)
        if json_section:
            sec = json_section.group(0)
            m = re.search(r'耗时[:：]\s*([\d.]+)\s*(?:秒|s)?', sec, re.IGNORECASE)
            if m:
                data["json_time"] = float(m.group(1))
            m = re.search(r'JSON\s*大小[:：]\s*([\d.]+)\s*MB', sec, re.IGNORECASE)
            if m:
                data["json_size_mb"] = float(m.group(1))
            m = re.search(r'SHA256\s*前缀[:：]\s*([a-fA-F0-9]{8,})', sec, re.IGNORECASE)
            if m:
                data["json_sha16"] = m.group(1)[:16]
            m = re.search(r'单项得分[:：]?\s*([\d,]+)', sec)
            if m:
                data["json_score"] = int(m.group(1).replace(',', ''))

        # 5. 经典综合得分
        classic_section = re.search(r'经典测试评分报告.*?(?=(?:Neo|N E O|Gen2|G E N 2|素数筛|$))', text, re.DOTALL)
        if classic_section:
            sec = classic_section.group(0)
            m = re.search(r'经典综合得分[:：]?\s*([\d,]+)', sec)
            if m:
                data["classic_total_score"] = int(m.group(1).replace(',', ''))

        # 6. 计算缺失的经典得分
        BASELINE = {"fib_10m": 300.0, "matmul_512": 5.0, "json_200k": 0.5}
        weights = {"fib_10m": 0.4, "matmul_512": 0.3, "json_200k": 0.3}

        if data["fib_score"] == 0 and data["fib_time"] > 0:
            data["fib_score"] = round((BASELINE["fib_10m"] / data["fib_time"]) * 1000, 0)
        if data["mat_score"] == 0 and data["mat_time"] > 0:
            data["mat_score"] = round((BASELINE["matmul_512"] / data["mat_time"]) * 1000, 0)
        if data["json_score"] == 0 and data["json_time"] > 0:
            data["json_score"] = round((BASELINE["json_200k"] / data["json_time"]) * 1000, 0)

        data["classic_total_score"] = round(
            data["fib_score"] * weights["fib_10m"] +
            data["mat_score"] * weights["matmul_512"] +
            data["json_score"] * weights["json_200k"], 0)

        # 7. Neo 扩展项（如果存在）
        if is_neo or is_gen2:
            data["mode"] = "gen2" if is_gen2 else "neo"
            data["neo_mode"] = True

            # 素数筛
            prime_sec = re.search(r'素数筛.*?(?=(?:字符串|字典|内存|列表|I/O|GIL|={10,}|$))', text, re.DOTALL)
            if prime_sec:
                sec = prime_sec.group(0)
                m = re.search(r'耗时[:：]\s*([\d.]+)\s*(?:秒|s)?', sec, re.IGNORECASE)
                if m:
                    data["prime_time"] = float(m.group(1))
                m = re.search(r'素数个数[:：]\s*([\d,]+)', sec)
                if m:
                    data["prime_count"] = int(m.group(1).replace(',', ''))
                m = re.search(r'单项得分[:：]?\s*([\d,]+)', sec)
                if m:
                    data["prime_score"] = int(m.group(1).replace(',', ''))

            # 字符串处理
            str_sec = re.search(r'字符串处理.*?(?=(?:字典|内存|列表|I/O|GIL|={10,}|$))', text, re.DOTALL)
            if str_sec:
                sec = str_sec.group(0)
                m = re.search(r'耗时[:：]\s*([\d.]+)\s*(?:秒|s)?', sec, re.IGNORECASE)
                if m:
                    data["str_time"] = float(m.group(1))
                m = re.search(r'匹配次数[:：]\s*([\d,]+)', sec)
                if m:
                    data["str_matches"] = int(m.group(1).replace(',', ''))
                m = re.search(r'单项得分[:：]?\s*([\d,]+)', sec)
                if m:
                    data["str_score"] = int(m.group(1).replace(',', ''))

            # 字典运算
            dict_sec = re.search(r'字典运算.*?(?=(?:内存|列表|I/O|GIL|Neo|N E O|Gen2|G E N 2|综合|={10,}|$))', text, re.DOTALL)
            if dict_sec:
                sec = dict_sec.group(0)
                m = re.search(r'耗时[:：]\s*([\d.]+)\s*(?:秒|s)?', sec, re.IGNORECASE)
                if m:
                    data["dict_time"] = float(m.group(1))
                m = re.search(r'字典大小[:：]\s*([\d,]+)', sec)
                if m:
                    data["dict_size"] = int(m.group(1).replace(',', ''))
                m = re.search(r'查找命中[:：]\s*([\d,]+)', sec)
                if m:
                    data["dict_hits"] = int(m.group(1).replace(',', ''))
                m = re.search(r'单项得分[:：]?\s*([\d,]+)', sec)
                if m:
                    data["dict_score"] = int(m.group(1).replace(',', ''))

            # Neo 综合得分
            neo_sec = re.search(r'Neo\s*综合得分[:：]?\s*([\d,]+)', text)
            if neo_sec:
                data["neo_total_score"] = int(neo_sec.group(1).replace(',', ''))

        # 8. Gen2 扩展项
        if is_gen2:
            data["gen2_mode"] = True

            # 内存带宽
            mem_sec = re.search(r'内存带宽.*?(?=(?:列表|I/O|GIL|={10,}|$))', text, re.DOTALL)
            if mem_sec:
                sec = mem_sec.group(0)
                m = re.search(r'耗时[:：]\s*([\d.]+)\s*(?:秒|s)?', sec, re.IGNORECASE)
                if m:
                    data["memory_time"] = float(m.group(1))
                m = re.search(r'等效带宽[:：]\s*([\d.]+)\s*MB/s', sec, re.IGNORECASE)
                if m:
                    data["memory_bandwidth"] = float(m.group(1))
                m = re.search(r'单项得分[:：]?\s*([\d,]+)', sec)
                if m:
                    data["memory_score"] = int(m.group(1).replace(',', ''))

            # 列表操作
            list_sec = re.search(r'列表操作.*?(?=(?:I/O|GIL|={10,}|$))', text, re.DOTALL)
            if list_sec:
                sec = list_sec.group(0)
                m = re.search(r'耗时[:：]\s*([\d.]+)\s*(?:秒|s)?', sec, re.IGNORECASE)
                if m:
                    data["list_time"] = float(m.group(1))
                m = re.search(r'最终长度[:：]\s*([\d,]+)', sec)
                if m:
                    data["list_length"] = int(m.group(1).replace(',', ''))
                m = re.search(r'单项得分[:：]?\s*([\d,]+)', sec)
                if m:
                    data["list_score"] = int(m.group(1).replace(',', ''))

            # I/O 吞吐
            io_sec = re.search(r'I/O\s*吞吐.*?(?=(?:GIL|={10,}|$))', text, re.DOTALL)
            if io_sec:
                sec = io_sec.group(0)
                m = re.search(r'耗时[:：]\s*([\d.]+)\s*(?:秒|s)?', sec, re.IGNORECASE)
                if m:
                    data["io_time"] = float(m.group(1))
                m = re.search(r'二进制大小[:：]\s*([\d.]+)\s*KB', sec, re.IGNORECASE)
                if m:
                    data["io_bin_kb"] = float(m.group(1))
                m = re.search(r'文本行数[:：]\s*([\d,]+)', sec)
                if m:
                    data["io_lines"] = int(m.group(1).replace(',', ''))
                m = re.search(r'单项得分[:：]?\s*([\d,]+)', sec)
                if m:
                    data["io_score"] = int(m.group(1).replace(',', ''))

            # GIL 并发
            gil_sec = re.search(r'GIL\s*并发.*?(?=(?:Gen2|G E N 2|综合|={10,}|$))', text, re.DOTALL)
            if gil_sec:
                sec = gil_sec.group(0)
                m = re.search(r'单线程耗时[:：]\s*([\d.]+)\s*s', sec)
                if m:
                    data["gil_single_time"] = float(m.group(1))
                m = re.search(r'多线程耗时[:：]\s*([\d.]+)\s*s', sec)
                if m:
                    data["gil_multi_time"] = float(m.group(1))
                m = re.search(r'实际加速比[:：]\s*([\d.]+)x', sec)
                if m:
                    data["gil_speedup"] = float(m.group(1))
                m = re.search(r'并发效率[:：]\s*([\d.]+)%', sec)
                if m:
                    data["gil_efficiency"] = float(m.group(1)) / 100

            # Gen2 综合得分
            gen2_sec = re.search(r'Gen2\s*综合得分[:：]?\s*([\d,]+)', text)
            if gen2_sec:
                data["gen2_total_score"] = int(gen2_sec.group(1).replace(',', ''))

        # 9. 补充系统信息
        if data["cpu"] == "Unknown":
            data["cpu"] = get_cpu_name()
        if data["python"] == "Unknown":
            data["python"] = get_python_version()
        if data["cores"] == "Unknown":
            data["cores"] = get_core_count()

        return data

    def _save_encrypted(self, data, default_name):
        encrypted = encrypt(json.dumps(data, ensure_ascii=False, indent=2))
        save_path = filedialog.asksaveasfilename(
            defaultextension=".wnpbr", initialfile=default_name,
            filetypes=[("Catchmark 加密文件", "*.wnpbr"), ("所有文件", "*.*")]
        )
        if not save_path:
            return None
        with open(save_path, "w", encoding="utf-8") as f:
            f.write(encrypted)
        return save_path

    def _do_file_convert(self):
        if not self._verify_password():
            return
        path = self.convert_path_var.get()
        if not path or path == "未选择文件":
            self.convert_status_var.set("请先选择旧版文件")
            return

        try:
            with open(path, "r", encoding="utf-8") as f:
                plain = f.read()

            # 先尝试 JSON
            try:
                data = json.loads(plain)
                if "total_score" not in data:
                    data = self._parse_legacy_text(plain)
            except json.JSONDecodeError:
                data = self._parse_legacy_text(plain)

            # Gen2/Neo 模式警告
            if data.get("mode") in ("neo", "gen2") or data.get("neo_mode") is True or data.get("gen2_mode") is True:
                msg = "Neo" if data.get("mode") == "neo" else "Gen2"
                messagebox.showwarning(f"{msg} 模式提示", f"检测到该文件为 {msg} 扩展测试结果。\n{msg} 模式本身已是完整格式，无需转换。\n如需查看，请直接在结果面板中加载。")
                return

            missing = []
            if data.get("fib_time", 0) == 0:
                missing.append("斐波那契耗时")
            if data.get("mat_time", 0) == 0:
                missing.append("矩阵耗时")
            if data.get("json_time", 0) == 0:
                missing.append("JSON耗时")

            base = os.path.splitext(os.path.basename(path))[0]
            save_path = self._save_encrypted(data, f"{base}_encrypted.wnpbr")
            if not save_path:
                self.convert_status_var.set("已取消保存")
                return

            status = f"转换成功：{os.path.basename(save_path)}"
            if missing:
                status += f"（缺少 {'、'.join(missing)}）"
            self.convert_status_var.set(status)

        except Exception as e:
            self.convert_status_var.set(f"转换失败：{str(e)}")

    def _do_text_convert(self):
        if not self._verify_password():
            return
        text = self.text_input.get("1.0", "end").strip()
        if not text:
            self.convert_status_var.set("请先粘贴跑分结果文本")
            return

        try:
            data = self._parse_legacy_text(text)

            # Gen2/Neo 模式警告
            if data.get("mode") in ("neo", "gen2") or data.get("neo_mode") is True or data.get("gen2_mode") is True:
                msg = "Neo" if data.get("mode") == "neo" else "Gen2"
                messagebox.showwarning(f"{msg} 模式提示", f"检测到该文本为 {msg} 扩展测试结果。\n{msg} 模式本身已是完整格式，无需转换。\n如需查看，请直接在结果面板中加载。")
                self.convert_status_var.set(f"{msg} 文本无需转换")
                return

            missing = []
            if data.get("fib_time", 0) == 0:
                missing.append("斐波那契耗时")
            if data.get("mat_time", 0) == 0:
                missing.append("矩阵耗时")
            if data.get("json_time", 0) == 0:
                missing.append("JSON耗时")

            save_path = self._save_encrypted(data, "Benchmark_Result_converted.wnpbr")
            if not save_path:
                self.convert_status_var.set("已取消保存")
                return

            status = f"生成成功：{os.path.basename(save_path)}"
            if missing:
                status += f"（缺少 {'、'.join(missing)}，请检查文本完整性）"
            self.convert_status_var.set(status)

        except Exception as e:
            self.convert_status_var.set(f"生成失败：{str(e)}")

    def toggle_theme(self):
        self.theme = "light" if self.theme == "dark" else "dark"
        self.c = PALETTE[self.theme]

        self.root.configure(bg=TRANSPARENT)
        self.root.wm_attributes('-transparentcolor', TRANSPARENT)

        if sys.platform == 'win32':
            self.root.update_idletasks()
            apply_win11(ctypes.windll.user32.GetParent(self.root.winfo_id()))

        for widget, attr, role in self.tracked:
            try:
                widget.configure(**{attr: self.c[role]})
            except tk.TclError:
                pass

        for card, bg_role in self.cards:
            card.set_color(self.c[bg_role], self.c["border"])

        for card, bg_role in self.editor_cards:
            card.set_color(self.c[bg_role], self.c["border"])

        # 显式更新所有已知按钮的文字颜色（Windows tkinter Button fg 有时不响应 _track）
        all_buttons = [
            getattr(self, 'dash_load_btn', None),
            getattr(self, 'editor_btn_load', None),
            getattr(self, 'editor_btn_gen', None),
            getattr(self, 'conv_btn1', None),
            getattr(self, 'conv_btn2', None),
            getattr(self, 'conv_btn3', None),
            getattr(self, 'conv_btn4', None),
        ]
        for btn in all_buttons:
            if btn:
                try:
                    btn.configure(fg=self.c["fg"], activeforeground=self.c["fg"])
                except tk.TclError:
                    pass

        page_map = {
            "dashboard": "结果面板",
            "convert": "转换工具",
            "editor": "制作结果"
        }
        self._update_nav_buttons(page_map.get(self.active_page, "结果面板"))

    def open_file(self):
        path = filedialog.askopenfilename(filetypes=[("Catchmark 结果文件", "*.wnpbr"), ("所有文件", "*.*")])
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                decrypted = decrypt(f.read())
            data = json.loads(decrypted)
            self.path_var.set(os.path.basename(path))
            self._fill(data)
            self._show_dashboard()
        except Exception as e:
            messagebox.showerror("读取失败", f"无法解密或解析该文件：\n{e}")

    def _fill(self, data):
        # 检测模式并重建布局
        is_gen2 = data.get("mode") == "gen2" or data.get("gen2_mode") is True
        is_neo = data.get("mode") == "neo" or data.get("neo_mode") is True
        is_custom = data.get("mode") == "custom" or data.get("custom_mode") is True
        new_mode = "custom" if is_custom else ("gen2" if is_gen2 else ("neo" if is_neo else "classic"))
        if new_mode != getattr(self, "current_mode", "classic"):
            self._rebuild_dashboard(new_mode)

        # 填充数据
        for key, var in self.fields.items():
            val = data.get(key)
            var.set(str(val) if val is not None else "-")

    def _on_mousewheel(self, event):
        if self.active_page == "dashboard":
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        elif self.active_page == "editor":
            self.editor_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _check_cli_args(self):
        """检查命令行参数，自动加载 .wnpbr 文件"""
        if len(sys.argv) > 1:
            path = sys.argv[1]
            if os.path.isfile(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        decrypted = decrypt(f.read())
                    data = json.loads(decrypted)
                    self.path_var.set(os.path.basename(path))
                    self._fill(data)
                    self._show_dashboard()
                except Exception as e:
                    messagebox.showerror("读取失败", f"无法解密或解析该文件：\n{e}")

    def _dummy(self):
        pass

if __name__ == "__main__":
    root = tk.Tk()
    app = Viewer(root)
    root.mainloop()
