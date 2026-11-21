#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WN-PBR 安装包密钥生成器

密钥规格:
  格式: XXXXX-XXXXX-XXXXX-XXXXX-XXXXX (25位, 5组)
  字符集: 23456789ABCDEFGHJKLMNPQRSTUVWXYZ (32字符, 去掉 0/O/1/I/l)
  第1组第1位: Gen 标识 (Gen1='2', Gen2='3', ... 使用字符集内字符)
  第1组第2位: 组件掩码 (V=Viewer, D=Decryptor, A=全能)
  第2-4组: 随机载荷
  第5组: 自定义校验和

三种密钥类型:
  V 型 -> 仅解锁 WN-PBR Benchmark Viewer
  D 型 -> 仅解锁 WN-PBR Decryptor
  A 型 -> 同时解锁 Viewer + Decryptor

用法:
  python keygen.py -t V -n 10         # 生成10个 Gen2 Viewer 密钥
  python keygen.py -t V -n 10 --gen 1 # 生成10个 Gen1 Viewer 密钥
  python keygen.py -t D -n 5          # 生成5个 Gen2 Decryptor 密钥
  python keygen.py -t A -n 3 --verify # 生成并验证
"""

import secrets
import argparse

CHARSET = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"
# Gen 标识映射: Gen1 -> '2' (字符集第0位), Gen2 -> '3' (字符集第1位)
GEN_MAP = {1: "2", 2: "3"}


def char_to_val(c: str) -> int:
    return CHARSET.index(c.upper())


def val_to_char(v: int) -> str:
    return CHARSET[v & 0x1F]


def compute_checksum(key20: str) -> str:
    """计算前20位字符的校验和 (5字符)"""
    h = 0x12345678
    for i, c in enumerate(key20):
        v = char_to_val(c)
        h ^= (v << (i % 27))
        h = ((h << 3) | (h >> 29)) & 0xFFFFFFFF
        h = (h + v * 2654435761) & 0xFFFFFFFF
        h ^= (v >> (i % 3 + 1))

    result = ""
    for i in range(5):
        n = (h >> (i * 5)) & 0x1F
        result += val_to_char(n)
    return result


def validate_key(key: str, expected_type: str = None, expected_gen: int = None) -> tuple:
    """
    验证密钥合法性
    返回: (is_valid: bool, gen: str, key_type: str, masked: str)
    """
    stripped = key.upper().replace("-", "").replace(" ", "")
    if len(stripped) != 25:
        return False, None, None, None

    for c in stripped:
        if c not in CHARSET:
            return False, None, None, None

    gen = stripped[0]
    key_type = stripped[1]

    if expected_gen is not None:
        if gen != GEN_MAP.get(expected_gen):
            return False, None, None, None

    if key_type not in ("V", "D", "A"):
        return False, None, None, None

    if expected_type:
        if expected_type == "V" and key_type not in ("V", "A"):
            return False, None, None, None
        if expected_type == "D" and key_type not in ("D", "A"):
            return False, None, None, None

    checksum = stripped[20:25]
    expected = compute_checksum(stripped[0:20])
    if checksum != expected:
        return False, None, None, None

    masked_parts = []
    for i in range(5):
        part = stripped[i*5:(i+1)*5]
        visible = part[i]
        masked = visible + "****"
        masked_parts.append(masked)
    masked = "-".join(masked_parts)

    return True, gen, key_type, masked


def generate_key(key_type: str, gen: int = 2) -> str:
    if key_type not in ("V", "D", "A"):
        raise ValueError("key_type must be V, D, or A")
    if gen not in GEN_MAP:
        raise ValueError("gen must be 1 or 2")

    gen_id = GEN_MAP[gen]
    group1 = gen_id + key_type + "".join(secrets.choice(CHARSET) for _ in range(3))
    payload = "".join(secrets.choice(CHARSET) for _ in range(15))
    key20 = group1 + payload
    checksum = compute_checksum(key20)

    return f"{group1}-{payload[0:5]}-{payload[5:10]}-{payload[10:15]}-{checksum}"


def main():
    parser = argparse.ArgumentParser(description="WN-PBR 密钥生成器")
    parser.add_argument("-t", "--type", choices=["V", "D", "A"], required=True,
                        help="密钥类型: V=Viewer, D=Decryptor, A=全能")
    parser.add_argument("-n", "--count", type=int, default=1,
                        help="生成数量 (默认 1)")
    parser.add_argument("--gen", type=int, choices=[1, 2], default=2,
                        help="代数: 1=Gen1, 2=Gen2 (默认 2)")
    parser.add_argument("--verify", action="store_true",
                        help="生成后自动验证")
    args = parser.parse_args()

    type_names = {"V": "Viewer", "D": "Decryptor", "A": "全能"}
    gen_label = f"Gen{args.gen}"
    print(f"=== 生成 {args.count} 个 {type_names[args.type]} 密钥 ({gen_label}) ===\n")

    for i in range(args.count):
        key = generate_key(args.type, gen=args.gen)
        print(f"  [{i+1}] {key}")

        if args.verify:
            ok, gen, kt, masked = validate_key(key, args.type if args.type != "A" else None, args.gen)
            status = "✓ 验证通过" if ok else "✗ 验证失败"
            print(f"      {status} | 掩码: {masked} | 类型: {kt}")

    print("\n=== 完成 ===")
    print("提示: 请妥善保管密钥。安装程序会在维护模式下记住已授权的组件。")


if __name__ == "__main__":
    main()
