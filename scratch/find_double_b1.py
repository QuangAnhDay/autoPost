path = r"D:\myProject\autoPost\autoPost\autoPost\.venv\Lib\site-packages\tksheet\main_table.py"
with open(path, "r", encoding="utf-8", errors="ignore") as f:
    for idx, line in enumerate(f, 1):
        if "def double_b1" in line:
            print(f"{idx}: {line.strip()}")
