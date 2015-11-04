import tkinter as tk
from PIL import Image
from PIL.ImageTk import PhotoImage
from main import Mediator

import time


class Window:
    """The GUI that the user interacts with."""
    def __init__(self):
        self.root = tk.Tk()

        # In order for tkinter to be threadsafe, it needs to be the main thread.
        # Therefor, we actually have to create the mediator object from within
        # the GUI rather than create the GUI from inside the mediator!
        self.med = Mediator(self)

        # The top half of the window has pictures, the bottom buttons.
        self.left_frm  = tk.Frame()
        self.right_frm = tk.Frame(width=100)

        # Load the top three images.
        pic1 = PhotoImage(Image.open("03.jpg"))
        pic2 = PhotoImage(Image.open("13.jpg"))
        pic3 = PhotoImage(Image.open("23.jpg"))

        self.pic1_lbl = tk.Label(self.left_frm, image=pic1)
        self.pic2_lbl = tk.Label(self.left_frm, image=pic2)
        self.pic3_lbl = tk.Label(self.left_frm, image=pic3)

        self.pic1_lbl.image = pic1  # Keep a copy around to avoid
        self.pic2_lbl.image = pic2  # these from getting garbage-
        self.pic3_lbl.image = pic3  # collected.

        self.pic1_lbl.grid(row=0, column=0)
        self.pic2_lbl.grid(row=0, column=1)
        self.pic3_lbl.grid(row=0, column=2)
        
        # We'll use a sliding scale for ratings.
        self.scale = tk.Scale(self.left_frm, from_=0, to=99, orient=tk.HORIZONTAL)
        self.scale.grid(row=1, column=0, columnspan=2, sticky=tk.W + tk.E)

        rate = lambda: self.med.save(self.scale.get())
        self.rate_btn = tk.Button(self.left_frm, text="Rate", anchor=tk.E, command=rate)
        self.rate_btn.grid(row=1, column=2)
        self.left_frm.pack(side=tk.LEFT)

        # Now for our buttons down the righ-hand side.
        self.next_btn  = tk.Button(self.right_frm, text="Skip",  anchor=tk.S, command=self.med.next_)
        self.exit_btn  = tk.Button(self.right_frm, text="Exit",  anchor=tk.S, command=self.med.close)
        self.open_btn  = tk.Button(self.right_frm, text="Open",  anchor=tk.S, command=self.med.open_vid)
        self.train_btn = tk.Button(self.right_frm, text="Train", anchor=tk.S, command=self.med.train)
        self.next_btn.grid(row=0)
        self.exit_btn.grid(row=1)
        self.open_btn.grid(row=2)
        self.train_btn.grid(row=3)

        self.right_frm.pack(side=tk.RIGHT)

        # Grab the next video immediately after creating the window.
        self.med.next_()

    def update_images(self, pic1, pic2, pic3):
        self.pic1_lbl.configure(image=pic1)
        self.pic2_lbl.configure(image=pic2)
        self.pic3_lbl.configure(image=pic3)
        self.pic1_lbl.image = pic1
        self.pic2_lbl.image = pic2
        self.pic3_lbl.image = pic3

    def __del__(self):
        self.med.close()
