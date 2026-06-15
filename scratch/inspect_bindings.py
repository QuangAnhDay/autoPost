import tkinter as tk
import tksheet
import pprint

root = tk.Tk()
sheet = tksheet.Sheet(root)
globals_dict = sheet.extra_bindings.__globals__
if "BINDING_TO_ATTR" in globals_dict:
    print("BINDING_TO_ATTR keys:")
    pprint.pprint(list(globals_dict["BINDING_TO_ATTR"].keys()))
else:
    print("BINDING_TO_ATTR not in globals")
