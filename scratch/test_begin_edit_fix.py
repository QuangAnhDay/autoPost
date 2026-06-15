import tkinter as tk
import tksheet

root = tk.Tk()
sheet = tksheet.Sheet(root)
sheet.pack()
sheet.set_sheet_data([["Initial", "✅"]])

# Event dict is passed to begin_edit_cell callback.
# Let's inspect what happens when we double-click a cell.
def begin_edit(event):
    print("begin_edit event:", event)
    # If column is 1 (the check column), return None to cancel
    if event.column == 1:
        return None
    # For other columns, return original value to edit
    val = sheet.get_cell_data(event.row, event.column)
    return "" if val is None else str(val)

sheet.extra_bindings("begin_edit_cell", begin_edit)

root.update()
print("Initialized successfully!")
