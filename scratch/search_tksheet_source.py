import os

venv_path = r"D:\myProject\autoPost\autoPost\autoPost\.venv\Lib\site-packages\tksheet"
matches = []
for root, dirs, files in os.walk(venv_path):
    for f in files:
        if f.endswith(".py"):
            path = os.path.join(root, f)
            with open(path, "r", encoding="utf-8", errors="ignore") as file:
                for idx, line in enumerate(file, 1):
                    if "begin_edit_cell" in line:
                        matches.append((f, idx, line.strip()))

for m in matches:
    print(f"{m[0]}:{m[1]}: {m[2]}")
