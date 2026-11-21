def main():
    print("=" * 50)
    print("      Python Benchmark 评分计算器")
    print("=" * 50)
    print("基准（单项 1000 分）：")
    print("  斐波那契 10M : 300.0 秒")
    print("  矩阵 512×512 : 5.0 秒")
    print("  JSON 200k    : 0.5 秒")
    print("权重：大整数 40% / 矩阵 30% / JSON 30%")
    print("-" * 50)

    # 输入
    fib_t = input("斐波那契 10M 耗时（秒）: ").strip()
    mat_t = input("矩阵 512×512 耗时（秒）: ").strip()
    json_t = input("JSON 200k 耗时（秒）    : ").strip()

    # 转换
    try:
        fib = float(fib_t) if fib_t else 0
        mat = float(mat_t) if mat_t else 0
        json = float(json_t) if json_t else 0
    except ValueError:
        print("\n错误：请输入有效的数字。")
        return

    # 基准
    BASE_FIB = 300.0
    BASE_MAT = 5.0
    BASE_JSON = 0.5

    # 计算得分
    fib_score = (BASE_FIB / fib) * 1000 if fib > 0 else 0
    mat_score = (BASE_MAT / mat) * 1000 if mat > 0 else 0
    json_score = (BASE_JSON / json) * 1000 if json > 0 else 0

    total = fib_score * 0.4 + mat_score * 0.3 + json_score * 0.3

    # 输出
    print("\n" + "=" * 50)
    print("              评 分 报 告")
    print("=" * 50)
    print(f"{'大整数累加 (40%)':<20} {fib_score:>10.1f}")
    print(f"{'矩阵乘法 (30%)':<20} {mat_score:>10.1f}")
    print(f"{'JSON 混合 (30%)':<20} {json_score:>10.1f}")
    print("-" * 50)
    print(f"{'综合得分':<20} {total:>10.1f}")
    print("=" * 50)

    # 评级
    if total >= 2000:
        grade = "S（顶级）"
    elif total >= 1500:
        grade = "A（优秀）"
    elif total >= 1000:
        grade = "B（良好）"
    elif total >= 600:
        grade = "C（及格）"
    else:
        grade = "D（较弱）"
    print(f"评级: {grade}")


if __name__ == "__main__":
    main()
