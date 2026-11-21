import ctypes
import sys
import tkinter as tk
from tkinter import filedialog, messagebox
import secrets
import csv
from datetime import datetime

# ============ DPI 感知 ============
if sys.platform == 'win32':
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        ctypes.windll.user32.SetProcessDPIAware()

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

# ============ 密钥算法 ============
CHARSET = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"
GEN_MAP = {1: "2", 2: "3"}

def char_to_val(c: str) -> int:
    return CHARSET.index(c.upper())

def val_to_char(v: int) -> str:
    return CHARSET[v & 0x1F]

def compute_checksum(key20: str) -> str:
    h = 0x12345678
    for i, c in enumerate(key20):
        v = char_to_val(c)
        h ^= (v << (i % 27))
        h = ((h << 3) | (h >> 29)) & 0xFFFFFFFF
        h = (h + v * 2654435761) & 0xFFFFFFFF
        h ^= (v >> (i % 3 + 1))
    result = ""
    for i in range(5):
        n = (h >> (i * 5)) & 0x1F
        result += val_to_char(n)
    return result

def generate_key(key_type: str, gen: int = 2) -> str:
    if key_type not in ("V", "D", "A"):
        raise ValueError("key_type must be V, D, or A")
    if gen not in GEN_MAP:
        raise ValueError("gen must be 1 or 2")
    gen_id = GEN_MAP[gen]
    group1 = gen_id + key_type + "".join(secrets.choice(CHARSET) for _ in range(3))
    payload = "".join(secrets.choice(CHARSET) for _ in range(15))
    key20 = group1 + payload
    checksum = compute_checksum(key20)
    return f"{group1}-{payload[0:5]}-{payload[5:10]}-{payload[10:15]}-{checksum}"

def validate_key(key: str, expected_gen: int = None) -> tuple:
    stripped = key.upper().replace("-", "").replace(" ", "")
    if len(stripped) != 25:
        return False, "长度错误（应为25位）", None
    for c in stripped:
        if c not in CHARSET:
            return False, "包含非法字符", None
    gen = stripped[0]
    key_type = stripped[1]
    if expected_gen is not None and gen != GEN_MAP.get(expected_gen):
        return False, "Gen标识错误", None
    if key_type not in ("V", "D", "A"):
        return False, "类型标识错误（应为 V/D/A）", None
    checksum = stripped[20:25]
    expected = compute_checksum(stripped[0:20])
    if checksum != expected:
        return False, "校验和不匹配", None
    return True, "验证通过", key_type
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
class KeygenApp:
    def __init__(self, root):
        self.root, self.theme = root, "dark"
        self.c = PALETTE[self.theme]
        self.tracked, self.cards = [], []
        self.active_page = "generate"
        self.csv_pool = []

        root.title("WN-PBR Keygen")
        root.configure(bg=TRANSPARENT)
        root.wm_attributes('-transparentcolor', TRANSPARENT)

        root.geometry("2300x1200")
        root.minsize(1600, 900)

        if sys.platform == 'win32':
            root.update_idletasks()
            apply_win11(ctypes.windll.user32.GetParent(root.winfo_id()))

        root.grid_columnconfigure(1, weight=1)
        root.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_main()

    def _track(self, widget, attr, role):
        self.tracked.append((widget, attr, role))
        widget.configure(**{attr: self.c[role]})
        return widget

    def _build_sidebar(self):
        self.sidebar = tk.Frame(self.root, width=280, bg=TRANSPARENT)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        tk.Label(self.sidebar, text="WN-PBR", font=("Segoe UI", 26, "bold"),
                 bg=TRANSPARENT, fg=self.c["fg"]).pack(anchor="w", padx=30, pady=(40, 4))
        tk.Label(self.sidebar, text="Keygen", font=("Segoe UI", 10),
                 bg=TRANSPARENT, fg=self.c["fg"]).pack(anchor="w", padx=30, pady=(0, 40))

        self.btn_gen = self._btn("生成密钥", self._show_generate, "btn_primary")
        self.btn_gen.pack(fill="x", padx=20, pady=4)
        self.btn_verify = self._btn("验证密钥", self._show_verify, "btn_secondary")
        self.btn_verify.pack(fill="x", padx=20, pady=4)
        self.btn_csv = self._btn("CSV 导出池", self._show_csv, "btn_secondary")
        self.btn_csv.pack(fill="x", padx=20, pady=4)
        self.btn_theme = self._btn("切换主题", self.toggle_theme, "btn_secondary")
        self.btn_theme.pack(fill="x", padx=20, pady=4)
        self.btn_exit = self._btn("退出", self.root.destroy, "btn_secondary")
        self.btn_exit.pack(fill="x", padx=20, pady=4)

        tk.Label(self.sidebar, text="Gen1  ·  Wing North Studio",
                 font=("Segoe UI", 9), bg=TRANSPARENT, fg=self.c["muted"]).pack(
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

        # === 生成页面 ===
        self.page_gen = tk.Frame(self.main, bg=self.c["bg"])
        self.page_gen.grid(row=0, column=0, sticky="nsew", padx=40, pady=40)
        self.page_gen.grid_columnconfigure(0, weight=1)
        self._track(self.page_gen, "bg", "bg")

        title = tk.Label(self.page_gen, text="生成密钥", font=("Segoe UI", 32, "bold"),
                         bg=self.c["bg"], fg=self.c["fg"])
        title.grid(row=0, column=0, sticky="w", pady=(0, 24))
        self._track(title, "bg", "bg")
        self._track(title, "fg", "fg")

        # 配置卡片
        cfg_card = RoundedCard(self.page_gen, bg_color=self.c["card"], radius=16,
                               border_color=self.c["border"],
                               row=1, column=0, sticky="ew", pady=(0, 16))
        self.cards.append((cfg_card, "card"))
        inner = cfg_card.inner

        # 类型选择
        tf = tk.Frame(inner, bg=self.c["card"])
        tf.pack(fill="x", pady=(12, 8))
        self._track(tf, "bg", "card")

        tk.Label(tf, text="密钥类型", font=("Segoe UI", 12, "bold"),
                 bg=self.c["card"], fg=self.c["fg"]).pack(side="left")

        self.type_var = tk.StringVar(value="V")
        self.type_buttons = {}
        type_names = {"V": "Viewer 专用", "D": "Decryptor 专用", "A": "全能 (All-in-One)"}
        for val, name in type_names.items():
            btn = tk.Button(tf, text=name, font=("Segoe UI", 11),
                            bg=self.c["btn_primary"] if val == "V" else self.c["btn_secondary"],
                            fg=self.c["fg"], activebackground=self.c["accent"],
                            activeforeground=self.c["fg"], bd=0, padx=16, pady=6, cursor="hand2",
                            command=lambda v=val: self._set_type(v))
            btn.pack(side="left", padx=(12, 0))
            self.type_buttons[val] = btn
            self._track(btn, "activebackground", "accent")
            self._track(btn, "activeforeground", "fg")

        # 代数选择
        gf = tk.Frame(inner, bg=self.c["card"])
        gf.pack(fill="x", pady=(0, 8))
        self._track(gf, "bg", "card")

        tk.Label(gf, text="密钥代数", font=("Segoe UI", 12, "bold"),
                 bg=self.c["card"], fg=self.c["fg"]).pack(side="left")

        self.gen_var = tk.IntVar(value=2)
        self.gen_buttons = {}
        gen_names = {1: "Gen1", 2: "Gen2"}
        for val, name in gen_names.items():
            btn = tk.Button(gf, text=name, font=("Segoe UI", 11),
                            bg=self.c["btn_primary"] if val == 2 else self.c["btn_secondary"],
                            fg=self.c["fg"], activebackground=self.c["accent"],
                            activeforeground=self.c["fg"], bd=0, padx=16, pady=6, cursor="hand2",
                            command=lambda v=val: self._set_gen(v))
            btn.pack(side="left", padx=(12, 0))
            self.gen_buttons[val] = btn
            self._track(btn, "activebackground", "accent")
            self._track(btn, "activeforeground", "fg")

        # 数量
        nf = tk.Frame(inner, bg=self.c["card"])
        nf.pack(fill="x", pady=(8, 12))
        self._track(nf, "bg", "card")

        tk.Label(nf, text="生成数量", font=("Segoe UI", 12, "bold"),
                 bg=self.c["card"], fg=self.c["fg"]).pack(side="left")

        self.count_var = tk.StringVar(value="1")
        ent = tk.Entry(nf, textvariable=self.count_var, font=("Segoe UI", 11),
                       bg=self.c["bg"], fg=self.c["fg"], insertbackground=self.c["fg"],
                       relief="flat", bd=0, highlightthickness=1,
                       highlightbackground=self.c["border"], highlightcolor=self.c["accent"],
                       width=8, justify="center")
        ent.pack(side="left", padx=(16, 0))
        self._track(ent, "bg", "bg")
        self._track(ent, "fg", "fg")
        self._track(ent, "highlightbackground", "border")
        self._track(ent, "highlightcolor", "accent")
        self._track(ent, "insertbackground", "fg")

        # 生成按钮
        gen_btn = tk.Button(inner, text="生成密钥", command=self._do_generate,
                            font=("Segoe UI", 11, "bold"), bg=self.c["btn_primary"], fg=self.c["fg"],
                            activebackground=self.c["accent"], activeforeground=self.c["fg"],
                            bd=0, padx=20, pady=10, cursor="hand2")
        gen_btn.pack(anchor="w", pady=(8, 0))
        self._track(gen_btn, "bg", "btn_primary")
        self._track(gen_btn, "fg", "fg")
        self._track(gen_btn, "activebackground", "accent")
        self._track(gen_btn, "activeforeground", "fg")

        cfg_card.update_height()

        # 结果区域（带滚动）
        result_header = tk.Frame(self.page_gen, bg=self.c["bg"])
        result_header.grid(row=2, column=0, sticky="ew", pady=(24, 12))
        self._track(result_header, "bg", "bg")
        result_header.grid_columnconfigure(0, weight=1)

        result_title = tk.Label(result_header, text="生成结果", font=("Segoe UI", 18, "bold"),
                                bg=self.c["bg"], fg=self.c["fg"])
        result_title.grid(row=0, column=0, sticky="w")
        self._track(result_title, "bg", "bg")
        self._track(result_title, "fg", "fg")

        self.add_pool_btn = tk.Button(result_header, text="加入 CSV 导出池", command=self._add_to_csv_pool,
                                    font=("Segoe UI", 10), bg=self.c["btn_secondary"], fg=self.c["fg"],
                                    activebackground=self.c["accent"], activeforeground=self.c["fg"],
                                    bd=0, padx=16, pady=8, cursor="hand2")
        self.add_pool_btn.grid(row=0, column=1, sticky="e")
        self._track(self.add_pool_btn, "bg", "btn_secondary")
        self._track(self.add_pool_btn, "fg", "fg")
        self._track(self.add_pool_btn, "activebackground", "accent")
        self._track(self.add_pool_btn, "activeforeground", "fg")

        # 滚动容器
        scroll_wrap = tk.Frame(self.page_gen, bg=self.c["bg"])
        scroll_wrap.grid(row=3, column=0, sticky="nsew")
        self._track(scroll_wrap, "bg", "bg")
        self.page_gen.grid_rowconfigure(3, weight=1)

        scroll_wrap.grid_rowconfigure(0, weight=1)
        scroll_wrap.grid_columnconfigure(0, weight=1)

        self.result_canvas = tk.Canvas(scroll_wrap, highlightthickness=0, bg=self.c["bg"])
        self.result_canvas.grid(row=0, column=0, sticky="nsew")
        self._track(self.result_canvas, "bg", "bg")

        result_sb = tk.Scrollbar(scroll_wrap, orient="vertical", command=self.result_canvas.yview)
        result_sb.grid(row=0, column=1, sticky="ns")
        self.result_canvas.configure(yscrollcommand=result_sb.set)

        self.result_frame = tk.Frame(self.result_canvas, bg=self.c["bg"])
        self.result_frame_id = self.result_canvas.create_window((0, 0), window=self.result_frame, anchor="nw")
        self._track(self.result_frame, "bg", "bg")

        self.result_frame.bind("<Configure>", lambda e: self.result_canvas.configure(scrollregion=self.result_canvas.bbox("all")))
        self.result_canvas.bind("<Configure>", lambda e: self.result_canvas.itemconfig(self.result_frame_id, width=e.width))

        def _on_mousewheel(event):
            self.result_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        self.result_canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # === 验证页面 ===
        self.page_verify = tk.Frame(self.main, bg=self.c["bg"])
        self.page_verify.grid(row=0, column=0, sticky="nsew", padx=40, pady=40)
        self.page_verify.grid_columnconfigure(0, weight=1)
        self._track(self.page_verify, "bg", "bg")

        vtitle = tk.Label(self.page_verify, text="验证密钥", font=("Segoe UI", 32, "bold"),
                          bg=self.c["bg"], fg=self.c["fg"])
        vtitle.grid(row=0, column=0, sticky="w", pady=(0, 24))
        self._track(vtitle, "bg", "bg")
        self._track(vtitle, "fg", "fg")

        v_card = RoundedCard(self.page_verify, bg_color=self.c["card"], radius=16,
                             border_color=self.c["border"],
                             row=1, column=0, sticky="ew", pady=(0, 16))
        self.cards.append((v_card, "card"))
        vinner = v_card.inner

        tk.Label(vinner, text="输入密钥", font=("Segoe UI", 12, "bold"),
                 bg=self.c["card"], fg=self.c["fg"]).pack(anchor="w", pady=(12, 8))

        self.verify_var = tk.StringVar()
        vent = tk.Entry(vinner, textvariable=self.verify_var, font=("Segoe UI", 13, "bold"),
                        bg=self.c["bg"], fg=self.c["fg"], insertbackground=self.c["fg"],
                        relief="flat", bd=0, highlightthickness=1,
                        highlightbackground=self.c["border"], highlightcolor=self.c["accent"])
        vent.pack(fill="x", ipady=8)
        self._track(vent, "bg", "bg")
        self._track(vent, "fg", "fg")
        self._track(vent, "highlightbackground", "border")
        self._track(vent, "highlightcolor", "accent")
        self._track(vent, "insertbackground", "fg")

        hint = tk.Label(vinner, text="格式: XXXXX-XXXXX-XXXXX-XXXXX-XXXXX",
                        font=("Segoe UI", 9), bg=self.c["card"], fg=self.c["muted"])
        hint.pack(anchor="w", pady=(4, 12))
        self._track(hint, "bg", "card")
        self._track(hint, "fg", "muted")

        vbtn = tk.Button(vinner, text="验证", command=self._do_verify,
                         font=("Segoe UI", 11, "bold"), bg=self.c["btn_primary"], fg=self.c["fg"],
                         activebackground=self.c["accent"], activeforeground=self.c["fg"],
                         bd=0, padx=20, pady=10, cursor="hand2")
        vbtn.pack(anchor="w")
        self._track(vbtn, "bg", "btn_primary")
        self._track(vbtn, "fg", "fg")
        self._track(vbtn, "activebackground", "accent")
        self._track(vbtn, "activeforeground", "fg")

        self.verify_result_var = tk.StringVar(value="")
        self.verify_result_label = tk.Label(self.page_verify, textvariable=self.verify_result_var,
                        font=("Segoe UI", 14, "bold"), bg=self.c["bg"], fg=self.c["fg"])
        self.verify_result_label.grid(row=2, column=0, sticky="w", pady=(24, 0))
        self._track(self.verify_result_label, "bg", "bg")
        self._track(self.verify_result_label, "fg", "fg")

        v_card.update_height()
        self.page_verify.grid_remove()

        # === CSV 导出池页面 ===
        self.page_csv = tk.Frame(self.main, bg=self.c["bg"])
        self.page_csv.grid(row=0, column=0, sticky="nsew", padx=40, pady=40)
        self.page_csv.grid_columnconfigure(0, weight=1)
        self.page_csv.grid_rowconfigure(2, weight=1)
        self._track(self.page_csv, "bg", "bg")

        csv_title = tk.Label(self.page_csv, text="CSV 导出池", font=("Segoe UI", 32, "bold"),
                             bg=self.c["bg"], fg=self.c["fg"])
        csv_title.grid(row=0, column=0, sticky="w", pady=(0, 8))
        self._track(csv_title, "bg", "bg")
        self._track(csv_title, "fg", "fg")

        self.csv_count_var = tk.StringVar(value="当前池内: 0 条")
        csv_count_lbl = tk.Label(self.page_csv, textvariable=self.csv_count_var,
                                 font=("Segoe UI", 12), bg=self.c["bg"], fg=self.c["muted"])
        csv_count_lbl.grid(row=1, column=0, sticky="w", pady=(0, 16))
        self._track(csv_count_lbl, "bg", "bg")
        self._track(csv_count_lbl, "fg", "muted")

        # 滚动列表
        csv_scroll_wrap = tk.Frame(self.page_csv, bg=self.c["bg"])
        csv_scroll_wrap.grid(row=2, column=0, sticky="nsew")
        self._track(csv_scroll_wrap, "bg", "bg")
        csv_scroll_wrap.grid_rowconfigure(0, weight=1)
        csv_scroll_wrap.grid_columnconfigure(0, weight=1)

        self.csv_canvas = tk.Canvas(csv_scroll_wrap, highlightthickness=0, bg=self.c["bg"])
        self.csv_canvas.grid(row=0, column=0, sticky="nsew")
        self._track(self.csv_canvas, "bg", "bg")

        csv_sb = tk.Scrollbar(csv_scroll_wrap, orient="vertical", command=self.csv_canvas.yview)
        csv_sb.grid(row=0, column=1, sticky="ns")
        self.csv_canvas.configure(yscrollcommand=csv_sb.set)

        self.csv_list_frame = tk.Frame(self.csv_canvas, bg=self.c["bg"])
        self.csv_list_frame_id = self.csv_canvas.create_window((0, 0), window=self.csv_list_frame, anchor="nw")
        self._track(self.csv_list_frame, "bg", "bg")

        self.csv_list_frame.bind("<Configure>", lambda e: self.csv_canvas.configure(scrollregion=self.csv_canvas.bbox("all")))
        self.csv_canvas.bind("<Configure>", lambda e: self.csv_canvas.itemconfig(self.csv_list_frame_id, width=e.width))

        def _csv_on_mousewheel(event):
            self.csv_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        self.csv_canvas.bind_all("<MouseWheel>", _csv_on_mousewheel)

        # 按钮行
        csv_btn_frame = tk.Frame(self.page_csv, bg=self.c["bg"])
        csv_btn_frame.grid(row=3, column=0, sticky="w", pady=(24, 0))
        self._track(csv_btn_frame, "bg", "bg")

        self.csv_export_btn = tk.Button(csv_btn_frame, text="导出 CSV", command=self._do_csv_export,
                                        font=("Segoe UI", 11, "bold"), bg=self.c["btn_primary"], fg=self.c["fg"],
                                        activebackground=self.c["accent"], activeforeground=self.c["fg"],
                                        bd=0, padx=20, pady=12, cursor="hand2")
        self.csv_export_btn.pack(side="left", padx=(0, 12))
        self._track(self.csv_export_btn, "bg", "btn_primary")
        self._track(self.csv_export_btn, "fg", "fg")
        self._track(self.csv_export_btn, "activebackground", "accent")
        self._track(self.csv_export_btn, "activeforeground", "fg")

        self.csv_clear_btn = tk.Button(csv_btn_frame, text="清空池子", command=self._clear_csv_pool,
                                       font=("Segoe UI", 11), bg=self.c["btn_secondary"], fg=self.c["fg"],
                                       activebackground=self.c["accent"], activeforeground=self.c["fg"],
                                       bd=0, padx=16, pady=12, cursor="hand2")
        self.csv_clear_btn.pack(side="left")
        self._track(self.csv_clear_btn, "bg", "btn_secondary")
        self._track(self.csv_clear_btn, "fg", "fg")
        self._track(self.csv_clear_btn, "activebackground", "accent")
        self._track(self.csv_clear_btn, "activeforeground", "fg")

        self.page_csv.grid_remove()

    def _clear_results(self):
        for w in self.result_frame.winfo_children():
            w.destroy()

    def _add_result_row(self, index, key):
        rf = tk.Frame(self.result_frame, bg=self.c["card"], padx=16, pady=10)
        rf.pack(fill="x", pady=(0, 8), expand=True)
        self._track(rf, "bg", "card")

        idx_lbl = tk.Label(rf, text=f"[{index}]", font=("Segoe UI", 10, "bold"),
                           bg=self.c["card"], fg=self.c["muted"])
        idx_lbl.pack(side="left", padx=(0, 12))
        self._track(idx_lbl, "bg", "card")
        self._track(idx_lbl, "fg", "muted")

        key_lbl = tk.Label(rf, text=key, font=("Consolas", 13, "bold"),
                           bg=self.c["card"], fg=self.c["accent"])
        key_lbl.pack(side="left")
        self._track(key_lbl, "bg", "card")
        self._track(key_lbl, "fg", "accent")

        def _copy(k=key):
            self.root.clipboard_clear()
            self.root.clipboard_append(k)
            self.root.update()

        cp_btn = tk.Button(rf, text="复制", command=_copy,
                           font=("Segoe UI", 9), bg=self.c["btn_secondary"], fg=self.c["fg"],
                           activebackground=self.c["accent"], activeforeground=self.c["fg"],
                           bd=0, padx=12, pady=4, cursor="hand2")
        cp_btn.pack(side="right")
        self._track(cp_btn, "bg", "btn_secondary")
        self._track(cp_btn, "fg", "fg")
        self._track(cp_btn, "activebackground", "accent")
        self._track(cp_btn, "activeforeground", "fg")

    def _do_generate(self):
        self._clear_results()
        try:
            count = int(self.count_var.get())
            if count < 1:
                count = 1
            if count > 100:
                count = 100
        except ValueError:
            count = 1

        ktype = self.type_var.get()
        gen = self.gen_var.get()
        for i in range(count):
            key = generate_key(ktype, gen=gen)
            self._add_result_row(i + 1, key)

    def _add_to_csv_pool(self):
        type_names = {"V": "Viewer 专用", "D": "Decryptor 专用", "A": "全能 (All-in-One)"}
        ktype = type_names.get(self.type_var.get(), "Unknown")
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        added = 0
        for w in self.result_frame.winfo_children():
            for child in w.winfo_children():
                if isinstance(child, tk.Label) and isinstance(child.cget("font"), str) and "Consolas" in child.cget("font"):
                    key = child.cget("text")
                    if key and len(key) == 29:
                        self.csv_pool.append((len(self.csv_pool) + 1, key, ktype, ts))
                        added += 1
                        break

        if added > 0:
            msg = f"已将 {added} 条密钥加入 CSV 导出池。当前池内共 {len(self.csv_pool)} 条。"
            messagebox.showinfo("加入成功", msg)
        else:
            messagebox.showinfo("提示", "当前生成结果为空，没有可加入的密钥。")

    def _set_gen(self, val):
        self.gen_var.set(val)
        for v, btn in self.gen_buttons.items():
            btn.configure(bg=self.c["btn_primary"] if v == val else self.c["btn_secondary"])

    def _set_type(self, val):
        self.type_var.set(val)
        for v, btn in self.type_buttons.items():
            btn.configure(bg=self.c["btn_primary"] if v == val else self.c["btn_secondary"])

    def _do_verify(self):
        key = self.verify_var.get().strip()
        if not key:
            self.verify_result_var.set("请输入密钥")
            self.verify_result_label.configure(fg=self.c["fg"])
            return
        ok, msg, ktype = validate_key(key)
        if ok:
            type_names = {"V": "Viewer 专用", "D": "Decryptor 专用", "A": "全能"}
            self.verify_result_var.set(f"验证通过  |  类型: {type_names.get(ktype, ktype)}")
            self.verify_result_label.configure(fg=self.c["accent"])
        else:
            self.verify_result_var.set(f"验证失败: {msg}")
            self.verify_result_label.configure(fg="#ff4444")

    def _show_generate(self):
        self.page_verify.grid_remove()
        self.page_csv.grid_remove()
        self.page_gen.grid()
        self.active_page = "generate"
        self._update_nav_buttons("生成密钥")

    def _show_verify(self):
        self.page_gen.grid_remove()
        self.page_csv.grid_remove()
        self.page_verify.grid()
        self.active_page = "verify"
        self._update_nav_buttons("验证密钥")

    def _show_csv(self):
        self.page_gen.grid_remove()
        self.page_verify.grid_remove()
        self.page_csv.grid()
        self.active_page = "csv"
        self._update_nav_buttons("CSV 导出池")
        self._refresh_csv_list()

    def _refresh_csv_list(self):
        for w in self.csv_list_frame.winfo_children():
            w.destroy()

        self.csv_count_var.set(f"当前池内: {len(self.csv_pool)} 条")

        if not self.csv_pool:
            empty_lbl = tk.Label(self.csv_list_frame, text="池子为空，请先在「生成密钥」页面生成并加入密钥。",
                                 font=("Segoe UI", 12), bg=self.c["bg"], fg=self.c["muted"])
            empty_lbl.pack(pady=40)
            self._track(empty_lbl, "bg", "bg")
            self._track(empty_lbl, "fg", "muted")
            return

        # 表头
        header = tk.Frame(self.csv_list_frame, bg=self.c["card"], padx=16, pady=8)
        header.pack(fill="x", pady=(0, 4))
        self._track(header, "bg", "card")

        headers = [("序号", 8), ("密钥", 30), ("类型", 16), ("加入时间", 20)]
        for text, width in headers:
            lbl = tk.Label(header, text=text, font=("Segoe UI", 11, "bold"),
                           bg=self.c["card"], fg=self.c["accent"], width=width, anchor="w")
            lbl.pack(side="left", padx=(0, 12))
            self._track(lbl, "bg", "card")
            self._track(lbl, "fg", "accent")

        # 数据行
        for idx, key, ktype, ts in self.csv_pool:
            row = tk.Frame(self.csv_list_frame, bg=self.c["card"], padx=16, pady=10)
            row.pack(fill="x", pady=(0, 4))
            self._track(row, "bg", "card")

            tk.Label(row, text=str(idx), font=("Segoe UI", 11), bg=self.c["card"],
                     fg=self.c["muted"], width=8, anchor="w").pack(side="left", padx=(0, 12))
            tk.Label(row, text=key, font=("Consolas", 12, "bold"), bg=self.c["card"],
                     fg=self.c["accent"], width=30, anchor="w").pack(side="left", padx=(0, 12))
            tk.Label(row, text=ktype, font=("Segoe UI", 11), bg=self.c["card"],
                     fg=self.c["fg"], width=16, anchor="w").pack(side="left", padx=(0, 12))
            tk.Label(row, text=ts, font=("Segoe UI", 10), bg=self.c["card"],
                     fg=self.c["muted"], width=20, anchor="w").pack(side="left")

    def _do_csv_export(self):
        if not self.csv_pool:
            messagebox.showinfo("提示", "CSV导出池为空，没有可导出的密钥。")
            return

        save_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            initialfile=f"WN-PBR_Keys_{datetime.now():%Y%m%d_%H%M%S}.csv",
            filetypes=[("CSV 文件", "*.csv"), ("所有文件", "*.*")]
        )
        if not save_path:
            return

        try:
            with open(save_path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(["序号", "密钥", "类型", "加入时间"])
                for idx, key, ktype, ts in self.csv_pool:
                    writer.writerow([idx, key, ktype, ts])
            msg = f"已导出 {len(self.csv_pool)} 条密钥。"
            messagebox.showinfo("导出成功", msg)
        except Exception as e:
            messagebox.showerror("导出失败", str(e))

    def _clear_csv_pool(self):
        if not self.csv_pool:
            messagebox.showinfo("提示", "池子已经是空的。")
            return
        msg = f"确定要清空 CSV 导出池吗？当前共有 {len(self.csv_pool)} 条密钥。"
        if messagebox.askyesno("确认清空", msg):
            self.csv_pool = []
            self._refresh_csv_list()

    def _update_nav_buttons(self, active_text):
        buttons = {
            "生成密钥": self.btn_gen,
            "验证密钥": self.btn_verify,
            "CSV 导出池": self.btn_csv,
            "切换主题": self.btn_theme,
            "退出": self.btn_exit,
        }
        for text, btn in buttons.items():
            role = "btn_primary" if text == active_text else "btn_secondary"
            btn.configure(bg=self.c[role], fg=self.c["fg"], activeforeground=self.c["fg"])

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

        current_type = self.type_var.get()
        for v, btn in getattr(self, 'type_buttons', {}).items():
            btn.configure(bg=self.c["btn_primary"] if v == current_type else self.c["btn_secondary"],
                          fg=self.c["fg"])

        current_gen = self.gen_var.get()
        for v, btn in getattr(self, 'gen_buttons', {}).items():
            btn.configure(bg=self.c["btn_primary"] if v == current_gen else self.c["btn_secondary"],
                          fg=self.c["fg"])

        page_map = {"generate": "生成密钥", "verify": "验证密钥", "csv": "CSV 导出池"}
        for v, btn in getattr(self, 'type_buttons', {}).items():
            btn.configure(bg=self.c["btn_primary"] if v == current_type else self.c["btn_secondary"],
                          fg=self.c["fg"])

        page_map = {"generate": "生成密钥", "verify": "验证密钥", "csv": "CSV 导出池"}
        self._update_nav_buttons(page_map.get(self.active_page, "生成密钥"))

if __name__ == "__main__":
    root = tk.Tk()
    app = KeygenApp(root)
    root.mainloop()
