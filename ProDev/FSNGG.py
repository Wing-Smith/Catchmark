
#Wing North Studio
#CPU 性能基准测试

import multiprocessing as mp
import time
import sys

# ============ 全局函数（兼容 Windows spawn 模式） ============

def fast_doubling(n):
    """
    快速倍增法 O(log n)。
    标准定义：F(0)=0, F(1)=1。
    返回 (F(n), F(n+1))。
    """
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
    """
    纯累加法计算斐波那契块。
    输入: (start_idx, end_idx, a, b)
        start_idx : 该块起始项数（用户定义 F(1)=0）
        end_idx   : 该块结束项数
        a         : F(start_idx)
        b         : F(start_idx + 1)
    返回: (end_idx, F(end_idx))
    """
    start_idx, end_idx, a, b = args
    # 从 start_idx 递推到 end_idx，需要 (end_idx - start_idx) 步
    for _ in range(end_idx - start_idx):
        c = a + b
        a, b = b, c
    return (end_idx, a)


# ============ 主程序 ============

def main():
    # Python 3.13 取消大整数转字符串的位数限制
    sys.set_int_max_str_digits(10**7)

    n = int(input("请输入斐波那契数列项数: "))
    if n < 1:
        print("项数必须大于0")
        return

    start_time = time.time()

    # ---- 小项直接单线程，避免进程调度开销 ----
    if n == 1:
        result = 0
    elif n == 2:
        result = 1
    elif n < 8000:
        a, b = 0, 1
        for _ in range(2, n):
            a, b = b, a + b
        result = b
    else:
        # ---- 多进程并行：每个进程独立累加自己的块 ----
        num_workers = min(mp.cpu_count(), 16)
        total = n - 2  # 第3项到第n项需要递推

        chunk_size = total // num_workers
        tasks = []

        for i in range(num_workers):
            chunk_start = 3 + i * chunk_size
            if i == num_workers - 1:
                chunk_end = n
            else:
                chunk_end = chunk_start + chunk_size - 1

            # 用快速倍增法 O(log n) 获取该块起始状态
            # 用户定义 F(k) 对应标准 F(k-1)
            a, b = fast_doubling(chunk_start - 1)
            tasks.append((chunk_start, chunk_end, a, b))

        # 启动进程池，真正利用多核（每个进程独立 GIL）
        with mp.Pool(num_workers) as pool:
            results = pool.map(fib_chunk, tasks)

        # 提取第 n 项结果（最后一个块一定以 n 结尾）
        result = None
        for idx, val in results:
            if idx == n:
                result = val
                break

    # ---- 输出 ----
    elapsed = time.time() - start_time
    result_str = str(result)
    print(f"第{n}项斐波那契数（共{len(result_str)}位）")
    print(f"计算耗时: {elapsed:.6f}秒")

    if len(result_str) > 200:
        print(f"前100位: {result_str[:100]}")
        print(f"后100位: {result_str[-100:]}")


if __name__ == "__main__":
    main()
