path = r"D:\myProject\autoPost\autoPost\autoPost\.venv\Lib\site-packages\tksheet\main_table.py"
with open(path, "r", encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()
    
start = 7370 - 1
end = min(len(lines), 7390)
for idx in range(start, end):
    print(f"{idx+1}: {lines[idx]}", end="")
