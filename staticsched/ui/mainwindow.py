import json
from tkinter import *
from tkinter import simpledialog, filedialog, ttk, messagebox
from staticsched.ui.graph_canvas import CanvasFrame

from staticsched.ui.notification_consts import *
from staticsched.ui.notifications import notify, subscribe
from staticsched.analyse import find_all_cycles, is_connected
from staticsched.raw_graph import DAG, Graph


def request_edge_weight(edge, ns):
    weight = simpledialog.askinteger("Weight", "Type new weight for edge")
    if weight:
        edge.weight = weight
        notify(EDGE_CHANGED.format(edge.source.n_id, edge.target.n_id), weight, ns=ns)


def request_node_weight(node, ns):
    weight = simpledialog.askinteger("Weight", "Type new weight for node")
    if weight:
        node.weight = weight
        notify(NODE_CHANGED.format(node.n_id), weight, ns=ns)


class UI:
    def __init__(self):
        self.task_dag = DAG()
        self.system_graph = Graph()

        self.root = Tk()

        self.build()
        subscribe(EDGE_WEIGHT_REQUEST, request_edge_weight, ns="ALL")
        subscribe(NODE_WEIGHT_REQUEST, request_node_weight, ns="ALL")

    def build(self):
        self.notebook = ttk.Notebook(self.root)

        self.dag_frame = CanvasFrame(self.task_dag, self.notebook)
        self.dag_frame.pack(expand=True)
        self.notebook.add(self.dag_frame, text="dag")

        self.system_frame = CanvasFrame(self.system_graph, self.notebook)
        self.system_frame.pack(expand=True)
        self.notebook.add(self.system_frame, text="system")

        self.notebook.pack(expand=True)

        self.configure_menu()

        self.root.bind_all("<KeyPress-Delete>", self.delete_pressed)

    def delete_pressed(self, event):
        if self.notebook.index("current") == 0:  # DAG
            self.dag_frame.delete(event)
        if self.notebook.index("current") == 1:  # System
            self.system_frame.delete(event)

    def configure_menu(self):
        self.menu = Menu(self.root)
        file_menu = Menu(self.menu)
        self.menu.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Save DAG...", command=self.save_dag)
        file_menu.add_command(label="Open DAG...", command=self.open_dag)
        file_menu.add_command(label="Save system graph...", command=self.save_sg)
        file_menu.add_command(label="Open system graph...", command=self.open_sg)
        file_menu.add_command(label="Reset", command=self.cleanup)

        dag_menu = Menu(self.menu)
        self.menu.add_cascade(label="DAG", menu=dag_menu)
        dag_menu.add_command(label="Check", command=self.dag_check)
        dag_menu.add_command(label="Reset marks", command=self.dag_reset_marks)

        dag_menu = Menu(self.menu)
        self.menu.add_cascade(label="System graph", menu=dag_menu)
        dag_menu.add_command(label="Check", command=self.system_check)
        dag_menu.add_command(label="Reset marks", command=self.system_reset_marks)
        self.root.config(menu=self.menu)

    def dag_check(self):
        self.dag_frame.reset_marks()
        cycle_found = False
        for cycle in find_all_cycles(self.task_dag):
            self.dag_frame.mark_nodes(cycle)
            cycle_found = True
        if cycle_found:
            messagebox.showerror("Cycle check", "CYCLE FOUND")
        else:
            messagebox.showinfo("Cycle check", "OK")

    def system_check(self):
        self.system_frame.reset_marks()
        if not is_connected(self.system_graph):
            self.system_frame.mark_nodes(self.system_graph.nodes.keys())
            messagebox.showerror("Connectivity check", "NOT CONNECTED")
        else:
            messagebox.showinfo("Connectivity check", "OK")

    def dag_reset_marks(self):
        self.dag_frame.reset_marks()

    def system_reset_marks(self):
        self.system_frame.reset_marks()

    def save_dag(self):
        saving_file = filedialog.asksaveasfile()
        if saving_file:
            serialized = json.dumps(self.task_dag.serialize())
            saving_file.write(serialized)
            saving_file.close()

    def open_dag(self):
        opened_file = filedialog.askopenfile()
        if opened_file:
            serialized = json.load(opened_file)
            opened_file.close()

            self.task_dag = DAG()
            self.dag_frame.load_new_graph(self.task_dag, serialized)

    def save_sg(self):
        saving_file = filedialog.asksaveasfile()
        if saving_file:
            serialized = json.dumps(self.system_graph.serialize())
            saving_file.write(serialized)
            saving_file.close()

    def open_sg(self):
        opened_file = filedialog.askopenfile()
        if opened_file:
            serialized = json.load(opened_file)
            opened_file.close()

            self.system_graph = Graph()
            self.system_frame.load_new_graph(self.system_graph, serialized)

    def cleanup(self):
        self.system_frame.cleanup()
        self.dag_frame.cleanup()

    def show(self):
        self.root.mainloop()
