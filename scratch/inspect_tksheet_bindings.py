import tksheet
import inspect

# Print the source code of extra_bindings or see how events are called
try:
    print(inspect.getsource(tksheet.Sheet.extra_bindings))
except Exception as e:
    print(e)
