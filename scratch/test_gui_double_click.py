import sys
sys.path.append(r"d:\myProject\autoPost\autoPost\autoPost")

import tkinter as tk
from gui import AutoPostGUI

# We need a Tk root to instantiate the GUI
root = tk.Tk()
app = AutoPostGUI()
# Mock editor window opening
app._mo_giao_dien_quan_ly()

# Let's inspect the sheet data
print("Initial sheet data:")
for r in range(app.sheet.get_total_rows()):
    print(f"Row {r}: {app.sheet.get_cell_data(r, 5)}")

# Let's simulate a double click on row 3 (0-indexed, which corresponds to row 4 in posts.json, value is '✅')
class MockEvent:
    def __init__(self, row, column):
        self.row = row
        self.column = column

print("\n--- Simulating double click on Row 3, Col 5 (currently ✅) ---")
event = MockEvent(3, 5)

# 1. Run begin_edit_cell (returns False in gui.py)
allowed = app._begin_edit_cell(event)
print("begin_edit_cell returned:", allowed)

# 2. Run double_click_sheet
app._double_click_sheet(event)
print("After _double_click_sheet directly, cell data:", app.sheet.get_cell_data(3, 5))

# Let's check if there is any other event or binding.
# In tksheet, what happens if we let the tkinter event loop run?
# We can call root.update() to process any pending events
root.update()
print("After root.update(), cell data:", app.sheet.get_cell_data(3, 5))

# Let's simulate double click on Row 0 (currently False)
print("\n--- Simulating double click on Row 0, Col 5 (currently False) ---")
event_0 = MockEvent(0, 5)
app._double_click_sheet(event_0)
print("After _double_click_sheet on Row 0, cell data:", app.sheet.get_cell_data(0, 5))
root.update()
print("After root.update() on Row 0, cell data:", app.sheet.get_cell_data(0, 5))
