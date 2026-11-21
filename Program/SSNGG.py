#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Catchmark Benchmark Suite - 基准测试引擎
版本: 2.4.0 (Custom)
作者: Wing North Studio

模式:
    --classic (默认)  经典三项测试：大整数 / 矩阵 / JSON
    --neo             Neo 扩展测试：经典三项 + 素数筛 / 字符串 / 字典
    --gen2            Gen2 全面测试：Neo 六项 + 内存带宽 / 列表操作 / I/O 吞吐 + GIL 并发
    --custom          客制化测试：自选测试项目，动态权重

依赖 (可选):
    pip install win11toast          # Win11 通知 (推荐)
    pip install win10toast          # Win10 通知

"""

import multiprocessing as mp
import time
import sys
import random
import json
import hashlib
import subprocess
import platform
import os
import getpass
import ctypes
import argparse
import re
import tempfile
import threading
from datetime import datetime
from pathlib import Path

# ============ Windows 启用 ANSI 颜色 ============
if sys.platform == 'win32':
    try:
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)
        mode = ctypes.c_ulong()
        kernel32.GetConsoleMode(handle, ctypes.byref(mode))
        mode.value |= 0x0004
        kernel32.SetConsoleMode(handle, mode)
    except Exception:
        pass

# ============ 颜色常量 ============
class C:
    RST = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    GREEN = "\033[92m"
    CYAN = "\033[96m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    WHITE = "\033[97m"
    GRAY = "\033[90m"
    ORANGE = "\033[38;5;208m"

def cprint(text, color="", bold=False, end="\n"):
    prefix = ""
    if bold:
        prefix += C.BOLD
    if color:
        prefix += color
    print(f"{prefix}{text}{C.RST}", end=end)

# ============ 进度条 ============
def progress_iter(iterable, total=None, desc="", width=40):
    total = total or getattr(iterable, "__len__", lambda: 0)()
    if total == 0:
        yield from iterable
        return
    start = time.perf_counter()
    for i, item in enumerate(iterable):
        yield item
        pct = (i + 1) / total
        filled = int(width * pct)
        bar = "█" * filled + "░" * (width - filled)
        elapsed = time.perf_counter() - start
        eta = elapsed / pct - elapsed if pct > 0 else 0
        status = f"\r  {C.CYAN}{desc}{C.RST} |{C.GREEN}{bar}{C.RST}| {pct*100:>5.1f}%  [{i+1}/{total}]  ETA: {eta:>5.1f}s"
        print(status, end="", flush=True)
    print()

# ============ Windows 通知 ============
def get_toast_icon():
    """查找通知图标路径（支持源码运行和 Nuitka onefile）"""
    candidates = []
    try:
        candidates.append(Path(__file__).resolve().parent / "Catchmark.ico")
    except NameError:
        pass
    if getattr(sys, 'frozen', False):
        candidates.append(Path(sys.executable).resolve().parent / "Catchmark.ico")
    for path in candidates:
        if path.exists():
            return str(path)
    return None

def notify(title, message):
    """Windows Toast 通知。Win11 优先 win11toast，回退 win10toast。"""
    if sys.platform != "win32":
        return
    icon_path = get_toast_icon()
    try:
        from win11toast import toast
        kwargs = {}
        if icon_path:
            kwargs["icon"] = icon_path
        toast(title, message, app_id="Wing North Software", **kwargs)
        return
    except Exception:
        pass
    try:
        from win10toast import ToastNotifier
        kwargs = {"duration": 5, "threaded": True}
        if icon_path:
            kwargs["icon_path"] = icon_path
        ToastNotifier().show_toast(title, message, **kwargs)
    except Exception:
        pass


def encrypt(text, offset=7350):
    return "".join(chr(ord(c) + offset) for c in text)

# ============ 获取 CPU 型号 ============
def get_cpu_name():
    system = platform.system()
    if system == "Windows":
        try:
            result = subprocess.run(
                ["wmic", "cpu", "get", "Name"],
                capture_output=True, text=True, check=True, timeout=5
            )
            lines = [line.strip() for line in result.stdout.splitlines()
                     if line.strip() and line.strip() != "Name"]
            if lines:
                return lines[0]
        except Exception:
            pass
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"HARDWARE\DESCRIPTION\System\CentralProcessor\0"
            )
            name, _ = winreg.QueryValueEx(key, "ProcessorNameString")
            winreg.CloseKey(key)
            return name.strip()
        except Exception:
            pass
    elif system == "Linux":
        try:
            with open("/proc/cpuinfo", "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("model name"):
                        return line.split(":", 1)[1].strip()
        except Exception:
            pass
    elif system == "Darwin":
        try:
            result = subprocess.run(
                ["sysctl", "-n", "machdep.cpu.brand_string"],
                capture_output=True, text=True, check=True, timeout=5
            )
            return result.stdout.strip()
        except Exception:
            pass
    proc = platform.processor()
    return proc if proc else "Unknown"

# ============ 评分基准 ============
BASELINE = {
    "fib_10m": 300.0,
    "matmul_512": 5.0,
    "json_200k": 0.5,
    "weights": {
        "fib_10m": 0.4,
        "matmul_512": 0.3,
        "json_200k": 0.3
    }
}

NEO_BASELINE = {
    "prime_10m": 2.5,
    "str_regex_100k": 3.0,
    "dict_500k": 1.5,
    "weights": {
        "prime_10m": 0.4,
        "str_regex_100k": 0.3,
        "dict_500k": 0.3
    }
}

GEN2_BASELINE = {
    "fib_10m": 300.0,
    "matmul_512": 5.0,
    "json_200k": 0.5,
    "prime_10m": 2.5,
    "str_regex_100k": 3.0,
    "dict_500k": 1.5,
    "memory_50m": 0.3,
    "list_ops_500k": 4.0,
    "io_1m": 1.0,
    "weights": {
        "fib_10m": 0.20,
        "matmul_512": 0.15,
        "json_200k": 0.10,
        "prime_10m": 0.15,
        "str_regex_100k": 0.10,
        "dict_500k": 0.10,
        "memory_50m": 0.10,
        "list_ops_500k": 0.05,
        "io_1m": 0.05,
    }
}

# ============ 客制化测试注册表 ============
CUSTOM_TEST_REGISTRY = [
    {"key": "fib_10m", "name": "大整数累加", "desc": "斐波那契第 10,000,000 项",
     "baseline": 300.0, "weight": 0.20, "group": "classic"},
    {"key": "matmul_512", "name": "矩阵乘法", "desc": "512 x 512 浮点矩阵",
     "baseline": 5.0, "weight": 0.15, "group": "classic"},
    {"key": "json_200k", "name": "JSON 混合负载", "desc": "200,000 条记录",
     "baseline": 0.5, "weight": 0.10, "group": "classic"},
    {"key": "prime_10m", "name": "素数筛", "desc": "埃拉托斯特尼筛法 10,000,000",
     "baseline": 2.5, "weight": 0.15, "group": "neo"},
    {"key": "str_regex_100k", "name": "字符串处理", "desc": "100,000 条正则匹配",
     "baseline": 3.0, "weight": 0.10, "group": "neo"},
    {"key": "dict_500k", "name": "字典运算", "desc": "500,000 次插入/查找/排序",
     "baseline": 1.5, "weight": 0.10, "group": "neo"},
    {"key": "memory_50m", "name": "内存带宽", "desc": "50MB bytearray 读写 + 对象分配",
     "baseline": 0.3, "weight": 0.10, "group": "gen2"},
    {"key": "list_ops_500k", "name": "列表操作", "desc": "500,000 次追加/排序/插入/切片",
     "baseline": 4.0, "weight": 0.05, "group": "gen2"},
    {"key": "io_1m", "name": "I/O 吞吐", "desc": "1MB 二进制 + 10,000 行文本读写",
     "baseline": 1.0, "weight": 0.05, "group": "gen2"},
    {"key": "gil", "name": "GIL 并发", "desc": "CPU 密集型多线程加速比测试",
     "baseline": None, "weight": 0.0, "group": "gen2", "no_score": True},
]

# ============ 斐波那契 ============
try:
    sys.set_int_max_str_digits(10**7)
except AttributeError:
    pass

def fast_doubling(n):
    if n == 0:
        return (0, 1)
    a, b = fast_doubling(n >> 1)
    c = a * (2 * b - a)
    d = a * a + b * b
    if n & 1:
        return (d, c + d)
    else:
        return (c, d)

def fib_chunk(args):
    start_idx, end_idx, a, b = args
    for _ in range(end_idx - start_idx):
        c = a + b
        a, b = b, c
    return (end_idx, a)

def bench_fib(n=10_000_000, progress=True):
    if n == 1:
        return 0, 0.0
    elif n == 2:
        return 1, 0.0
    elif n < 8000:
        a, b = 0, 1
        t0 = time.perf_counter()
        for _ in range(2, n):
            a, b = b, a + b
        t1 = time.perf_counter()
        return b, t1 - t0
    else:
        num_workers = min(mp.cpu_count(), 16)
        total = n - 2
        chunk_size = total // num_workers
        tasks = []
        for i in range(num_workers):
            chunk_start = 3 + i * chunk_size
            if i == num_workers - 1:
                chunk_end = n
            else:
                chunk_end = chunk_start + chunk_size - 1
            a, b = fast_doubling(chunk_start - 1)
            tasks.append((chunk_start, chunk_end, a, b))
        t0 = time.perf_counter()
        with mp.Pool(num_workers) as pool:
            if progress:
                results = list(progress_iter(
                    pool.imap_unordered(fib_chunk, tasks),
                    total=len(tasks),
                    desc="大整数累加"
                ))
            else:
                results = pool.map(fib_chunk, tasks)
        t1 = time.perf_counter()
        for idx, val in results:
            if idx == n:
                return val, t1 - t0
        return None, t1 - t0

# ============ 矩阵乘法 ============
def bench_matmul(n=512):
    rng = random.Random(42)
    A = [[rng.random() for _ in range(n)] for _ in range(n)]
    B = [[rng.random() for _ in range(n)] for _ in range(n)]
    C = [[0.0] * n for _ in range(n)]
    t0 = time.perf_counter()
    for i in range(n):
        for k in range(n):
            aik = A[i][k]
            for j in range(n):
                C[i][j] += aik * B[k][j]
    t1 = time.perf_counter()
    elapsed = t1 - t0
    flops = 2 * n ** 3
    gflops = flops / elapsed / 1e9
    checksum = sum(C[i][i] for i in range(0, n, 16))
    return elapsed, gflops, checksum

# ============ JSON 混合负载 ============
def bench_json(n=200_000):
    records = []
    rng = random.Random(42)
    t0 = time.perf_counter()
    for i in range(n):
        rec = {
            "id": i,
            "name": f"user_{i}_{rng.randint(1000, 9999)}",
            "score": rng.random() * 100,
            "tags": [f"tag{j}" for j in range(rng.randint(3, 8))]
        }
        records.append(rec)
    text = json.dumps(records)
    h = hashlib.sha256(text.encode()).hexdigest()
    count = text.count("tag5")
    t1 = time.perf_counter()
    return t1 - t0, len(text), h[:16], count

# ============ Neo 测试项 ============

def bench_prime_sieve(n=10_000_000):
    """埃拉托斯特尼筛法 - 测试整数运算与内存访问"""
    t0 = time.perf_counter()
    sieve = bytearray(b'\x01') * (n + 1)
    sieve[0:2] = b'\x00\x00'
    for i in range(2, int(n**0.5) + 1):
        if sieve[i]:
            step = i
            start = i * i
            sieve[start:n+1:step] = b'\x00' * ((n - start) // step + 1)
    count = sum(sieve)
    t1 = time.perf_counter()
    return t1 - t0, count

def bench_str_regex(n=100_000):
    """字符串拼接与正则匹配 - 测试字符串处理能力"""
    rng = random.Random(42)
    patterns = [r"user_\d{4,6}", r"[a-z]+_[0-9]{4}", r"tag[3-8]"]
    compiled = [re.compile(p) for p in patterns]
    t0 = time.perf_counter()
    texts = []
    for i in range(n):
        texts.append(f"user_{rng.randint(1000,999999)}_score_{rng.random()*100:.2f}_tags_{','.join(f'tag{j}' for j in range(rng.randint(3,8)))}")
    total_matches = 0
    for text in texts:
        for cp in compiled:
            total_matches += len(cp.findall(text))
    t1 = time.perf_counter()
    return t1 - t0, total_matches

def bench_dict_ops(n=500_000):
    """大规模字典插入、查找、排序 - 测试哈希表性能"""
    rng = random.Random(42)
    t0 = time.perf_counter()
    d = {}
    for i in range(n):
        d[f"key_{i}_{rng.randint(1000,9999)}"] = rng.random() * 1000
    lookup_hits = 0
    for i in range(n):
        key = f"key_{i}_{rng.randint(1000,9999)}"
        if key in d:
            lookup_hits += 1
    sorted_items = sorted(d.items(), key=lambda x: x[1], reverse=True)
    top_sum = sum(v for _, v in sorted_items[:1000])
    t1 = time.perf_counter()
    return t1 - t0, len(d), lookup_hits, top_sum

# ============ Gen2 测试项 ============

def bench_memory(n=50_000_000):
    """内存带宽与分配压力测试"""
    t0 = time.perf_counter()
    # 大规模 bytearray 连续读写
    a = bytearray(n)
    for i in range(0, n, 4096):
        a[i] = i & 0xFF
    # 切片拷贝
    b = a[:n//2]
    # 对象创建压力
    objs = [bytearray(1024) for _ in range(10000)]
    t1 = time.perf_counter()
    elapsed = t1 - t0
    total_bytes = n + len(b) + sum(len(o) for o in objs)
    bandwidth = total_bytes / elapsed / 1024 / 1024
    return elapsed, bandwidth

def bench_list_ops(n=500_000):
    """列表综合操作测试"""
    rng = random.Random(42)
    t0 = time.perf_counter()
    # 尾部追加
    lst = []
    for i in range(n):
        lst.append(rng.randint(0, 9999))
    # 排序
    lst.sort()
    # 随机插入
    for i in range(n // 10):
        lst.insert(rng.randint(0, len(lst)), rng.randint(0, 9999))
    # 切片
    s = lst[n//4:n//2]
    # 合并
    lst.extend(s)
    t1 = time.perf_counter()
    return t1 - t0, len(lst)

def bench_io(n=1_000_000):
    """I/O 吞吐测试"""
    t0 = time.perf_counter()
    # 二进制大文件顺序写
    with tempfile.NamedTemporaryFile(delete=False) as f:
        path = f.name
        data = bytes(range(256)) * (n // 256 + 1)
        f.write(data[:n])
    # 顺序读
    with open(path, 'rb') as f:
        read_data = f.read()
    # 文本逐行读写
    lines = [f"line_{i:08d},data_{i%1000:04d},value={i*1.5:.2f}\n" for i in range(n//100)]
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        text_path = f.name
        f.writelines(lines)
    with open(text_path, 'r') as f:
        read_lines = f.readlines()
    # 清理
    os.unlink(path)
    os.unlink(text_path)
    t1 = time.perf_counter()
    return t1 - t0, len(read_data), len(read_lines)

def bench_gil(n=1_000_000, workers=8):
    """GIL 并发影响测试（不计入总分，独立展示）"""
    def _worker(seed, count):
        rng = random.Random(seed)
        total = 0
        for _ in range(count):
            data = str(rng.random()).encode()
            total += int(hashlib.md5(data).hexdigest(), 16)
        return total

    chunk = n // workers

    # 单线程基准
    t0 = time.perf_counter()
    single_result = _worker(42, n)
    t1 = time.perf_counter()
    single_time = t1 - t0

    # 多线程
    results = [None] * workers
    def _thread_wrapper(idx):
        results[idx] = _worker(42 + idx, chunk)

    t2 = time.perf_counter()
    threads = []
    for i in range(workers):
        t = threading.Thread(target=_thread_wrapper, args=(i,))
        threads.append(t)
        t.start()
    for t in threads:
        t.join()
    t3 = time.perf_counter()
    multi_time = t3 - t2

    speedup = single_time / multi_time if multi_time > 0 else 0
    efficiency = speedup / workers if workers > 0 else 0
    return single_time, multi_time, speedup, efficiency
# ============ 客制化测试模式 ============
def run_custom_mode(args, cpu_name, py_ver, cores, timestamp):
    """客制化测试模式：用户自选测试项，动态执行并评分"""
    registry = CUSTOM_TEST_REGISTRY
    selectable = [item for item in registry if not item.get("no_score", False)]
    gil_item = next((item for item in registry if item.get("no_score")), None)

    # 交互式选择
    if not args.silent:
        print()
        cprint("=" * 60, C.BLUE, bold=True)
        cprint("         客 制 化 测 试 项 目 选 择", C.BLUE, bold=True)
        cprint("=" * 60, C.BLUE, bold=True)
        print()
        cprint("  请勾选要测试的项目（输入编号，用空格分隔）:", C.WHITE, bold=True)
        print()
        for i, item in enumerate(selectable, 1):
            tag = {"classic": C.GREEN, "neo": C.MAGENTA, "gen2": C.ORANGE}[item["group"]]
            cprint(f"  [{i}] {item['name']:<12} {item['desc']}", tag)
        print()
        if gil_item:
            cprint(f"  [G] {gil_item['name']:<12} {gil_item['desc']}（不计入总分）", C.GRAY)
        print()
        cprint("  示例: 1 2 4 7  G", C.GRAY)
        print()

    # 读取输入
    selected_keys = []
    include_gil = False
    if not args.silent:
        raw = input("  输入选项: ").strip().lower()
        parts = raw.split()
        for p in parts:
            if p == 'g' and gil_item:
                include_gil = True
            elif p.isdigit():
                idx = int(p) - 1
                if 0 <= idx < len(selectable):
                    selected_keys.append(selectable[idx]["key"])
    else:
        # 静默模式下默认全选（不含 GIL）
        selected_keys = [item["key"] for item in selectable]

    if not selected_keys:
        cprint("  未选择任何测试项，已退出。", C.RED)
        return None

    # 去重并保持注册表顺序
    ordered_keys = [item["key"] for item in selectable if item["key"] in selected_keys]
    total = len(ordered_keys) + (1 if include_gil else 0)
    results = {}
    scores = {}

    print()
    cprint("=" * 60, C.CYAN, bold=True)
    cprint("         Catchmark  Python 综合性能 Benchmark", C.CYAN, bold=True)
    cprint("         模式: 客制化测试", C.CYAN, bold=True)
    cprint("=" * 60, C.CYAN, bold=True)
    cprint(f"  CPU 型号:   {cpu_name}", C.WHITE)
    cprint(f"  Python:     {py_ver}", C.WHITE)
    cprint(f"  逻辑核心:   {cores}", C.WHITE)
    cprint("-" * 60, C.GRAY)

    idx = 1
    # 大整数
    if "fib_10m" in ordered_keys:
        print()
        cprint(f"[{idx}/{total}] 大整数累加 — 斐波那契第 10,000,000 项", C.YELLOW, bold=True)
        if not args.silent:
            cprint("      计算中，请稍候（通常数十秒至数分钟）...", C.GRAY)
        fib_val, fib_t = bench_fib(10_000_000, progress=not args.no_progress)
        fib_score = (BASELINE["fib_10m"] / fib_t) * 1000 if fib_t > 0 else 0
        cprint(f"      耗时:      {fib_t:.3f} s", C.WHITE)
        cprint(f"      结果位数:  {len(str(fib_val))}", C.WHITE)
        cprint(f"      单项得分:  {fib_score:>10.0f}", C.GREEN, bold=True)
        results["fib_time"] = round(fib_t, 3)
        results["fib_digits"] = len(str(fib_val))
        results["fib_score"] = round(fib_score, 0)
        scores["fib_10m"] = fib_score
        idx += 1

    # 矩阵
    if "matmul_512" in ordered_keys:
        print()
        cprint(f"[{idx}/{total}] 浮点矩阵乘法 — 512 x 512", C.YELLOW, bold=True)
        if not args.silent:
            cprint("      计算中，请稍候...", C.GRAY)
        mat_t, mat_gflops, mat_chk = bench_matmul(512)
        mat_score = (BASELINE["matmul_512"] / mat_t) * 1000 if mat_t > 0 else 0
        cprint(f"      耗时:        {mat_t:.3f} s", C.WHITE)
        cprint(f"      等效 GFLOPS: {mat_gflops:.3f}", C.WHITE)
        cprint(f"      校验和:      {mat_chk:.4f}", C.WHITE)
        cprint(f"      单项得分:    {mat_score:>10.0f}", C.GREEN, bold=True)
        results["mat_time"] = round(mat_t, 3)
        results["mat_gflops"] = round(mat_gflops, 3)
        results["mat_checksum"] = round(mat_chk, 4)
        results["mat_score"] = round(mat_score, 0)
        scores["matmul_512"] = mat_score
        idx += 1

    # JSON
    if "json_200k" in ordered_keys:
        print()
        cprint(f"[{idx}/{total}] JSON 混合负载 — 200,000 条记录", C.YELLOW, bold=True)
        if not args.silent:
            cprint("      计算中，请稍候...", C.GRAY)
        json_t, json_size, json_hash, json_cnt = bench_json(200_000)
        json_score = (BASELINE["json_200k"] / json_t) * 1000 if json_t > 0 else 0
        cprint(f"      耗时:        {json_t:.3f} s", C.WHITE)
        cprint(f"      JSON 大小:   {json_size / 1024 / 1024:.2f} MB", C.WHITE)
        cprint(f"      SHA256 前缀: {json_hash}", C.WHITE)
        cprint(f"      单项得分:    {json_score:>10.0f}", C.GREEN, bold=True)
        results["json_time"] = round(json_t, 3)
        results["json_size_mb"] = round(json_size / 1024 / 1024, 2)
        results["json_sha16"] = json_hash
        results["json_score"] = round(json_score, 0)
        scores["json_200k"] = json_score
        idx += 1

    # 素数筛
    if "prime_10m" in ordered_keys:
        print()
        cprint(f"[{idx}/{total}] 素数筛 — 埃拉托斯特尼筛法 10,000,000", C.YELLOW, bold=True)
        if not args.silent:
            cprint("      计算中，请稍候...", C.GRAY)
        prime_t, prime_count = bench_prime_sieve(10_000_000)
        prime_score = (NEO_BASELINE["prime_10m"] / prime_t) * 1000 if prime_t > 0 else 0
        cprint(f"      耗时:        {prime_t:.3f} s", C.WHITE)
        cprint(f"      素数个数:    {prime_count:,}", C.WHITE)
        cprint(f"      单项得分:    {prime_score:>10.0f}", C.GREEN, bold=True)
        results["prime_time"] = round(prime_t, 3)
        results["prime_count"] = prime_count
        results["prime_score"] = round(prime_score, 0)
        scores["prime_10m"] = prime_score
        idx += 1

    # 字符串
    if "str_regex_100k" in ordered_keys:
        print()
        cprint(f"[{idx}/{total}] 字符串处理 — 100,000 条正则匹配", C.YELLOW, bold=True)
        if not args.silent:
            cprint("      计算中，请稍候...", C.GRAY)
        str_t, str_matches = bench_str_regex(100_000)
        str_score = (NEO_BASELINE["str_regex_100k"] / str_t) * 1000 if str_t > 0 else 0
        cprint(f"      耗时:        {str_t:.3f} s", C.WHITE)
        cprint(f"      匹配次数:    {str_matches:,}", C.WHITE)
        cprint(f"      单项得分:    {str_score:>10.0f}", C.GREEN, bold=True)
        results["str_time"] = round(str_t, 3)
        results["str_matches"] = str_matches
        results["str_score"] = round(str_score, 0)
        scores["str_regex_100k"] = str_score
        idx += 1

    # 字典
    if "dict_500k" in ordered_keys:
        print()
        cprint(f"[{idx}/{total}] 字典运算 — 500,000 次插入/查找/排序", C.YELLOW, bold=True)
        if not args.silent:
            cprint("      计算中，请稍候...", C.GRAY)
        dict_t, dict_len, dict_hits, dict_top = bench_dict_ops(500_000)
        dict_score = (NEO_BASELINE["dict_500k"] / dict_t) * 1000 if dict_t > 0 else 0
        cprint(f"      耗时:        {dict_t:.3f} s", C.WHITE)
        cprint(f"      字典大小:    {dict_len:,}", C.WHITE)
        cprint(f"      查找命中:    {dict_hits:,}", C.WHITE)
        cprint(f"      单项得分:    {dict_score:>10.0f}", C.GREEN, bold=True)
        results["dict_time"] = round(dict_t, 3)
        results["dict_size"] = dict_len
        results["dict_hits"] = dict_hits
        results["dict_top_sum"] = round(dict_top, 2)
        results["dict_score"] = round(dict_score, 0)
        scores["dict_500k"] = dict_score
        idx += 1

    # 内存
    if "memory_50m" in ordered_keys:
        print()
        cprint(f"[{idx}/{total}] 内存带宽 — 50MB bytearray 读写 + 对象分配", C.YELLOW, bold=True)
        if not args.silent:
            cprint("      计算中，请稍候...", C.GRAY)
        mem_t, mem_bw = bench_memory(50_000_000)
        mem_score = (GEN2_BASELINE["memory_50m"] / mem_t) * 1000 if mem_t > 0 else 0
        cprint(f"      耗时:        {mem_t:.3f} s", C.WHITE)
        cprint(f"      等效带宽:    {mem_bw:.1f} MB/s", C.WHITE)
        cprint(f"      单项得分:    {mem_score:>10.0f}", C.GREEN, bold=True)
        results["memory_time"] = round(mem_t, 3)
        results["memory_bandwidth"] = round(mem_bw, 1)
        results["memory_score"] = round(mem_score, 0)
        scores["memory_50m"] = mem_score
        idx += 1

    # 列表
    if "list_ops_500k" in ordered_keys:
        print()
        cprint(f"[{idx}/{total}] 列表操作 — 500,000 次追加/排序/插入/切片", C.YELLOW, bold=True)
        if not args.silent:
            cprint("      计算中，请稍候...", C.GRAY)
        list_t, list_len = bench_list_ops(500_000)
        list_score = (GEN2_BASELINE["list_ops_500k"] / list_t) * 1000 if list_t > 0 else 0
        cprint(f"      耗时:        {list_t:.3f} s", C.WHITE)
        cprint(f"      最终长度:    {list_len:,}", C.WHITE)
        cprint(f"      单项得分:    {list_score:>10.0f}", C.GREEN, bold=True)
        results["list_time"] = round(list_t, 3)
        results["list_length"] = list_len
        results["list_score"] = round(list_score, 0)
        scores["list_ops_500k"] = list_score
        idx += 1

    # IO
    if "io_1m" in ordered_keys:
        print()
        cprint(f"[{idx}/{total}] I/O 吞吐 — 1MB 二进制 + 10,000 行文本读写", C.YELLOW, bold=True)
        if not args.silent:
            cprint("      计算中，请稍候...", C.GRAY)
        io_t, io_bin_size, io_lines = bench_io(1_000_000)
        io_score = (GEN2_BASELINE["io_1m"] / io_t) * 1000 if io_t > 0 else 0
        cprint(f"      耗时:        {io_t:.3f} s", C.WHITE)
        cprint(f"      二进制大小:  {io_bin_size / 1024:.1f} KB", C.WHITE)
        cprint(f"      文本行数:    {io_lines:,}", C.WHITE)
        cprint(f"      单项得分:    {io_score:>10.0f}", C.GREEN, bold=True)
        results["io_time"] = round(io_t, 3)
        results["io_bin_kb"] = round(io_bin_size / 1024, 1)
        results["io_lines"] = io_lines
        results["io_score"] = round(io_score, 0)
        scores["io_1m"] = io_score
        idx += 1

    # GIL（不计分）
    if include_gil:
        print()
        cprint(f"[{idx}/{total}] GIL 并发 — {cores} 线程 CPU 密集型加速比", C.YELLOW, bold=True)
        if not args.silent:
            cprint("      计算中，请稍候...", C.GRAY)
        gil_single, gil_multi, gil_speedup, gil_eff = bench_gil(1_000_000, workers=cores)
        cprint(f"      单线程耗时:  {gil_single:.3f} s", C.WHITE)
        cprint(f"      多线程耗时:  {gil_multi:.3f} s", C.WHITE)
        cprint(f"      实际加速比:  {gil_speedup:.2f}x", C.WHITE)
        cprint(f"      并发效率:    {gil_eff*100:.1f}%", C.WHITE)
        results["gil_single_time"] = round(gil_single, 3)
        results["gil_multi_time"] = round(gil_multi, 3)
        results["gil_speedup"] = round(gil_speedup, 2)
        results["gil_efficiency"] = round(gil_eff, 4)

    # 动态权重计算（归一化）
    raw_weights = {k: GEN2_BASELINE["weights"][k] for k in ordered_keys}
    total_w = sum(raw_weights.values())
    norm_weights = {k: (v / total_w if total_w > 0 else 0) for k, v in raw_weights.items()}

    custom_total = sum(scores[k] * norm_weights[k] for k in ordered_keys)

    # 报告
    print()
    cprint("=" * 60, C.BLUE, bold=True)
    cprint("           客 制 化 测 试 评 分 报 告", C.BLUE, bold=True)
    cprint("=" * 60, C.BLUE, bold=True)
    for k in ordered_keys:
        item = next(i for i in registry if i["key"] == k)
        pct = norm_weights[k] * 100
        cprint(f"  {item['name'] + f' ({pct:.0f}%)':<24} {scores[k]:>10.0f}", C.WHITE)
    cprint("-" * 60, C.GRAY)
    cprint(f"  {'客制化综合得分':<24} {custom_total:>10.0f}", C.GREEN, bold=True)
    if include_gil:
        cprint(f"  {'并发效率指数':<24} {gil_eff*100:>9.1f}%", C.CYAN, bold=True)
    cprint("=" * 60, C.BLUE, bold=True)

    return {
        "mode": "custom",
        "custom_mode": True,
        "custom_items": ordered_keys,
        "custom_weights": {k: round(v, 4) for k, v in norm_weights.items()},
        "custom_total_score": round(custom_total, 0),
        "cpu": cpu_name,
        "python": py_ver,
        "cores": cores,
        "timestamp": timestamp,
        **results
    }
# ============ 主程序 ============
def main():
    parser = argparse.ArgumentParser(description="Catchmark Benchmark Suite")
    parser.add_argument("--output", "-o", type=str, default=None,
                        help="指定结果文件保存路径（默认保存到桌面 Catchmark_用户名 文件夹）")
    parser.add_argument("--plain", action="store_true",
                        help="同时输出未加密的 JSON 文件（调试用）")
    parser.add_argument("--silent", "-s", action="store_true",
                        help="静默模式：不显示彩色输出，不弹出通知")
    parser.add_argument("--no-progress", action="store_true",
                        help="禁用进度条，恢复原版 pool.map 性能")
    parser.add_argument("--no-notify", action="store_true",
                        help="禁用 Windows 通知")
    parser.add_argument("--neo", action="store_true",
                        help="直接启动 Neo 扩展测试，跳过模式选择")
    parser.add_argument("--classic", action="store_true",
                        help="直接启动经典测试，跳过模式选择")
    parser.add_argument("--gen2", action="store_true",
                        help="直接启动 Gen2 全面测试，跳过模式选择")
    parser.add_argument("--custom", action="store_true",
                        help="直接启动客制化测试，自行选择测试项目")
    args = parser.parse_args()

    # 静默模式覆盖
    if args.silent:
        global cprint
        def cprint(text, color="", bold=False, end="\n"):
            print(text, end=end)

    # ============ 模式选择 ============
    mode = "classic"
    if args.custom:
        mode = "custom"
    elif args.gen2:
        mode = "gen2"
    elif args.neo:
        mode = "neo"
    elif args.classic:
        mode = "classic"
    elif not args.silent:

                print()
                cprint("=" * 60, C.CYAN, bold=True)
                cprint("         Catchmark Benchmark Suite  v2.4.0 (Custom)", C.CYAN, bold=True)
                cprint("=" * 60, C.CYAN, bold=True)
                print()
                cprint("  请选择测试模式:", C.WHITE, bold=True)
                print()
                cprint("  [1] 经典测试", C.GREEN, bold=True)
                cprint("      大整数累加 + 矩阵乘法 + JSON 混合负载", C.GRAY)
                cprint("      耗时较短，适合快速评估", C.GRAY)
                print()
                cprint("  [2] Neo 扩展测试", C.MAGENTA, bold=True)
                cprint("      经典三项 + 素数筛 + 字符串处理 + 字典运算", C.GRAY)
                cprint("      更全面，耗时较长", C.GRAY)
                print()
                cprint("  [3] Gen2 全面测试", C.ORANGE, bold=True)
                cprint("      Neo 六项 + 内存带宽 + 列表操作 + I/O 吞吐 + GIL 并发", C.GRAY)
                cprint("      最全面，耗时最长，面向高级用户", C.GRAY)
                print()
                cprint("  [4] 退出", C.RED)
                print()
                cprint("  [5] 客制化测试", C.BLUE, bold=True)
                cprint("      自选测试项目组合，动态计算权重", C.GRAY)
                cprint("      适合有特定评估需求的用户", C.GRAY)
                print()
                cprint("  /\\_/\\   /\\_/\\   /\\_/\\   /\\_/\\   /\\_/\\   /\\_/\\   /\\_/\\", C.GRAY)
                cprint(" ( o.o ) ( o.o ) ( o.o ) ( o.o ) ( o.o ) ( o.o ) ( o.o )", C.GRAY)
                cprint("  > ^ <   > ^ <   > ^ <   > ^ <   > ^ <   > ^ <   > ^ <", C.GRAY)
                print()

                while True:
                    try:
                        choice = input("  输入选项 (1/2/3/4/5): ").strip()
                        if choice == "1":
                            mode = "classic"
                            break
                        elif choice == "2":
                            mode = "neo"
                            break
                        elif choice == "3":
                            mode = "gen2"
                            break
                        elif choice == "4":
                            print("\n  已退出。")
                            return
                        elif choice == "5":
                            mode = "custom"
                            break
                        else:
                            cprint("  无效输入，请重新选择。", C.RED)
                    except (EOFError, KeyboardInterrupt):
                        print("\n  已退出。")
                        return
    else:
        mode = "classic"

    mode_names = {
        "classic": "经典测试",
        "neo": "Neo 扩展测试",
        "gen2": "Gen2 全面测试",
        "custom": "客制化测试"
    }
    mode_name = mode_names[mode]
    total_tests = {"classic": 3, "neo": 6, "gen2": 10, "custom": 0}[mode]

    cpu_name = get_cpu_name()
    py_ver = sys.version.split()[0]
    cores = mp.cpu_count()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ============ 客制化模式直接跳转 ============
    if mode == "custom":
        custom_data = run_custom_mode(args, cpu_name, py_ver, cores, timestamp)
        if custom_data is None:
            return
        data = custom_data
        json_str = json.dumps(data, ensure_ascii=False, indent=2)
        encrypted = encrypt(json_str, offset=7350)

        # 保存
        if args.output:
            result_file = Path(args.output)
            result_dir = result_file.parent
        else:
            username = getpass.getuser()
            result_dir = Path.home() / "Desktop" / f"Catchmark_{username}"
            result_dir.mkdir(parents=True, exist_ok=True)
            suffix = "_Custom"
            filename = f"Benchmark_Result{suffix}_{datetime.now():%Y%m%d_%H%M%S}.wnpbr"
            result_file = result_dir / filename

        try:
            with result_file.open("w", encoding="utf-8") as f:
                f.write(encrypted)

            if args.plain:
                plain_file = result_file.with_suffix(".json")
                with plain_file.open("w", encoding="utf-8") as f:
                    f.write(json_str)
                cprint(f"\n[调试] 明文 JSON 已保存: {plain_file.resolve()}", C.MAGENTA)

            print()
            cprint("结果已保存至:", C.WHITE)
            cprint(f"  {result_file.resolve()}", C.CYAN)
            cprint("（.wnpbr 文件需用 Catchmark Benchmark Viewer 程序查看）", C.GRAY)

            if not args.silent and not args.no_notify:
                final_score = int(data["custom_total_score"])
                notify("Catchmark Benchmark 完成", f"客制化测试 综合得分: {final_score}")

        except PermissionError:
            print()
            cprint("[错误] 没有权限写入目标文件夹。", C.RED, bold=True)
            cprint(f"目标路径: {result_dir}", C.WHITE)
            cprint("请检查文件夹权限或安全软件设置。", C.GRAY)
        except Exception as e:
            print()
            cprint(f"[错误] 保存结果文件时出错: {e}", C.RED, bold=True)
        return

    print()
    cprint("=" * 60, C.CYAN, bold=True)
    cprint("         Catchmark  Python 综合性能 Benchmark", C.CYAN, bold=True)
    cprint(f"         模式: {mode_name}", C.CYAN, bold=True)
    cprint("=" * 60, C.CYAN, bold=True)
    cprint(f"  CPU 型号:   {cpu_name}", C.WHITE)
    cprint(f"  Python:     {py_ver}", C.WHITE)
    cprint(f"  逻辑核心:   {cores}", C.WHITE)
    cprint("-" * 60, C.GRAY)

    # ============ 经典三项 ============
    # 1. 大整数
    print()
    cprint(f"[1/{total_tests}] 大整数累加 — 斐波那契第 10,000,000 项", C.YELLOW, bold=True)
    if not args.silent:
        cprint("      计算中，请稍候（通常数十秒至数分钟）...", C.GRAY)
    fib_val, fib_t = bench_fib(10_000_000, progress=not args.no_progress)
    fib_score = (BASELINE["fib_10m"] / fib_t) * 1000 if fib_t > 0 else 0
    cprint(f"      耗时:      {fib_t:.3f} s", C.WHITE)
    cprint(f"      结果位数:  {len(str(fib_val))}", C.WHITE)
    cprint(f"      单项得分:  {fib_score:>10.0f}", C.GREEN, bold=True)

    # 2. 矩阵
    print()
    cprint(f"[2/{total_tests}] 浮点矩阵乘法 — 512 x 512", C.YELLOW, bold=True)
    if not args.silent:
        cprint("      计算中，请稍候...", C.GRAY)
    mat_t, mat_gflops, mat_chk = bench_matmul(512)
    mat_score = (BASELINE["matmul_512"] / mat_t) * 1000 if mat_t > 0 else 0
    cprint(f"      耗时:        {mat_t:.3f} s", C.WHITE)
    cprint(f"      等效 GFLOPS: {mat_gflops:.3f}", C.WHITE)
    cprint(f"      校验和:      {mat_chk:.4f}", C.WHITE)
    cprint(f"      单项得分:    {mat_score:>10.0f}", C.GREEN, bold=True)

    # 3. JSON
    print()
    cprint(f"[3/{total_tests}] JSON 混合负载 — 200,000 条记录", C.YELLOW, bold=True)
    if not args.silent:
        cprint("      计算中，请稍候...", C.GRAY)
    json_t, json_size, json_hash, json_cnt = bench_json(200_000)
    json_score = (BASELINE["json_200k"] / json_t) * 1000 if json_t > 0 else 0
    cprint(f"      耗时:        {json_t:.3f} s", C.WHITE)
    cprint(f"      JSON 大小:   {json_size / 1024 / 1024:.2f} MB", C.WHITE)
    cprint(f"      SHA256 前缀: {json_hash}", C.WHITE)
    cprint(f"      单项得分:    {json_score:>10.0f}", C.GREEN, bold=True)

    # 经典综合
    w = BASELINE["weights"]
    classic_total = fib_score * w["fib_10m"] + mat_score * w["matmul_512"] + json_score * w["json_200k"]

    print()
    cprint("=" * 60, C.CYAN, bold=True)
    cprint("              经 典 测 试 评 分 报 告", C.CYAN, bold=True)
    cprint("=" * 60, C.CYAN, bold=True)
    cprint(f"  {'大整数累加 (40%)':<24} {fib_score:>10.0f}", C.WHITE)
    cprint(f"  {'矩阵乘法 (30%)':<24} {mat_score:>10.0f}", C.WHITE)
    cprint(f"  {'JSON 混合负载 (30%)':<24} {json_score:>10.0f}", C.WHITE)
    cprint("-" * 60, C.GRAY)
    cprint(f"  {'经典综合得分':<24} {classic_total:>10.0f}", C.GREEN, bold=True)
    cprint("=" * 60, C.CYAN, bold=True)

    # ============ Neo 扩展项 ============
    neo_data = {}
    neo_total = 0.0

    if mode in ("neo", "gen2"):
        print()
        cprint("-" * 60, C.MAGENTA)
        cprint("              N E O  扩 展 测 试", C.MAGENTA, bold=True)
        cprint("-" * 60, C.MAGENTA)

        # 4. 素数筛
        print()
        cprint(f"[4/{total_tests}] 素数筛 — 埃拉托斯特尼筛法 10,000,000", C.YELLOW, bold=True)
        if not args.silent:
            cprint("      计算中，请稍候...", C.GRAY)
        prime_t, prime_count = bench_prime_sieve(10_000_000)
        prime_score = (NEO_BASELINE["prime_10m"] / prime_t) * 1000 if prime_t > 0 else 0
        cprint(f"      耗时:        {prime_t:.3f} s", C.WHITE)
        cprint(f"      素数个数:    {prime_count:,}", C.WHITE)
        cprint(f"      单项得分:    {prime_score:>10.0f}", C.GREEN, bold=True)

        # 5. 字符串正则
        print()
        cprint(f"[5/{total_tests}] 字符串处理 — 100,000 条正则匹配", C.YELLOW, bold=True)
        if not args.silent:
            cprint("      计算中，请稍候...", C.GRAY)
        str_t, str_matches = bench_str_regex(100_000)
        str_score = (NEO_BASELINE["str_regex_100k"] / str_t) * 1000 if str_t > 0 else 0
        cprint(f"      耗时:        {str_t:.3f} s", C.WHITE)
        cprint(f"      匹配次数:    {str_matches:,}", C.WHITE)
        cprint(f"      单项得分:    {str_score:>10.0f}", C.GREEN, bold=True)

        # 6. 字典操作
        print()
        cprint(f"[6/{total_tests}] 字典运算 — 500,000 次插入/查找/排序", C.YELLOW, bold=True)
        if not args.silent:
            cprint("      计算中，请稍候...", C.GRAY)
        dict_t, dict_len, dict_hits, dict_top = bench_dict_ops(500_000)
        dict_score = (NEO_BASELINE["dict_500k"] / dict_t) * 1000 if dict_t > 0 else 0
        cprint(f"      耗时:        {dict_t:.3f} s", C.WHITE)
        cprint(f"      字典大小:    {dict_len:,}", C.WHITE)
        cprint(f"      查找命中:    {dict_hits:,}", C.WHITE)
        cprint(f"      单项得分:    {dict_score:>10.0f}", C.GREEN, bold=True)

        # Neo 综合
        nw = NEO_BASELINE["weights"]
        neo_total = prime_score * nw["prime_10m"] + str_score * nw["str_regex_100k"] + dict_score * nw["dict_500k"]

        print()
        cprint("=" * 60, C.MAGENTA, bold=True)
        cprint("              N E O  综 合 评 分 报 告", C.MAGENTA, bold=True)
        cprint("=" * 60, C.MAGENTA, bold=True)
        cprint(f"  {'素数筛 (40%)':<24} {prime_score:>10.0f}", C.WHITE)
        cprint(f"  {'字符串处理 (30%)':<24} {str_score:>10.0f}", C.WHITE)
        cprint(f"  {'字典运算 (30%)':<24} {dict_score:>10.0f}", C.WHITE)
        cprint("-" * 60, C.GRAY)
        cprint(f"  {'Neo 综合得分':<24} {neo_total:>10.0f}", C.GREEN, bold=True)
        cprint("=" * 60, C.MAGENTA, bold=True)

        neo_data = {
            "neo_mode": True,
            "prime_time": round(prime_t, 3),
            "prime_count": prime_count,
            "prime_score": round(prime_score, 0),
            "str_time": round(str_t, 3),
            "str_matches": str_matches,
            "str_score": round(str_score, 0),
            "dict_time": round(dict_t, 3),
            "dict_size": dict_len,
            "dict_hits": dict_hits,
            "dict_top_sum": round(dict_top, 2),
            "dict_score": round(dict_score, 0),
            "neo_total_score": round(neo_total, 0)
        }

    # ============ Gen2 扩展项 ============
    gen2_data = {}
    gen2_total = 0.0
    gil_data = {}

    if mode == "gen2":
        print()
        cprint("-" * 60, C.ORANGE)
        cprint("              G E N 2  扩 展 测 试", C.ORANGE, bold=True)
        cprint("-" * 60, C.ORANGE)

        # 7. 内存带宽
        print()
        cprint(f"[7/{total_tests}] 内存带宽 — 50MB bytearray 读写 + 对象分配", C.YELLOW, bold=True)
        if not args.silent:
            cprint("      计算中，请稍候...", C.GRAY)
        mem_t, mem_bw = bench_memory(50_000_000)
        mem_score = (GEN2_BASELINE["memory_50m"] / mem_t) * 1000 if mem_t > 0 else 0
        cprint(f"      耗时:        {mem_t:.3f} s", C.WHITE)
        cprint(f"      等效带宽:    {mem_bw:.1f} MB/s", C.WHITE)
        cprint(f"      单项得分:    {mem_score:>10.0f}", C.GREEN, bold=True)

        # 8. 列表操作
        print()
        cprint(f"[8/{total_tests}] 列表操作 — 500,000 次追加/排序/插入/切片", C.YELLOW, bold=True)
        if not args.silent:
            cprint("      计算中，请稍候...", C.GRAY)
        list_t, list_len = bench_list_ops(500_000)
        list_score = (GEN2_BASELINE["list_ops_500k"] / list_t) * 1000 if list_t > 0 else 0
        cprint(f"      耗时:        {list_t:.3f} s", C.WHITE)
        cprint(f"      最终长度:    {list_len:,}", C.WHITE)
        cprint(f"      单项得分:    {list_score:>10.0f}", C.GREEN, bold=True)

        # 9. I/O 吞吐
        print()
        cprint(f"[9/{total_tests}] I/O 吞吐 — 1MB 二进制 + 10,000 行文本读写", C.YELLOW, bold=True)
        if not args.silent:
            cprint("      计算中，请稍候...", C.GRAY)
        io_t, io_bin_size, io_lines = bench_io(1_000_000)
        io_score = (GEN2_BASELINE["io_1m"] / io_t) * 1000 if io_t > 0 else 0
        cprint(f"      耗时:        {io_t:.3f} s", C.WHITE)
        cprint(f"      二进制大小:  {io_bin_size / 1024:.1f} KB", C.WHITE)
        cprint(f"      文本行数:    {io_lines:,}", C.WHITE)
        cprint(f"      单项得分:    {io_score:>10.0f}", C.GREEN, bold=True)

        # 10. GIL 并发（不计入总分）
        print()
        cprint(f"[10/{total_tests}] GIL 并发 — {cores} 线程 CPU 密集型加速比", C.YELLOW, bold=True)
        if not args.silent:
            cprint("      计算中，请稍候...", C.GRAY)
        gil_single, gil_multi, gil_speedup, gil_eff = bench_gil(1_000_000, workers=cores)
        cprint(f"      单线程耗时:  {gil_single:.3f} s", C.WHITE)
        cprint(f"      多线程耗时:  {gil_multi:.3f} s", C.WHITE)
        cprint(f"      实际加速比:  {gil_speedup:.2f}x", C.WHITE)
        cprint(f"      并发效率:    {gil_eff*100:.1f}%", C.WHITE)
        cprint(f"      {'(GIL 限制下，理想应为 ' + str(cores) + 'x)'}", C.GRAY)

        # Gen2 综合
        g2w = GEN2_BASELINE["weights"]
        gen2_total = (
            fib_score * g2w["fib_10m"] +
            mat_score * g2w["matmul_512"] +
            json_score * g2w["json_200k"] +
            prime_score * g2w["prime_10m"] +
            str_score * g2w["str_regex_100k"] +
            dict_score * g2w["dict_500k"] +
            mem_score * g2w["memory_50m"] +
            list_score * g2w["list_ops_500k"] +
            io_score * g2w["io_1m"]
        )

        print()
        cprint("=" * 60, C.ORANGE, bold=True)
        cprint("              G E N 2  综 合 评 分 报 告", C.ORANGE, bold=True)
        cprint("=" * 60, C.ORANGE, bold=True)
        cprint(f"  {'大整数累加 (20%)':<24} {fib_score:>10.0f}", C.WHITE)
        cprint(f"  {'矩阵乘法 (15%)':<24} {mat_score:>10.0f}", C.WHITE)
        cprint(f"  {'JSON 混合负载 (10%)':<24} {json_score:>10.0f}", C.WHITE)
        cprint(f"  {'素数筛 (15%)':<24} {prime_score:>10.0f}", C.WHITE)
        cprint(f"  {'字符串处理 (10%)':<24} {str_score:>10.0f}", C.WHITE)
        cprint(f"  {'字典运算 (10%)':<24} {dict_score:>10.0f}", C.WHITE)
        cprint(f"  {'内存带宽 (10%)':<24} {mem_score:>10.0f}", C.WHITE)
        cprint(f"  {'列表操作 (5%)':<24} {list_score:>10.0f}", C.WHITE)
        cprint(f"  {'I/O 吞吐 (5%)':<24} {io_score:>10.0f}", C.WHITE)
        cprint("-" * 60, C.GRAY)
        cprint(f"  {'Gen2 综合得分':<24} {gen2_total:>10.0f}", C.GREEN, bold=True)
        cprint(f"  {'并发效率指数':<24} {gil_eff*100:>9.1f}%", C.CYAN, bold=True)
        cprint("=" * 60, C.ORANGE, bold=True)

        gen2_data = {
            "gen2_mode": True,
            "memory_time": round(mem_t, 3),
            "memory_bandwidth": round(mem_bw, 1),
            "memory_score": round(mem_score, 0),
            "list_time": round(list_t, 3),
            "list_length": list_len,
            "list_score": round(list_score, 0),
            "io_time": round(io_t, 3),
            "io_bin_kb": round(io_bin_size / 1024, 1),
            "io_lines": io_lines,
            "io_score": round(io_score, 0),
            "gen2_total_score": round(gen2_total, 0)
        }

        gil_data = {
            "gil_single_time": round(gil_single, 3),
            "gil_multi_time": round(gil_multi, 3),
            "gil_speedup": round(gil_speedup, 2),
            "gil_efficiency": round(gil_eff, 4),
        }

    # ============ 构造 JSON 并加密 ============
    data = {
        "cpu": cpu_name,
        "python": py_ver,
        "cores": cores,
        "timestamp": timestamp,
        "mode": mode,
        "fib_time": round(fib_t, 3),
        "fib_digits": len(str(fib_val)),
        "fib_score": round(fib_score, 0),
        "mat_time": round(mat_t, 3),
        "mat_gflops": round(mat_gflops, 3),
        "mat_checksum": round(mat_chk, 4),
        "mat_score": round(mat_score, 0),
        "json_time": round(json_t, 3),
        "json_size_mb": round(json_size / 1024 / 1024, 2),
        "json_sha16": json_hash,
        "json_score": round(json_score, 0),
        "classic_total_score": round(classic_total, 0)
    }

    if mode in ("neo", "gen2"):
        data.update(neo_data)

    if mode == "gen2":
        data.update(gen2_data)
        data.update(gil_data)

    json_str = json.dumps(data, ensure_ascii=False, indent=2)
    encrypted = encrypt(json_str, offset=7350)

    # 保存
    if args.output:
        result_file = Path(args.output)
        result_dir = result_file.parent
    else:
        username = getpass.getuser()
        result_dir = Path.home() / "Desktop" / f"WNPBR_{username}"
        result_dir.mkdir(parents=True, exist_ok=True)
        suffix = {"classic": "", "neo": "_Neo", "gen2": "_Gen2", "custom": "_Custom"}[mode]
        filename = f"Benchmark_Result{suffix}_{datetime.now():%Y%m%d_%H%M%S}.wnpbr"
        result_file = result_dir / filename

    try:
        with result_file.open("w", encoding="utf-8") as f:
            f.write(encrypted)

        if args.plain:
            plain_file = result_file.with_suffix(".json")
            with plain_file.open("w", encoding="utf-8") as f:
                f.write(json_str)
            cprint(f"\n[调试] 明文 JSON 已保存: {plain_file.resolve()}", C.MAGENTA)

        print()
        cprint("结果已保存至:", C.WHITE)
        cprint(f"  {result_file.resolve()}", C.CYAN)
        cprint("（.wnpbr 文件需用 Catchmark Benchmark Viewer 程序查看）", C.GRAY)

        if not args.silent and not args.no_notify:
            if mode == "gen2":
                final_score = int(gen2_total)
            elif mode == "neo":
                final_score = int(neo_total)
            else:
                final_score = int(classic_total)
            notify("Catchmark Benchmark 完成", f"{mode_name} 综合得分: {final_score}")

    except PermissionError:
        print()
        cprint("[错误] 没有权限写入目标文件夹。", C.RED, bold=True)
        cprint(f"目标路径: {result_dir}", C.WHITE)
        cprint("请检查文件夹权限或安全软件设置。", C.GRAY)
    except Exception as e:
        print()
        cprint(f"[错误] 保存结果文件时出错: {e}", C.RED, bold=True)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n用户中断。")
    except Exception as e:
        cprint(f"\n运行出错: {e}", C.RED, bold=True)
    if not sys.argv[1:] or "--silent" not in sys.argv:
        input("\n按 Enter 键退出...")
