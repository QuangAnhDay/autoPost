import tkinter as tk
import tksheet

root = tk.Tk()
sheet = tksheet.Sheet(root)
sheet.pack()
sheet.set_sheet_data([["✅"]])

def double_click(event):
    print("Double click callback triggered via sheet.bind!")

# Bind double click
sheet.bind("<Double-Button-1>", double_click)

# Verify if extra_double_b1_func is set on main table
print("extra_double_b1_func set:", sheet.MT.extra_double_b1_func == double_click)
root.update()
