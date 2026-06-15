import tkinter as tk
import tksheet

root = tk.Tk()
sheet = tksheet.Sheet(root)
sheet.pack()
sheet.set_sheet_data([["✅"]])

def begin_edit(event):
    print("begin_edit, current val:", sheet.get_cell_data(0, 0))
    return False

def double_click(event):
    print("double_click start, current val:", sheet.get_cell_data(0, 0))
    sheet.set_cell_data(0, 0, "")
    print("double_click end, current val:", sheet.get_cell_data(0, 0))

sheet.extra_bindings("begin_edit_cell", begin_edit)
sheet.extra_bindings("double_click_left_click", double_click)

# Let's simulate double click event
class DummyEvent:
    def __init__(self):
        self.row = 0
        self.column = 0

print("Initial cell data:", sheet.get_cell_data(0, 0))
# Simulating what tksheet does internally or we can just see if we can run it.
# Actually, let's just run it with root.update() to process events.
# But since we can't interactively double click, we can see if tksheet has a checkbox toggle.
print("tksheet dir:", [x for x in dir(sheet) if "checkbox" in x.lower()])
