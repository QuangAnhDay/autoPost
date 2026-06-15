path = r"D:\myProject\autoPost\autoPost\autoPost\.venv\Lib\site-packages\tksheet\sheet.py"
with open(path, "r", encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()
    
start = 670 - 1
end = min(len(lines), 700)
for idx in range(start, end):
    print(f"{idx+1}: {lines[idx]}", end="")
