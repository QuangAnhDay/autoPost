import tkinter as tk
import tksheet

root = tk.Tk()
sheet = tksheet.Sheet(root)
sheet.pack()
sheet.set_sheet_data([["✅"]])

def begin_edit(event):
    print("begin_edit_cell event fired!")
    return False

def double_click(event):
    print("double_click_left_click event fired!")
    val = sheet.get_cell_data(0, 0)
    current = "" if val is None else str(val).strip()
    new_val = "" if current in ("✅", "None", "nan") else "✅"
    print(f"double_click setting cell from '{val}' to '{new_val}'")
    sheet.set_cell_data(0, 0, new_val)

sheet.extra_bindings("begin_edit_cell", begin_edit)
sheet.extra_bindings("double_click_left_click", double_click)

root.update()

class DummyEvent:
    def __init__(self, x, y):
        self.x = x
        self.y = y

# Call double click handler
event = DummyEvent(50, 15)
sheet.MT.double_b1(event)

root.update()
print("Final cell data in sheet:", repr(sheet.get_cell_data(0, 0)))
