import json
from tkinter import *
from tkinter import simpledialog, filedialog, ttk, messagebox
from staticsched.graph_analytics.cpu_priorities import CohesionCPUPrioritizationPolicy
from staticsched.graph_analytics.gantt import System
from staticsched.graph_analytics.router import DFSRouter
from staticsched.graph_analytics.scheduler.schedulers import Scheduler
from staticsched.ui.gantt_ui import draw_gantt_diagram

from staticsched.ui.widgets.graph_canvas import CanvasFrame
from staticsched.ui.windows.graph_params_window import GraphParamsWindow
from staticsched.ui.notification_consts import *
from staticsched.ui.notifications import notify, subscribe
from staticsched.graph_analytics.analyse import find_all_cycles, is_connected, find_critical_path, \
    find_all_critical_paths
from staticsched.graph_analytics.task_queues import QueueGenerationPolicy3, QueueGenerationPolicy4, QueueGenerationPolicy16
from staticsched.graph_analytics.raw_graph import DAG, Graph
from staticsched.ui.table_window import TableWindow


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
        subscribe(GRAPH_GENERATED, self.update_dag, ns="DAG_GENERATOR")

        self.open_dag(open("saved/dag1"))
        self.open_sg(open("saved/3line"))
        self.schedule()

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
        file_menu.add_command(label="Open DAG...", command=self.open_dag_dialog)
        file_menu.add_command(label="Save system graph...", command=self.save_sg)
        file_menu.add_command(label="Open system graph...", command=self.open_sg_dialog)
        file_menu.add_command(label="Reset", command=self.cleanup)

        dag_menu = Menu(self.menu)
        self.menu.add_cascade(label="DAG", menu=dag_menu)
        dag_menu.add_command(label="Generate random graph", command=self.generate_graph)
        dag_menu.add_command(label="Enumerate", command=self.dag_re_enumerate)
        dag_menu.add_separator()
        dag_menu.add_command(label="Check", command=self.dag_check)
        dag_menu.add_command(label="Reset marks", command=self.dag_reset_marks)
        dag_menu.add_command(label="Find critical path", command=self.find_critical_path)
        dag_menu.add_command(label="Generate queue (method #3)", command=self.queue_3)
        dag_menu.add_command(label="Generate queue (method #4)", command=self.queue_4)
        dag_menu.add_command(label="Generate queue (method #16)", command=self.queue_16)

        graph_menu = Menu(self.menu)
        self.menu.add_cascade(label="System graph", menu=graph_menu)
        graph_menu.add_command(label="Enumerate", command=self.system_graph_re_enumerate)
        graph_menu.add_command(label="Check", command=self.system_check)
        graph_menu.add_command(label="Reset marks", command=self.system_reset_marks)

        schedule_menu = Menu(self.menu)
        self.menu.add_cascade(label="Scheduler", menu=schedule_menu)
        schedule_menu.add_command(label="Schedule", command=self.schedule)

        self.root.config(menu=self.menu)

    def dag_check(self):
        self.dag_frame.reset_marks()
        cycle_found = False
        for cycle in find_all_cycles(self.task_dag):
            self.dag_frame.mark_nodes(cycle, color="red")
            cycle_found = True
        if cycle_found:
            messagebox.showerror("Cycle check", "CYCLE FOUND")
        else:
            messagebox.showinfo("Cycle check", "OK")

    def system_check(self):
        self.system_frame.reset_marks()
        if not is_connected(self.system_graph):
            self.system_frame.mark_nodes(self.system_graph.nodes.keys(), color="red")
            messagebox.showerror("Connectivity check", "NOT CONNECTED")
        else:
            messagebox.showinfo("Connectivity check", "OK")

    def dag_reset_marks(self):
        self.dag_frame.reset_marks()

    def system_reset_marks(self):
        self.system_frame.reset_marks()

    def find_critical_path(self):
        length, path = find_critical_path(self.task_dag)
        self.dag_frame.mark_nodes(path, color="green")
        TableWindow(self.root, ["node"], [[node] for node in path], "Critical path")

    def queue_3(self):
        paths = find_all_critical_paths(self.task_dag, forward=True, weight_based=True)
        queue = QueueGenerationPolicy3().get_queue(self.task_dag)
        print(queue)
        TableWindow(self.root, ["node", "Tcrit<down>", "Critical path"],
                    [[node, paths[node][0], paths[node][1]] for node in queue],
                    "Queue #3")

    def queue_4(self):
        paths = find_all_critical_paths(self.task_dag, forward=True, weight_based=False)
        queue = QueueGenerationPolicy4().get_queue(self.task_dag)

        def get_connectivity(node_id):
            return len(self.task_dag.get_neighbours(self.task_dag.nodes[node_id], forward=True) + self.task_dag.get_neighbours(self.task_dag.nodes[node_id], forward=False))
        TableWindow(self.root, ["node", "Ncrit<down>", "Connectivity", "Critical path"],
                    [[node, paths[node][0], get_connectivity(node), paths[node][1]] for node in queue],
                    "Queue #4")

    def queue_16(self):
        paths = find_all_critical_paths(self.task_dag, forward=False, weight_based=True)
        queue = QueueGenerationPolicy16().get_queue(self.task_dag)
        TableWindow(self.root, ["node", "Tcrit<up>", "Critical path"],
                    [[node, paths[node][0], paths[node][1]] for node in queue],
                    "Queue #16")

    def schedule(self):
        system = System(self.system_graph, duplex=True, has_io_cpu=True)
        router = DFSRouter(self.system_graph)

        scheduler = Scheduler(self.task_dag, self.system_graph,
                              QueueGenerationPolicy3(),
                              CohesionCPUPrioritizationPolicy(),
                              system,
                              router)
        scheduler.schedule_dag()
        draw_gantt_diagram(system)

    def generate_graph(self):
        GraphParamsWindow(self.root)

    def dag_re_enumerate(self):
        self.task_dag.re_enumerate()
        self.update_dag(self.task_dag.serialize())

    def system_graph_re_enumerate(self):
        self.system_graph.re_enumerate()
        self.update_system_graph(self.system_graph.serialize())

    def save_dag(self):
        saving_file = filedialog.asksaveasfile()
        if saving_file:
            serialized = json.dumps(self.task_dag.serialize())
            saving_file.write(serialized)
            saving_file.close()

    def open_dag_dialog(self):
        opened_file = filedialog.askopenfile()
        self.open_dag(opened_file)

    def open_dag(self, opened_file):
        if opened_file:
            serialized = json.load(opened_file)
            opened_file.close()

            self.task_dag = DAG()
            self.dag_frame.load_new_graph(self.task_dag, serialized)

    def update_dag(self, serialized):
        self.task_dag = DAG()
        self.dag_frame.load_new_graph(self.task_dag, serialized)

    def update_system_graph(self, serialized):
        self.system_graph = Graph()
        self.system_frame.load_new_graph(self.system_graph, serialized)

    def save_sg(self):
        saving_file = filedialog.asksaveasfile()
        if saving_file:
            serialized = json.dumps(self.system_graph.serialize())
            saving_file.write(serialized)
            saving_file.close()

    def open_sg_dialog(self):
        opened_file = filedialog.askopenfile()
        self.open_sg(opened_file)

    def open_sg(self, opened_file):
        if opened_file:
            serialized = json.load(opened_file)
            opened_file.close()

            self.system_graph = Graph()
            self.system_frame.load_new_graph(self.system_graph, serialized)

    def cleanup(self):
        self.system_frame.cleanup()
        self.dag_frame.cleanup()

    def show(self):
        self.root.wm_title("Static Scheduler")
        self.root.mainloop()
