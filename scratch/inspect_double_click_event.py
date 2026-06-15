import tkinter as tk
import tksheet

root = tk.Tk()
sheet = tksheet.Sheet(root)
sheet.pack()
sheet.set_sheet_data([["✅"]])

class ClickEvent:
    def __init__(self):
        self.x = 50
        self.y = 15
        self.widget = sheet.MT

def double_click(event):
    print("Event type:", type(event))
    
    # Use sheet.MT.identify_row/col
    row = sheet.MT.identify_row(y=event.y)
    col = sheet.MT.identify_col(x=event.x)
    print(f"Identified from coordinates: row={row}, col={col}")
    
    selected = sheet.get_currently_selected()
    print("Selected representation:", repr(selected))
    if selected:
        print("Selected type:", type(selected))
        # Check attributes of selected
        if hasattr(selected, "row"):
            print("selected.row:", selected.row)
        else:
            print("selected does not have .row")

sheet.select_cell(0, 0)
double_click(ClickEvent())
root.update()
