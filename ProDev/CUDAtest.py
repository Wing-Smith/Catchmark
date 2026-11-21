import cupy as cp
print(cp.cuda.runtime.getDeviceCount())  # 输出GPU数量，若为1则说明识别成功
