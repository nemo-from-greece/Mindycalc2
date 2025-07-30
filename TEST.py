from Mindycalc.Data import *
from customwidgets import *
import Logic

# root = ctk.CTk()
#
# def radiobutton_event():
#     print("radiobutton toggled, current value:", radio_var.get())
#
# radio_var = ctk.IntVar(value=0)
#
# spinbox = Spinbox(root)
# option0 = CoolantToggle(root, 'Images/No_coolant.png', radio_var, 0, radiobutton_event)
# option1 = CoolantToggle(root, 'Images/Items/Water.png', radio_var, 1, radiobutton_event)
# option2 = CoolantToggle(root, 'Images/Items/Cryofluid.png', radio_var, 2, radiobutton_event)
# ctk.CTkLabel(root, text='Rate').grid(row=2, column=0)
# math = MathLabel(root, spinbox.var, lambda x: x * (1 + radio_var.get()))
#
# def update_math_label(*args):
#     math.recompute()  # Force recompute
#
# radio_var.trace_add("write", update_math_label)
#
# spinbox.grid(row=0, column=0, columnspan=3, padx=10, pady=10)
# option0.grid(row=1, column=0, padx=10, pady=10)
# option1.grid(row=1, column=1, padx=10, pady=10)
# option2.grid(row=1, column=2, padx=10, pady=10)
# math.grid(row=2, column=1, columnspan=2)
#
# spinbox.set(1)
# option0.select()
#
# print(Logic.find_producers_resource(find_resource('Titanium'), 'SERPULO'))
#
# root.mainloop()

path, factories = Logic.find_upgrade_path(find_unit('Omura'))
Logic.calculate_process_inputs(path, factories, 1)