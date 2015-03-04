from tkinter import *
from staticsched.raw_graph import Graph

from staticsched.ui.notification_consts import *
from staticsched.ui.graph_elements.graph import GraphDrawController
from staticsched.ui.notifications import notify, unsubscribe_all


class GraphCanvas(Canvas):
    def __init__(self, root, graph):
        super().__init__(root, width=800, height=600, bg='white')
        self.graph = GraphDrawController(self, graph)
        self.root = root
        self.build()
        self.id = 0
        self.ns = self.graph.graph_id

    def build(self):
        self.bind("<Double-Button-1>", self.add_node)
        self.bind("<Button-1>", self.select)
        self.bind("<ButtonRelease-3>", self.end_connecting)
        self.pack(in_=self.root, expand=YES, fill=BOTH)

    def delete_pressed(self, event):
        self.graph.delete_current()

    def end_connecting(self, event):
        selected = self.find_node_by_coords(event.x, event.y)
        if selected:
            notify(CONNECT_END, selected, ns=self.ns)
        else:
            notify(CONNECT_CANCELED, None, ns=self.ns)

    def add_node(self, event):
        node = self.graph.add_node(event.x, event.y)
        self.graph.select_node(node.n_id)

    def is_selected(self, object_id):
        return "current" in self.gettags(object_id)

    def is_node_selected(self, q):
        return "node" in self.gettags(q)

    def is_edge_selected(self, q):
        return "edge" in self.gettags(q)

    def find_item_in_tag(self, tags):
        return filter(None, re.findall(r"item_[^_]*", tags[0]))

    def find_edge_in_tag(self, tags):
        return filter(None, re.findall(r"line[^_]*_[^_]*", tags[0]))

    def find_node_by_coords(self, x, y):
        q = self.find_closest(x, y)
        tags = self.gettags(q)
        if self.is_selected(q) and self.is_node_selected(q):
            selected_node = list(self.find_item_in_tag(tags))[0].replace("item_", "")
            return selected_node
        return None

    def find_edge_by_coords(self, x, y):
        q = self.find_closest(x, y)
        tags = self.gettags(q)
        if self.is_selected(q) and self.is_edge_selected(q):
            selected_edge = list(self.find_edge_in_tag(tags))[0].replace("line", "").split("_")
            return selected_edge
        return None

    def select(self, event):
        selected_node = self.find_node_by_coords(event.x, event.y)
        selected_edge = self.find_edge_by_coords(event.x, event.y)
        if selected_node:
            self.graph.select_node(selected_node)
        elif selected_edge:
            self.graph.select_edge(selected_edge)
        else:
            self.graph.deselect()

    def cleanup(self):
        self.graph.delete_all()
        unsubscribe_all(self.graph, ns=self.ns)

    def load_new_graph(self, task_dag, serialized):
        self.cleanup()
        self.graph = GraphDrawController(self, task_dag)
        self.ns = self.graph.graph_id
        Graph.deserialize(self.graph, serialized)

    def reset_marks(self):
        self.graph.reset_marks()

    def mark_nodes_red(self, node_list):
        self.graph.mark_nodes_red(node_list)


class CanvasFrame(Frame):
    def __init__(self, graph, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.canvas = GraphCanvas(self, graph)

    def load_new_graph(self, graph, serialized):
        self.canvas.load_new_graph(graph, serialized)

    def cleanup(self):
        self.canvas.cleanup()

    def delete(self, event):
        self.canvas.delete_pressed(event)

    def reset_marks(self):
        self.canvas.reset_marks()

    def mark_nodes(self, node_list):
        self.canvas.mark_nodes_red(node_list)
