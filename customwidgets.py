import customtkinter as ctk
from PIL import Image
from Data import load_image
from typing import Union, Callable

# noinspection PyUnusedLocal
class ITButton(ctk.CTkFrame):
    def __init__(self, master, image_path, text, command=None, **kwargs):
        super().__init__(master, fg_color='#202020', corner_radius=6, **kwargs)

        self.command = command
        self.is_pressed = False

        self.image = load_image(image_path)

        # Outline frame for hover/press borders
        self.outline_frame = ctk.CTkFrame(self, fg_color='transparent', corner_radius=6)
        self.outline_frame.place(relx=0, rely=0, relwidth=1, relheight=1)

        # Image and text labels (vertically stacked)
        self.image_label = ctk.CTkLabel(self, image=self.image, text='', fg_color='transparent')
        self.text_label = ctk.CTkLabel(self, text=text, fg_color='transparent', text_color='white')

        # Layout
        self.image_label.grid(pady=(8, 2), padx=5)
        self.text_label.grid(pady=(0, 8), padx=5)

        # Event bindings
        self._bind_all_widgets('<Enter>', self._on_enter)
        self._bind_all_widgets('<Leave>', self._on_leave)
        self._bind_all_widgets('<Button-1>', self._on_press)
        self._bind_all_widgets('<ButtonRelease-1>', self._on_release)

    def _bind_all_widgets(self, event, handler):
        self.bind(event, handler)
        self.outline_frame.bind(event, handler)
        self.image_label.bind(event, handler)
        self.text_label.bind(event, handler)

    def _on_enter(self, event):
        if not self.is_pressed:
            self.outline_frame.configure(border_color='#fcd47c', border_width=2)

    def _on_leave(self, event):
        if not self.is_pressed:
            self.outline_frame.configure(border_width=0)

    def _on_press(self, event):
        self.is_pressed = True
        self.outline_frame.configure(border_color='#fbbd37', border_width=2)

    def _on_release(self, event):
        if self.is_pressed:
            self.is_pressed = False
            self.outline_frame.configure(border_color='#fcd47c', border_width=2)
            if self.command:
                self.command()

# noinspection PyUnusedLocal
class DefaultButton(ctk.CTkFrame):
    def __init__(self, master, text, command=None, width=120, height=32, **kwargs):
        super().__init__(master, fg_color="#202020", corner_radius=6, width=width, height=height, **kwargs)

        self.command = command
        self.is_pressed = False

        # Outer outline frame (for hover/press effect)
        self.outline_frame = ctk.CTkFrame(self, fg_color="transparent", corner_radius=6,
                                          height=height, width=width)
        self.outline_frame.grid(row=0, column=0, sticky="nsew")

        # Label inside outline
        self.text_label = ctk.CTkLabel(self.outline_frame, text=text, fg_color="transparent",
                                          height=height, width=width)
        self.text_label.grid(row=0, column=0, padx=10, pady=5, sticky="nsew")

        # Grid config for proper expansion
        self.outline_frame.grid_rowconfigure(0, weight=1)
        self.outline_frame.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Event binding (hover/click)
        self._bind_all_widgets("<Enter>", self._on_enter)
        self._bind_all_widgets("<Leave>", self._on_leave)
        self._bind_all_widgets("<Button-1>", self._on_press)
        self._bind_all_widgets("<ButtonRelease-1>", self._on_release)

    def _bind_all_widgets(self, event, handler):
        for widget in [self, self.outline_frame, self.text_label]:
            widget.bind(event, handler)

    def _on_enter(self, event):
        if not self.is_pressed:
            self.outline_frame.configure(border_color="#fcd47c", border_width=2)

    def _on_leave(self, event):
        if not self.is_pressed:
            self.outline_frame.configure(border_width=0)

    def _on_press(self, event):
        self.is_pressed = True
        self.outline_frame.configure(border_color="#fbbd37", border_width=2)

    def _on_release(self, event):
        if self.is_pressed:
            self.is_pressed = False
            self.outline_frame.configure(border_color="#fcd47c", border_width=2)
            if self.command:
                self.command()

# noinspection PyUnusedLocal
class BackButton(ctk.CTkFrame):
    def __init__(self, master, command=None, **kwargs):
        super().__init__(master, fg_color='#202020', corner_radius=6, width=100, height=32, **kwargs)

        self.command = command
        self.is_pressed = False

        pil_image = Image.open('Images/Back.png').convert('RGBA')
        self.image = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=(16, 13))

        self.outline_frame = ctk.CTkFrame(self, fg_color='transparent', bg_color='transparent',
                                          corner_radius=6, width=100, height=32)
        self.outline_frame.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.icon_label = ctk.CTkLabel(self, image=self.image, text='', fg_color='transparent', bg_color='transparent')
        self.icon_label.place(relx=0.5, rely=0.5, anchor="center")

        # Event binding
        self._bind_all('<Enter>', self._on_enter)
        self._bind_all('<Leave>', self._on_leave)
        self._bind_all('<Button-1>', self._on_press)
        self._bind_all('<ButtonRelease-1>', self._on_release)

    def _bind_all(self, event, handler):
        for w in [self, self.outline_frame, self.icon_label]:
            w.bind(event, handler)

    def _on_enter(self, event):
        if not self.is_pressed:
            self.outline_frame.configure(border_color='#fcd47c', border_width=2)

    def _on_leave(self, event):
        if not self.is_pressed:
            self.outline_frame.configure(border_width=0)

    def _on_press(self, event):
        self.is_pressed = True
        self.outline_frame.configure(border_color='#fbbd37', border_width=2)

    def _on_release(self, event):
        if self.is_pressed:
            self.is_pressed = False
            self.outline_frame.configure(border_color='#fcd47c', border_width=2)
            if self.command:
                self.command()

class Spinbox(ctk.CTkFrame):
    def __init__(self, parent, width=70, stepSize=1.0, minValue=0.0, maxValue=100.0,
                 decimals=2, command=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.stepSize = stepSize
        self.minVal = minValue
        self.maxVal = maxValue
        self.command = command
        self.decimals = decimals

        self.var = ctk.StringVar(value=f"{max(self.minVal, 1.0):.{self.decimals}f}")
        self.var.trace_add("write", self._onVar_write)

        vcmd = (self.register(self.Validate), '%P')
        self.entry = ctk.CTkEntry(self,
                                  textvariable=self.var,
                                  validate="key",
                                  validatecommand=vcmd,
                                  width=width)
        self.entry.grid(row=0, column=1, padx=2, pady=2, sticky="ew")

        # Overwrite-style keyboard input
        self.entry.bind("<Key>", self._on_key_press)

        self.btn_sub = ctk.CTkButton(self, text="−", width=30, command=self._subtract)
        self.btn_sub.grid(row=0, column=0, padx=2, pady=2)
        self.btn_add = ctk.CTkButton(self, text="+", width=30, command=self._increment)
        self.btn_add.grid(row=0, column=2, padx=2, pady=2)

        self.grid_columnconfigure(1, weight=1)

    @staticmethod
    def Validate(proposed: str) -> bool:
        if proposed in ("", "-", ".", "-."):
            return True
        try:
            float(proposed)
            return True
        except ValueError:
            return False

    def _onVar_write(self, *args):
        if self.command:
            try:
                val = float(self.var.get())
                self.command(val)
            except ValueError:
                pass

    def _on_key_press(self, event):
        widget = self.entry
        text = widget.get()
        idx = widget.index(ctk.INSERT)

        if event.keysym == "BackSpace":
            if idx == 0:
                return "break"
            # Replace the char before the cursor with "" (overwrite behavior)
            new_text = text[:idx - 1] + "" + text[idx:]
            self.var.set(new_text)
            widget.icursor(idx - 1)
            return "break"

        elif event.keysym == "Delete":
            if idx >= len(text):
                return "break"
            # Replace the char at the cursor with ""
            new_text = text[:idx] + "" + text[idx + 1:]
            self.var.set(new_text)
            widget.icursor(idx)
            return "break"

        elif len(event.char) == 0:
            return  # Ignore non-character keys like arrows, shift, etc.

        # Character input handling
        if not (event.char.isdigit() or event.char == "." or event.char == "-"):
            return "break"

        # Prevent more than one "." or "-" in the string
        if event.char == "." and "." in text:
            return "break"
        if event.char == "-" and "-" in text:
            return "break"

        # Overwrite logic
        if idx < len(text):
            new_text = text[:idx] + event.char + text[idx + 1:]
        else:
            new_text = text + event.char  # Append at the end

        if not self.Validate(new_text):
            return "break"

        self.var.set(new_text)
        widget.icursor(idx + 1)
        return "break"

    def _correctValue(self):
        # Optional: no longer called on focus out unless you re-enable that bind
        pass

    def _increment(self):
        try:
            num = float(self.var.get())
        except ValueError:
            num = self.minVal
        num = min(self.maxVal, num + self.stepSize)
        self.var.set(f"{num:.{self.decimals}f}")

    def _subtract(self):
        try:
            num = float(self.var.get())
        except ValueError:
            num = self.minVal
        num = max(self.minVal, num - self.stepSize)
        self.var.set(f"{num:.{self.decimals}f}")

    def get(self) -> float:
        try:
            return float(self.var.get())
        except ValueError:
            return self.minVal

    def set(self, value):
        num = max(self.minVal, min(self.maxVal, float(value)))
        self.var.set(f"{num:.{self.decimals}f}")

class MathLabel(ctk.CTkLabel):
    def __init__(self, parent,
                 sourceVar: ctk.Variable,
                 expr: Callable[[float], Union[float,str]],
                 fmt: str = "{:.2f}",
                 **kwargs):
        self.sourceVar = sourceVar
        self.expr = expr
        self.fmt = fmt
        self.compVar = ctk.StringVar()
        super().__init__(parent, textvariable=self.compVar, **kwargs)

        self.sourceVar.trace_add("write", self.recompute)
        self.recompute()

    def recompute(self, *args):
        try:
            if self.sourceVar.get() != '':
                x = float(self.sourceVar.get())
            else:
                x=0.0
            res = self.expr(x)
            if isinstance(res, (int, float)):
                self.compVar.set(self.fmt.format(res))
            else:
                self.compVar.set(str(res))
        except Exception as e:
            self.compVar.set("Err")
            print(e)
            
class CoolantToggle(ctk.CTkFrame):
    def __init__(self, master, coolantImage, radioVar, value, command=None, **kwargs):
        super().__init__(master, **kwargs)
        self.command = command
        self.coolantImage = coolantImage
        self.value = value
        self.radioVar = radioVar

        self.image = load_image(self.coolantImage)

        self.create_widgets()

    def create_widgets(self):
        imageLabel = ctk.CTkLabel(self, image=self.image, text='', fg_color='transparent')
        imageLabel.grid(row=0, column=0)

        radioBtn = ctk.CTkRadioButton(self, text='', variable=self.radioVar, value=self.value,
                                           command=self.command, width=32, height=32)
        radioBtn.grid(row=1, column=0)

    def select(self):
        self.radioVar.set(self.value)
