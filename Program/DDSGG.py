import ctypes
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import json
import os
from pathlib import Path

# ============ DPI 感知 ============
if sys.platform == 'win32':
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        ctypes.windll.user32.SetProcessDPIAware()

# ============ 偏移量 ============
OFFSET = 7350

def decrypt(text):
    return "".join(chr(ord(c) - OFFSET) for c in text)

# ============ 配色 ============
PALETTE = {
    "dark": {
        "bg": "#202020", "card": "#2d2d2d", "fg": "#ffffff",
        "muted": "#a0a0a0", "accent": "#4cc2ff",
        "border": "#3a3a3a", "btn_primary": "#0078d4", "btn_secondary": "#3a3a3a",
    },
    "light": {
        "bg": "#f3f3f3", "card": "#ffffff", "fg": "#1a1a1a",
        "muted": "#5f5f5f", "accent": "#0078d4",
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

# ============ 主程序 ============
class Decryptor:
    def __init__(self, root):
        self.root, self.theme = root, "dark"
        self.c = PALETTE[self.theme]
        self.tracked = []
        self.current_plain = None
        self.current_filename = None

        root.title("Catchmark Decryptor")
        root.configure(bg="#010101")
        root.wm_attributes('-transparentcolor', "#010101")

        # 加载自定义图标（支持 Nuitka onefile 嵌入资源）
        self._load_icon(root, "Catchmark_Decryptor.png")

        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
        w = min(int(sw * 0.70), 1400)
        h = min(int(w * 9 / 16), int(sh * 0.80))
        root.geometry(str(w) + "x" + str(h))
        root.minsize(800, 600)

        if sys.platform == 'win32':
            root.update_idletasks()
            apply_win11(ctypes.windll.user32.GetParent(root.winfo_id()))

        self._build_ui()

        # 检查命令行参数，自动加载传入的 .wnpbr 文件
        self._check_cli_args()

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

    def _build_ui(self):
        toolbar = tk.Frame(self.root, bg=self.c["bg"], padx=24, pady=16)
        toolbar.pack(fill="x")
        self._track(toolbar, "bg", "bg")

        title_lbl = tk.Label(toolbar, text="Catchmark Decryptor", font=("Segoe UI", 18, "bold"),
                             bg=self.c["bg"], fg=self.c["fg"])
        title_lbl.pack(side="left")
        self._track(title_lbl, "bg", "bg")
        self._track(title_lbl, "fg", "fg")

        btn_frame = tk.Frame(toolbar, bg=self.c["bg"])
        btn_frame.pack(side="right")
        self._track(btn_frame, "bg", "bg")

        self.btn_open = tk.Button(btn_frame, text="选择文件", command=self.open_file,
                                  font=("Segoe UI", 10), bg=self.c["btn_primary"], fg=self.c["fg"],
                                  activebackground=self.c["accent"], activeforeground=self.c["fg"],
                                  bd=0, padx=16, pady=8, cursor="hand2")
        self.btn_open.pack(side="left", padx=(0, 8))
        self._track(self.btn_open, "bg", "btn_primary")
        self._track(self.btn_open, "fg", "fg")

        self.btn_save = tk.Button(btn_frame, text="保存 JSON", command=self.save_json,
                                  font=("Segoe UI", 10), bg=self.c["btn_secondary"], fg=self.c["fg"],
                                  activebackground=self.c["accent"], activeforeground=self.c["fg"],
                                  bd=0, padx=16, pady=8, cursor="hand2")
        self.btn_save.pack(side="left", padx=(0, 8))
        self._track(self.btn_save, "bg", "btn_secondary")
        self._track(self.btn_save, "fg", "fg")

        self.btn_theme = tk.Button(btn_frame, text="切换主题", command=self.toggle_theme,
                                   font=("Segoe UI", 10), bg=self.c["btn_secondary"], fg=self.c["fg"],
                                   activebackground=self.c["accent"], activeforeground=self.c["fg"],
                                   bd=0, padx=16, pady=8, cursor="hand2")
        self.btn_theme.pack(side="left")
        self._track(self.btn_theme, "bg", "btn_secondary")
        self._track(self.btn_theme, "fg", "fg")

        self.path_var = tk.StringVar(value="未选择文件")
        path_lbl = tk.Label(self.root, textvariable=self.path_var, font=("Segoe UI", 10),
                            bg=self.c["bg"], fg=self.c["muted"], anchor="w", padx=24)
        path_lbl.pack(fill="x")
        self._track(path_lbl, "bg", "bg")
        self._track(path_lbl, "fg", "muted")

        sep = tk.Frame(self.root, height=1)
        sep.pack(fill="x", padx=24, pady=(8, 0))
        self._track(sep, "bg", "border")

        self.text = scrolledtext.ScrolledText(
            self.root, font=("Consolas", 11), wrap="word",
            bg=self.c["card"], fg=self.c["fg"], insertbackground=self.c["fg"],
            relief="flat", bd=0, padx=16, pady=16, state="disabled"
        )
        self.text.pack(fill="both", expand=True, padx=24, pady=16)
        self._track(self.text, "bg", "card")
        self._track(self.text, "fg", "fg")
        self._track(self.text, "insertbackground", "fg")

    def open_file(self):
        path = filedialog.askopenfilename(filetypes=[("Catchmark 文件", "*.wnpbr"), ("所有文件", "*.*")])
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                encrypted = f.read()
            plain = decrypt(encrypted)
            data = json.loads(plain)
            formatted = json.dumps(data, ensure_ascii=False, indent=2)

            self.current_plain = formatted
            self.current_filename = os.path.splitext(os.path.basename(path))[0]
            self.path_var.set("已加载：" + os.path.basename(path))

            self.text.configure(state="normal")
            self.text.delete("1.0", "end")
            self.text.insert("1.0", formatted)
            self.text.configure(state="disabled")
        except Exception as e:
            messagebox.showerror("解密失败", str(e))

    def save_json(self):
        if self.current_plain is None:
            messagebox.showwarning("提示", "请先选择一个 .wnpbr 文件进行解密。")
            return
        save_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            initialfile=self.current_filename + "_decrypted.json",
            filetypes=[("JSON 文件", "*.json"), ("所有文件", "*.*")]
        )
        if not save_path:
            return
        try:
            with open(save_path, "w", encoding="utf-8") as f:
                f.write(self.current_plain)
            messagebox.showinfo("保存成功", "明文已保存至：" + chr(10) + save_path)
        except Exception as e:
            messagebox.showerror("保存失败", str(e))

    def _check_cli_args(self):
        """检查命令行参数，自动加载 .wnpbr 文件"""
        if len(sys.argv) > 1:
            path = sys.argv[1]
            if os.path.isfile(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        encrypted = f.read()
                    plain = decrypt(encrypted)
                    data = json.loads(plain)
                    formatted = json.dumps(data, ensure_ascii=False, indent=2)
                    self.current_plain = formatted
                    self.current_filename = os.path.splitext(os.path.basename(path))[0]
                    self.path_var.set("已加载：" + os.path.basename(path))
                    self.text.configure(state="normal")
                    self.text.delete("1.0", "end")
                    self.text.insert("1.0", formatted)
                    self.text.configure(state="disabled")
                except Exception as e:
                    messagebox.showerror("解密失败", str(e))

    def toggle_theme(self):
        self.theme = "light" if self.theme == "dark" else "dark"
        self.c = PALETTE[self.theme]

        self.root.configure(bg="#010101")
        self.root.wm_attributes('-transparentcolor', "#010101")

        if sys.platform == 'win32':
            self.root.update_idletasks()
            apply_win11(ctypes.windll.user32.GetParent(self.root.winfo_id()))

        for widget, attr, role in self.tracked:
            try:
                widget.configure(**{attr: self.c[role]})
            except tk.TclError:
                pass

if __name__ == "__main__":
    root = tk.Tk()
    app = Decryptor(root)
    root.mainloop()
