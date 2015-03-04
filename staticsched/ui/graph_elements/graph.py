from staticsched.ui.graph_elements.edge import GraphEdgeDrawController, DAGEdgeDrawController
from staticsched.ui.graph_elements.node import DAGNodeDrawController, GraphNodeDrawController

from staticsched.ui.notification_consts import *
from staticsched.ui.notifications import notify, subscribe

from staticsched.raw_graph import DAG, Graph, Node, Edge

FAKE_NODE_ID = "fake_node_id"


class GraphDrawController:
    def __init__(self, canvas, graph):
        self.graph = graph
        self.ns = graph.graph_id
        self.canvas = canvas
        self.selected = None
        self.nodes = {}
        self.edges = []
        self.connecting_started_with = None
        self._fake_edge = None
        self._fake_node = Node(FAKE_NODE_ID, 0, 0, -1)
        self.graph_id = graph.graph_id
        subscribe(CONNECT_START, self.on_connect_start, ns=self.ns)
        subscribe(CONNECT_END, self.on_connect_end, ns=self.ns)
        subscribe(CONNECT_CANCELED, self.on_connect_cancel, ns=self.ns)
        subscribe(FAKE_NODE_DRAG_EVENT, self.fake_node_drag, ns=self.ns)
        subscribe(NODE_DELETED, self.node_deleted, ns=self.ns)
        subscribe(EDGE_DELETED, self.edge_deleted, ns=self.ns)

    def on_connect_start(self, node_id):
        node = self.nodes[node_id].node

        self.connecting_started_with = node_id

        self._fake_node.x, self._fake_node.y = node.x, node.y
        edge = Edge(node, self._fake_node, -1)
        self._fake_edge = GraphEdgeDrawController(self.canvas, edge, target_offset=False, ns=self.ns)

    def on_connect_end(self, node):
        self.cancel_arrow_drag()
        if not self.connecting_started_with:
            return
        self.add_edge(self.connecting_started_with, node, 1)

    def cancel_arrow_drag(self):
        if self._fake_edge:
            self._fake_edge.delete()
            self._fake_edge = None

    def on_connect_cancel(self, msg):
        self.cancel_arrow_drag()

    def fake_node_drag(self, coords):
        self._fake_node.x, self._fake_node.y = coords
        notify(NODE_CHANGED.format(FAKE_NODE_ID), None, ns=self.ns)

    def create_node_controller(self, node):
        if isinstance(self.graph, Graph):
            return GraphNodeDrawController(self.canvas, node, ns=self.ns)
        elif isinstance(self.graph, DAG):
            return DAGNodeDrawController(self.canvas, node, ns=self.ns)
        else:
            raise NotImplemented()

    def create_edge_controller(self, edge):
        if isinstance(self.graph, Graph):
            return GraphEdgeDrawController(self.canvas, edge, ns=self.ns)
        elif isinstance(self.graph, DAG):
            return DAGEdgeDrawController(self.canvas, edge, ns=self.ns)
        else:
            raise NotImplemented()

    def add_node(self, x, y, weight=1, n_id=None):
        node = self.graph.add_node(x=x, y=y, weight=weight, n_id=n_id)
        self.nodes[node.n_id] = self.create_node_controller(node)
        return node

    def select_node(self, n_id):
        self.deselect()
        self.nodes[n_id].select()
        self.selected = self.nodes[n_id]

    def select_edge(self, selected_edge):
        self.deselect()
        edge = self.find_edge(selected_edge)
        edge.select()
        self.selected = edge

    def find_edge(self, selected_edge):
        for edge in self.edges:
            if edge.edge.source.n_id == selected_edge[0] and \
                            edge.edge.target.n_id == selected_edge[1]:
                return edge

    def deselect(self):
        if self.selected:
            self.selected.deselect()

    def add_edge(self, source, target, weight):
        edge = self.graph.add_edge(source, target, weight)
        self.edges.append(self.create_edge_controller(edge))

    def delete_current(self):
        if self.selected:
            self.selected.delete()

    def delete_all(self):
        for node in self.nodes.values():
            node.delete()

    def node_deleted(self, node_id):
        self.graph.delete_node(node_id)

    def edge_deleted(self, edge):
        self.graph.delete_edge(edge)

    def reset_marks(self):
        for node in self.nodes.values():
            node.reset_mark()

    def mark_nodes_red(self, node_list):
        for node_id in node_list:
            if node_id in self.nodes:
                self.nodes[node_id].mark()
