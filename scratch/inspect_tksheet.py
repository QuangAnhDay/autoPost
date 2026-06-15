import tksheet
import inspect

print("Sheet init signature:", inspect.signature(tksheet.Sheet.__init__))
# Let's inspect Sheet's event bindings and what properties they pass.
# We can create a sheet and see what namedtuples are defined in tksheet module.
print("Namedtuples in tksheet:")
import collections
for name, obj in inspect.getmembers(tksheet):
    if isinstance(obj, type) and issubclass(obj, tuple) and hasattr(obj, "_fields"):
        print(f"  {name}: {obj._fields}")
