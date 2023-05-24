import tkinter as tk
import customtkinter as ctk
import numpy as np
from PIL import Image, ImageTk


class CompareStacks:
    def __init__(self) -> None:
        ctk.set_appearance_mode('dark')
        self.root = ctk.CTk()
        # self.root.geometry('1200x1200')

    def __call__(self, stack_left, stack_right):
        self.draw_stack(stack_left, side=ctk.LEFT)
        self.draw_stack(stack_right, side=ctk.RIGHT)
        self.root.mainloop()

    def draw_stack(self, stack, side):
        slices, height, width = stack.shape
        images = []
        for slice in range(slices):
            images.append(ImageTk.PhotoImage(Image.fromarray(stack[slice, :, :])))
        frame = ctk.CTkFrame(master=self.root, width=width, height=height)
        frame.pack(side=side, padx=20, pady=20)
        canvas = ctk.CTkCanvas(frame, width=width, height=height)
        canvas.pack()
        slider = tk.Scale(
            frame,
            orient=ctk.HORIZONTAL,
            from_=0,
            to=slices - 1,
            length=width,
            command=lambda i: canvas.create_image(0, 0, image=images[int(i)], anchor=tk.NW),
            repeatdelay=1,
            resolution=1,
        )
        slider.pack(side=ctk.BOTTOM)
