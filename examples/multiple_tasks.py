import hashlib
import json
import math
import os
import random
import re
import string
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed

from yapflame import profile


def cpu_heavy_math(n: int = 800_000) -> float:
    total = 0.0
    for i in range(1, n + 1):
        total += math.sqrt(i) * math.sin(i) * math.cos(i)
    return total


def prime_sieve(limit: int = 200_000) -> list[int]:
    is_prime = [True] * (limit + 1)
    is_prime[0] = is_prime[1] = False
    for i in range(2, int(math.isqrt(limit)) + 1):
        if is_prime[i]:
            for j in range(i * i, limit + 1, i):
                is_prime[j] = False
    return [i for i, flag in enumerate(is_prime) if flag]


def sort_large_list(size: int = 2_000_000) -> None:
    data = [random.random() for _ in range(size)]
    data.sort()


def hash_data(rounds: int = 300_000) -> str:
    digest = b"seed"
    for _ in range(rounds):
        digest = hashlib.sha256(digest).digest()
    return digest.hex()


def json_serialization(rounds: int = 5_000) -> None:
    for _ in range(rounds):
        obj = {
            "id": random.randint(0, 1_000_000),
            "name": "".join(random.choices(string.ascii_letters, k=20)),
            "tags": [random.choice(["alpha", "beta", "gamma"]) for _ in range(10)],
            "nested": {"x": random.random(), "y": random.random()},
        }
        blob = json.dumps(obj)
        json.loads(blob)


def regex_matching() -> int:
    text = "".join(random.choices(string.ascii_lowercase + " ", k=500_000))
    patterns = [
        r"\b[a-z]{5}\b",
        r"([aeiou]){2,}",
        r"\b\w+ing\b",
        r"[bcdfg]{3,}",
        r"\b[a-m]+\b",
    ]
    total = 0
    for pat in patterns:
        total += len(re.findall(pat, text))
    return total


def file_io_work(num_files: int = 200, size_kb: int = 64) -> None:
    tmpdir = tempfile.mkdtemp(prefix="yapflame_")
    paths: list[str] = []
    try:
        for i in range(num_files):
            p = os.path.join(tmpdir, f"file_{i}.bin")
            with open(p, "wb") as f:
                f.write(os.urandom(size_kb * 1024))
            paths.append(p)
        for p in paths:
            with open(p, "rb") as f:
                _ = f.read()
    finally:
        for p in paths:
            os.remove(p)
        os.rmdir(tmpdir)


def matrix_multiply(size: int = 300) -> list[list[float]]:
    a = [[random.random() for _ in range(size)] for _ in range(size)]
    b = [[random.random() for _ in range(size)] for _ in range(size)]
    c = [[0.0] * size for _ in range(size)]
    for i in range(size):
        for j in range(size):
            s = 0.0
            for k in range(size):
                s += a[i][k] * b[k][j]
            c[i][j] = s
    return c


def fibonacci_recursive(n: int = 34) -> int:
    if n <= 1:
        return n
    return fibonacci_recursive(n - 1) + fibonacci_recursive(n - 2)


def string_processing(iterations: int = 50_000) -> str:
    s = ""
    for i in range(iterations):
        s += f"item-{i}-"
    parts = s.split("-")
    result = ",".join(parts)
    _ = result.upper()
    _ = result.lower()
    return result[:100]


TASKS = [
    ("cpu_heavy_math", cpu_heavy_math),
    ("prime_sieve", prime_sieve),
    ("sort_large_list", sort_large_list),
    ("hash_data", hash_data),
    ("json_serialization", json_serialization),
    ("regex_matching", regex_matching),
    ("file_io_work", file_io_work),
    ("matrix_multiply", matrix_multiply),
    ("fibonacci_recursive", fibonacci_recursive),
    ("string_processing", string_processing),
]


def _aggregate(results: dict[str, str]) -> None:
    for _ in range(2_000):
        blob = json.dumps(results)
        _ = json.loads(blob)
    total = 0.0
    for i in range(500_000):
        total += math.sin(i) * math.cos(i)


def main():
    print(f"launching {len(TASKS)} tasks ...")
    results: dict[str, str] = {}

    with profile() as p:
        with ThreadPoolExecutor(max_workers=len(TASKS)) as pool:
            futures = {pool.submit(fn): name for name, fn in TASKS}
            for future in as_completed(futures):
                name = futures[future]
                try:
                    ret = future.result()
                    results[name] = f"ok ({type(ret).__name__})"
                    print(f"  + {name}")
                except Exception as exc:
                    results[name] = f"FAILED: {exc}"
                    print(f"  x {name}: {exc}")

        print("aggregating on main thread ...")
        _aggregate(results)

    p.open()


if __name__ == "__main__":
    main()
