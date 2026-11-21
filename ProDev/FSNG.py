import threading
import time
from queue import Queue
import sys

def fib_worker(queue, result_queue):
    while not queue.empty():
        start, end, a, b = queue.get()
        current_a, current_b = a, b
        for i in range(start, end + 1):
            c = current_a + current_b
            current_a, current_b = current_b, c
        result_queue.put((end, current_a))
        queue.task_done()

def main():
    # 针对Python 3.13的特定处理：使用足够大的数值而非None
    max_digits = 10**6  # 100万位，远超百万项斐波那契数的需求
    sys.set_int_max_str_digits(max_digits)
    
    n = int(input("请输入斐波那契数列项数: "))
    if n < 1:
        print("项数必须大于0")
        return
    
    start_time = time.time()
    
    if n == 1:
        final_value = 0
    elif n == 2:
        final_value = 1
    else:
        task_queue = Queue()
        result_queue = Queue()
        num_threads = min(threading.active_count() + 4, 16)
        
        total = n - 2
        chunk_size = max(total // num_threads, 1000)
        current_start = 3
        a, b = 0, 1
        
        while current_start <= n:
            current_end = min(current_start + chunk_size - 1, n)
            task_queue.put((current_start, current_end, a, b))
            # 预计算下一分片的起始值
            for _ in range(current_end - current_start + 1):
                a, b = b, a + b
            current_start = current_end + 1
        
        # 启动线程
        threads = []
        for _ in range(num_threads):
            t = threading.Thread(target=fib_worker, args=(task_queue, result_queue))
            t.start()
            threads.append(t)
        
        # 等待计算完成
        task_queue.join()
        
        # 获取最后一项结果
        final_value = None
        while not result_queue.empty():
            idx, val = result_queue.get()
            if idx == n:
                final_value = val
        
        # 等待所有线程结束
        for t in threads:
            t.join()
    
    # 输出结果（优先显示长度，可选显示完整值）
    try:
        print(f"第{n}项斐波那契数（共{len(str(final_value))}位）")
        # 如需显示完整值，取消下面一行注释（可能耗时较长）
        # print(f"数值: {final_value}")
    except Exception as e:
        print(f"计算完成，第{n}项斐波那契数计算成功")
    
    print(f"计算耗时: {time.time() - start_time:.6f}秒")

if __name__ == "__main__":
    main()
