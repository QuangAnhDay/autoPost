path = r"D:\myProject\autoPost\autoPost\autoPost\.venv\Lib\site-packages\tksheet\main_table.py"
with open(path, "r", encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()
    
# Print around line 7439 (1-indexed, so 7438 index in list)
start = max(0, 7420 - 1)
end = min(len(lines), 7460)
for idx in range(start, end):
    print(f"{idx+1}: {lines[idx]}", end="")
