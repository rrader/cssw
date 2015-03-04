from staticsched.ui.graph_elements import length
from staticsched.ui.graph_elements.node import NODE_RADIUS
from staticsched.ui.notification_consts import *
from staticsched.ui.notifications import subscribe, notify, unsubscribe_all

SMALL_OFFSET = 2


class EdgeDrawController:
    def __init__(self, canvas, edge, ns, target_offset=True):
        self.ns = ns
        self.target_offset = target_offset
        self.edge = edge
        self.canvas = canvas
        self._line = None
        self._weight = None
        self.create_edge()
        subscribe(NODE_CHANGED.format(self.edge.source.n_id), self.update_edge, ns=self.ns)
        subscribe(NODE_CHANGED.format(self.edge.target.n_id), self.update_edge, ns=self.ns)
        subscribe(EDGE_CHANGED.format(self.edge.source.n_id, self.edge.target.n_id), self.update_edge, ns=self.ns)
        subscribe(DELETE_NODE.format(self.edge.source.n_id), self.on_node_delete, ns=self.ns)
        subscribe(DELETE_NODE.format(self.edge.target.n_id), self.on_node_delete, ns=self.ns)

    def get_tag(self):
        return "line{}_{}".format(self.edge.source.n_id, self.edge.target.n_id)

    def on_node_delete(self, event):
        self.delete()

    def get_coords(self):
        s = self.edge.source.x, self.edge.source.y
        e = self.edge.target.x, self.edge.target.y
        if length(s, e) > 0:
            dx = ((e[0] - s[0]) * NODE_RADIUS) / length(s, e)
            dy = ((e[1] - s[1]) * NODE_RADIUS) / length(s, e)
        else:
            dx, dy = 0, 0
        start_point = s[0] + dx, s[1] + dy
        if self.target_offset:
            end_point = (e[0] - dx, e[1] - dy)
        else:
            offset = SMALL_OFFSET if dx > 0 else -SMALL_OFFSET
            end_point = (e[0] - offset, e[1] - offset)
        # middle_points = self.get_bezier_points(start_point, end_point)
        coords = start_point + end_point
        return coords

    def mid_coords(self):
        coords = self.get_coords()
        return coords[0] + (coords[2] - coords[0])/2 + 20, coords[1] + (coords[3] - coords[1])/2 + 20

    def create_line(self, coords):
        raise NotImplemented()

    def create_edge(self):
        tag = self.get_tag()
        coords = self.get_coords()
        self._line = self.create_line(coords)
        self._weight = self.canvas.create_text(*self.mid_coords(),
                                               text=str(self.edge.weight),
                                               activefill='blue',
                                               tags=(tag, tag+"_w", "edge"))
        self.canvas.tag_bind(tag + "_w", "<ButtonPress-1>", self.on_click)

    def on_click(self, event):
        notify(EDGE_WEIGHT_REQUEST, self.edge, ns=self.ns)

    def update_edge(self, msg):
        self.canvas.coords(self._line, *self.get_coords())
        self.canvas.coords(self._weight, *self.mid_coords())
        self.canvas.itemconfig(self._weight, text=str(self.edge.weight) if self.edge.weight >= 0 else "")

    def delete(self):
        self.canvas.delete(self._line)
        self.canvas.delete(self._weight)
        notify(EDGE_DELETED, self.edge, ns=self.ns)
        unsubscribe_all(self, ns=self.ns)

    def select(self):
        self.canvas.itemconfig(self._line, fill="blue")

    def deselect(self):
        self.canvas.itemconfig(self._line, fill="black")


class GraphEdgeDrawController(EdgeDrawController):
    def create_line(self, coords):
        return self.canvas.create_line(*coords,
                                       width=2, fill='black',
                                       tags=(self.get_tag(), self.get_tag() + "_l", "line", "edge"))

    def update_edge(self, msg):
        super().update_edge(msg)
        # self.canvas.itemconfig(self._weight, text="")

    def create_edge(self):
        super().create_edge()
        self.update_edge(None)


class DAGEdgeDrawController(EdgeDrawController):
    def create_line(self, coords):
        return self.canvas.create_line(*coords,
                                       width=2, fill='black', arrow="last",
                                       tags=(self.get_tag(), self.get_tag() + "_l", "line", "edge"))
