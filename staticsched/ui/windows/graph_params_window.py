from tkinter import *
from tkinter import simpledialog
from tkinter.ttk import *
import warnings
from staticsched.graph_analytics.raw_graph import DAG
from staticsched.ui.notification_consts import GRAPH_GENERATED
from staticsched.ui.notifications import notify


def make_entry(parent, caption, var, **options):
    Label(parent, text=caption).pack(side=TOP)
    entry = Entry(parent, textvariable=var, **options)
    entry.pack(side=TOP)
    return entry


class GraphParamsWindow:
    def __init__(self, root):
        self.min_weight = IntVar(value="5")
        self.max_weight = IntVar(value="20")
        self.count = IntVar(value="10")
        self.connectivity = DoubleVar(value="0.5")
        self.connections_percent = IntVar(value="20")
        self.min_edge_weight = IntVar(value="1")
        self.max_edge_weight = IntVar(value="50")

        self.root = Toplevel(root)
        self.root.wm_title("DAG generation params")
        self.build()

    def build(self):
        self.frame = Frame(self.root)
        self.frame.pack(fill='both', expand=True)

        make_entry(self.frame, "min_weight", self.min_weight)
        make_entry(self.frame, "max_weight", self.max_weight)
        make_entry(self.frame, "count", self.count)
        make_entry(self.frame, "connectivity", self.connectivity)
        make_entry(self.frame, "connections_percent", self.connections_percent)
        make_entry(self.frame, "min_edge_weight", self.min_edge_weight)
        make_entry(self.frame, "max_edge_weight", self.max_edge_weight)

        button = Button(self.frame, text='okay', command=self.do_generate)
        button.pack(side='right')

    def do_generate(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            graph = DAG.generate(self.min_weight.get(), self.max_weight.get(), self.count.get(),
                                 self.connectivity.get(), self.connections_percent.get(),
                                 self.min_edge_weight.get(), self.max_edge_weight.get())
            if w:
                simpledialog.messagebox.showwarning("Warning", "\n".join(str(warn.message) for warn in w))
        serialized = graph.serialize()
        notify(GRAPH_GENERATED, serialized, ns="DAG_GENERATOR")
