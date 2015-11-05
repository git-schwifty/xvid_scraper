import tkinter as tk
from PIL import Image
from PIL.ImageTk import PhotoImage
from main import Mediator

import time


class Window:
    """The GUI that the user interacts with."""
    def __init__(self):
        # In order for tkinter to be threadsafe, it needs to be the main thread.
        # Therefor, we actually have to create the mediator object from within
        # the GUI rather than create the GUI from inside the mediator!
        self.med = Mediator(self)

        self.root = tk.Tk()
        
        # Add a menubar.
        self.root_menu = tk.Menu(self.root)

        self.file_menu = tk.Menu(self.root_menu, tearoff=0)
        self.file_menu.add_command(label="Exit",        command=self.med.close)
        self.file_menu.add_command(label="Train",       command=self.med.train)
        self.file_menu.add_command(label="Clear Queue", command=self.med.clear_queue)
        self.root_menu.add_cascade(label="File", menu=self.file_menu)

        self.fetishes_menu = tk.Menu(self.root_menu, tearoff=0)
        for fetish in ["amateur",      "anal",  "asian",    "ebony",
                       "blowjob",      "gay",   "hardcore", "tits",
                       "interracial", "latina", "lesbian",  "milf",
                       "shemale",      "teen",  "new",      "best"]:
            self.fetishes_menu.add_radiobutton(label=str(fetish), command=lambda: self.med.set_fetish(fetish))
        self.root_menu.add_cascade(label="Fetishes", menu=self.fetishes_menu)

        self.root.config(menu=self.root_menu)

        # The top half of the window has pictures, the bottom buttons.
        self.left_frm  = tk.Frame()
        self.right_frm = tk.Frame()

        # LEFT FRAME
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
        self.scale = tk.Scale(self.left_frm,
                              from_=0, to=99,
                              orient=tk.HORIZONTAL,
                              repeatdelay=1,
                              repeatinterval=1)

        self.scale.grid(row=1, column=0, columnspan=2, sticky=tk.W + tk.E)
        self.scale.set(50)
        
        # Add the rate button just to the left of the scale.
        rate = lambda: self.med.save(self.scale.get())
        self.rate_btn = tk.Button(self.left_frm, text="Rate", anchor=tk.E, command=rate)
        self.rate_btn.grid(row=1, column=2)
        self.left_frm.pack(side=tk.LEFT)

        # RIGHT FRAME
        # Now for our buttons down the righ-hand side.
        self.next_btn  = tk.Button(self.right_frm, text="Skip",  anchor=tk.S, command=self.med.next_)
        self.open_btn  = tk.Button(self.right_frm, text="Open",  anchor=tk.S, command=self.med.open_vid)
        self.next_btn.grid(row=0, column=0)
        self.open_btn.grid(row=0, column=1)
        self.feedback_box = tk.Message(self.right_frm, text="creating window...", width=250)
        self.feedback_box.grid(row=2, rowspan=3, columnspan=3)

        self.right_frm.pack(side=tk.LEFT)

        # Some keybindings.
        self.root.bind("a", lambda event: self.med.save(0))
        self.root.bind("s", lambda event: self.med.save(1))
        self.root.bind("d", lambda event: self.med.save(2))
        self.root.bind("f", lambda event: self.med.save(3))
        self.root.bind("g", lambda event: self.med.save(4))
        self.root.bind("h", lambda event: self.med.save(5))
        self.root.bind("j", lambda event: self.med.save(6))
        self.root.bind("k", lambda event: self.med.save(7))
        self.root.bind("l", lambda event: self.med.save(8))
        self.root.bind(";", lambda event: self.med.save(9))
        self.root.bind("<space>",  lambda event: self.med.next_())
        self.root.bind("<Return>", lambda event: rate())
        self.root.bind("t",        lambda event: self.med.train())
        self.root.bind("o",        lambda event: self.med.open_vid())
        self.root.bind("x",        lambda event: self.med.close())

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
