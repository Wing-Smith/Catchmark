import time
import random

def matmul(n):
    # 纯 Python 列表，不依赖 numpy
    A = [[random.random() for _ in range(n)] for _ in range(n)]
    B = [[random.random() for _ in range(n)] for _ in range(n)]
    C = [[0.0] * n for _ in range(n)]
    
    t0 = time.perf_counter()
    for i in range(n):
        for k in range(n):
            aik = A[i][k]
            for j in range(n):
                C[i][j] += aik * B[k][j]
    t1 = time.perf_counter()
    
    flops = 2 * n ** 3
    elapsed = t1 - t0
    print(f"矩阵 {n}x{n} 耗时: {elapsed:.3f}s")
    print(f"近似 GFLOPS: {flops / elapsed / 1e9:.3f}")

if __name__ == "__main__":
    n = int(input("矩阵维度 (建议 256 或 512): "))
    matmul(n)
