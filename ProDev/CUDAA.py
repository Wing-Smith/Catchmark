import numba.cuda as cuda
import numpy as np
import time
import sys
from numba import float32

# ============ 温度监控（nvidia-ml-py 的导入名是 pynvml） ============
try:
    import pynvml
    pynvml.nvmlInit()
    handle = pynvml.nvmlDeviceGetHandleByIndex(0)
    HAS_NVML = True
except Exception:
    HAS_NVML = False

def get_temp():
    if not HAS_NVML:
        return None
    try:
        return pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
    except:
        return None

# ============ CUDA 内核 ============
@cuda.jit
def furnace_kernel(data, iterations, seed):
    idx = cuda.blockIdx.x * cuda.blockDim.x + cuda.threadIdx.x
    stride = cuda.blockDim.x * cuda.gridDim.x
    n = data.shape[0]
    
    for pos in range(idx, n, stride):
        x = float32(seed + pos)
        y = float32(1.0)
        z = float32(0.5)
        
        for _ in range(iterations):
            x = x * y + z
            y = y * x + z
            z = z * x + y
            if x > 1e6:
                x = x / 1e6
        
        data[pos] = x + y + z

# ============ 主程序 ============
def main():
    if not cuda.is_available():
        print("错误：Numba CUDA 不可用。请确认 NVIDIA 驱动已安装。")
        return
    
    dev = cuda.get_current_device()
    name = dev.name.decode() if isinstance(dev.name, bytes) else dev.name
    
    print("=" * 60)
    print(" CUDA GPU 压榨 / 分段计时器")
    print("=" * 60)
    print(f"设备: {name}")
    print(f"SM 数量: {dev.MULTIPROCESSOR_COUNT}")
    temp = get_temp()
    print(f"当前温度: {temp}°C" if temp else "温度监控: 未启用")
    print("-" * 60)
    
    # 模式选择
    try:
        m = input("模式 [1]快速验证  [2]满负载压榨  [3]自定义: ").strip()
    except:
        m = "2"
    
    if m == "1":
        n, iters, blocks, dur = 1024*1024, 1000, dev.MULTIPROCESSOR_COUNT*2, 5
    elif m == "3":
        n = int(input("元素数(如33554432): ") or "33554432")
        iters = int(input("迭代数(如50000): ") or "50000")
        blocks = int(input("Blocks: ") or str(dev.MULTIPROCESSOR_COUNT*8))
        dur = int(input("秒数(0=无限): ") or "30")
    else:
        n, iters, blocks, dur = 32*1024*1024, 50000, dev.MULTIPROCESSOR_COUNT*8, 30
    
    threads = 256
    print(f"\n数据: {n*4/1024/1024:.1f} MB | 线程: {blocks*threads:,} | 迭代: {iters:,}")
    print("运行中... Ctrl+C 随时停止\n")
    
    # 主机数据
    h_data = np.zeros(n, dtype=np.float32)
    
    # ============ H2D 计时 ============
    e_h2d1 = cuda.event(); e_h2d2 = cuda.event()
    e_h2d1.record()
    d_data = cuda.to_device(h_data)
    e_h2d2.record()
    e_h2d2.synchronize()
    h2d_ms = e_h2d1.elapsed_time(e_h2d2)
    
    # 预热（避免编译计入时间）
    furnace_kernel[1, 1](d_data[:1024], 1, 0)
    cuda.synchronize()
    
    # ============ 主循环（精确累加每次内核 GPU 时间） ============
    t0 = time.perf_counter()
    launches = 0
    total_flops = 0
    kern_total_ms = 0.0
    last_report = t0
    
    try:
        while True:
            e_k1 = cuda.event(); e_k2 = cuda.event()
            e_k1.record()
            furnace_kernel[blocks, threads](d_data, iters, launches)
            e_k2.record()
            e_k2.synchronize()
            
            kern_total_ms += e_k1.elapsed_time(e_k2)
            launches += 1
            total_flops += n * iters * 8
            
            now = time.perf_counter()
            if now - last_report >= 5.0:
                avg_kern = kern_total_ms / launches
                gflops = (n * iters * 8 / (avg_kern / 1000)) / 1e9
                t = f" | {get_temp()}°C" if get_temp() else ""
                print(f"[{now-t0:6.1f}s] 平均内核: {avg_kern:7.2f} ms | {gflops:7.2f} GFLOPS{t}")
                last_report = now
            
            if dur > 0 and now - t0 >= dur:
                break
    except KeyboardInterrupt:
        print("\n用户中断")
    
    total_s = time.perf_counter() - t0
    
    # ============ D2H 计时 ============
    e_d2h1 = cuda.event(); e_d2h2 = cuda.event()
    e_d2h1.record()
    h_result = d_data.copy_to_host()
    e_d2h2.record()
    e_d2h2.synchronize()
    d2h_ms = e_d2h1.elapsed_time(e_d2h2)
    
    # ============ 报告 ============
    print("\n" + "=" * 60)
    print(" 分段计时报告")
    print("=" * 60)
    print(f"  H2D 拷贝:        {h2d_ms:10.3f} ms")
    print(f"  内核执行(总计):  {kern_total_ms:10.3f} ms ({launches} 次)")
    print(f"  内核执行(平均):  {kern_total_ms/launches:10.3f} ms/次")
    print(f"  D2H 拷贝:        {d2h_ms:10.3f} ms")
    print(f"  Python 开销:     {total_s*1000 - h2d_ms - kern_total_ms - d2h_ms:10.3f} ms")
    print("-" * 60)
    print(f"  总耗时:          {total_s*1000:10.3f} ms")
    print(f"  总 FLOP:         {total_flops:,}")
    print(f"  平均性能:        {(total_flops/total_s)/1e9:10.2f} GFLOPS")
    if get_temp():
        print(f"  结束温度:        {get_temp()}°C")
    print(f"  结果校验:        {h_result[:5]}")
    print("=" * 60)

if __name__ == "__main__":
    main()
