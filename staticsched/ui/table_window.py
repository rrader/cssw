from tkinter import *
from tkinter.ttk import *


class TableWindow:
    def __init__(self, root, headers, data, title=""):
        self.root = Toplevel(root)
        self.root.wm_title(title)
        self.headers = headers
        self.data = data
        self.build()

    def build(self):
        self.frame = Frame(self.root)
        self.frame.pack(fill='both', expand=True)

        self.tree = Treeview(self.root, columns=self.headers, show="headings")
        vsb = Scrollbar(self.root, orient="vertical", command=self.tree.yview)
        hsb = Scrollbar(self.root, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.grid(column=0, row=0, sticky='nsew', in_=self.frame)
        vsb.grid(column=1, row=0, sticky='ns', in_=self.frame)
        hsb.grid(column=0, row=1, sticky='ew', in_=self.frame)
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_rowconfigure(0, weight=1)

        for column in self.headers:
            self.tree.heading(column, text=column.title())
            self.tree.heading(column, text=column.title())

        for row in self.data:
            self.tree.insert('', 'end', values=row)
