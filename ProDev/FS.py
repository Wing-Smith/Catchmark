import cupy as cp

n = int(input("请输入要生成的斐波那契数列项数: "))

# 处理前两项的特殊情况（CPU输出，因为数值小且无需加速）
if n >= 1:
    print(f"#1#--0")
if n >= 2:
    print(f"#2#--1")

# 若项数大于2，使用GPU加速计算后续项
if n > 2:
    # 在GPU上初始化前两项
    a = cp.array(0, dtype=cp.int64)
    b = cp.array(1, dtype=cp.int64)
    for i in range(3, n + 1):
        # GPU上执行斐波那契计算
        c = a + b
        # 将结果从GPU拷贝到CPU并输出
        print(f"#{i}#--{c.get()}")
        # 更新GPU上的变量
        a, b = b, c
