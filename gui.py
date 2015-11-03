import tkinter as tk
from PIL import Image
from PIL.ImageTk import PhotoImage
from main2 import Mediator


class Window:
    """The GUI that the user interacts with."""
    # There's really not a lot I can think to fix having to
    # do most things three times in a short, readable and
    # elegant way.

    def __init__(self):
        self.root = tk.Tk()

        # In order for tkinter to be threadsafe, it needs to be the main thread.
        # Therefor, we actually have to create the mediator object from within
        # the GUI rather than create the GUI from inside the mediator!
        self.med = Mediator(self)

        # The top half of the window has pictures, the bottom buttons.
        self.top_frm = tk.Frame()
        self.btm_frm = tk.Frame()

        # Load the top three images.
        pic1 = PhotoImage(Image.open("03.jpg"))
        pic2 = PhotoImage(Image.open("13.jpg"))
        pic3 = PhotoImage(Image.open("23.jpg"))
        self.pic1_lbl = tk.Label(self.top_frm, image=pic1)
        self.pic2_lbl = tk.Label(self.top_frm, image=pic2)
        self.pic3_lbl = tk.Label(self.top_frm, image=pic2)
        self.pic1_lbl.image = pic1  # Keep a copy around to avoid
        self.pic2_lbl.image = pic2  # these from getting garbage-
        self.pic3_lbl.image = pic3  # collected.
        self.pic1_lbl.pack(side=tk.LEFT)
        self.pic2_lbl.pack(side=tk.LEFT)
        self.pic3_lbl.pack(side=tk.LEFT)

        self.top_frm.pack()

        # Create a bunch of buttons at the bottom of the screen.
        hate = lambda: self.med.save(0)
        neut = lambda: self.med.save(1)
        love = lambda: self.med.save(2)
        fave = lambda: self.med.save(3)
        self.hate_btn = tk.Button(self.btm_frm, text="Hate",   anchor=tk.S, command=hate)
        self.neut_btn = tk.Button(self.btm_frm, text="Meh.",   anchor=tk.S, command=neut)
        self.love_btn = tk.Button(self.btm_frm, text="Love",   anchor=tk.S, command=love)
        self.fave_btn = tk.Button(self.btm_frm, text="WOWZA!", anchor=tk.S, command=fave)
        self.next_btn = tk.Button(self.btm_frm, text="Skip",   anchor=tk.S, command=self.med.next_)
        self.exit_btn = tk.Button(self.btm_frm, text="Exit",   anchor=tk.S, command=self.close)
        self.open_btn = tk.Button(self.btm_frm, text="Open",   anchor=tk.S, command=self.med.open_vid)
        for btn in [self.hate_btn, self.neut_btn,
                    self.love_btn, self.fave_btn,
                    self.exit_btn, self.open_btn,
                    self.next_btn]:
            btn.pack(side=tk.LEFT)

        self.btm_frm.pack()


    def update_images(self, pic1, pic2, pic3):
        self.pic1_lbl.configure(image=pic1)
        self.pic2_lbl.configure(image=pic2)
        self.pic3_lbl.configure(image=pic3)
        self.pic1_lbl.image = pic1
        self.pic2_lbl.image = pic2
        self.pic3_lbl.image = pic3

    def open_vid(self):
        pass

    def close(self):
        # Since there's a connection to a database,
        # we want to make sure that it gets closed.
        self.med.close_db()
        self.root.destroy()

    def __del__(self):
        # Since there's a connection to a database,
        # we want to make sure that it gets closed.
        self.med.close_db()
