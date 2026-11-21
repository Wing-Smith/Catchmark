import multiprocessing
import time

def fib_chunk(start, end, a, b):
    """计算斐波那契数列的一个分片"""
    result = []
    current_a, current_b = a, b
    for i in range(start, end + 1):
        c = current_a + current_b
        result.append((i, c))
        current_a, current_b = current_b, c
    return result

def main():
    n = int(input("请输入斐波那契数列项数: "))
    if n < 1:
        print("项数必须大于0")
        return
    
    start_time = time.time()
    
    # 前两项单独处理
    results = []
    if n >= 1:
        results.append((1, 0))
    if n >= 2:
        results.append((2, 1))
    
    if n > 2:
        # 计算需要分片的部分（从第3项开始）
        num_processes = multiprocessing.cpu_count()  # 自动获取CPU核心数
        total = n - 2  # 从第3项到第n项的总数量
        chunk_size = max(total // num_processes, 1)  # 每个进程处理的分片大小
        
        # 准备每个进程的参数
        pool = multiprocessing.Pool(processes=num_processes)
        tasks = []
        current_start = 3
        a, b = 0, 1  # 第1项和第2项的值
        
        while current_start <= n:
            current_end = min(current_start + chunk_size - 1, n)
            # 计算当前分片的起始值（a和b对应前两项）
            tasks.append(pool.apply_async(
                fib_chunk, 
                args=(current_start, current_end, a, b)
            ))
            # 提前计算下一个分片的起始值（避免进程间依赖）
            for _ in range(current_end - current_start + 1):
                a, b = b, a + b
            current_start = current_end + 1
        
        # 收集所有进程的结果
        for task in tasks:
            results.extend(task.get())
        pool.close()
        pool.join()
    
    # 按序号排序并输出（或写入文件）
    results.sort(key=lambda x: x[0])
    # 如需输出，建议写入文件以避免I/O瓶颈
    # with open("fib_results.txt", "w") as f:
    #     for idx, val in results:
    #         f.write(f"#{idx}#--{val}\n")
    
    print(f"总耗时: {time.time() - start_time:.2f}秒")

if __name__ == "__main__":
    main()
