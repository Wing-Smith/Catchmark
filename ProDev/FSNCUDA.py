n = int(input("请输入要生成的斐波那契数列项数: "))

# 处理前两项的特殊情况
if n >= 1:
    print(f"#1#--0")
if n >= 2:
    print(f"#2#--1")

# 计算并输出后续项
a, b = 0, 1
for i in range(3, n + 1):
    c = a + b
    print(f"#{i}#--{c}")
    a, b = b, c
