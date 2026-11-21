import time
import json
import random
import hashlib

def mixed_bench(n=200_000):
    records = []
    t0 = time.perf_counter()
    
    for i in range(n):
        rec = {
            "id": i,
            "name": f"user_{i}_{random.randint(1000, 9999)}",
            "score": random.random() * 100,
            "tags": [f"tag{j}" for j in range(random.randint(3, 8))]
        }
        records.append(rec)
    
    # JSON 序列化
    text = json.dumps(records)
    
    # 哈希计算
    h = hashlib.sha256(text.encode()).hexdigest()
    
    # 字符串搜索
    count = text.count("tag5")
    
    t1 = time.perf_counter()
    
    print(f"处理 {n} 条记录耗时: {t1-t0:.3f}s")
    print(f"JSON 大小: {len(text) / 1024 / 1024:.2f} MB")
    print(f"SHA256: {h[:16]}...")
    print(f"'tag5' 出现次数: {count}")

if __name__ == "__main__":
    n = int(input("记录数 (建议 100000 或 200000): "))
    mixed_bench(n)
