from staticsched.ui.notification_consts import *
from staticsched.ui.notifications import subscribe, notify, unsubscribe_all


NODE_RADIUS = 20

ANIMATION_STEP_FACTOR = 0.1
ANIMATION_TIME = 25


class NodeDrawController:
    def __init__(self, canvas, node, ns):
        self.ns = ns
        self.node = node
        self.canvas = canvas
        self._shape = None
        self._separator = None
        self._identifier = None
        self._weight = None
        self.x_rad = NODE_RADIUS / 4
        self.create_shape()
        self.connecting_started_with = None
        subscribe(NODE_CHANGED.format(self.node.n_id), self.node_changed, ns=self.ns)

    def get_tag(self):
        tag = "item_{}".format(self.node.n_id)
        return tag

    def get_tag_shape(self):
        return self.get_tag() + "_o"

    def create_shape(self):
        raise NotImplemented()

    def on_weight_click(self, event):
        notify(NODE_WEIGHT_REQUEST, self.node, ns=self.ns)

    def arrow_drag(self, event):
        notify(FAKE_NODE_DRAG_EVENT, (event.x, event.y), ns=self.ns)

    def delete(self):
        self.canvas.delete(self._identifier)
        self.canvas.delete(self._separator)
        self.canvas.delete(self._weight)
        self.canvas.delete(self._shape)
        notify(DELETE_NODE.format(self.node.n_id), self.node.n_id, ns=self.ns)
        notify(NODE_DELETED, self.node.n_id, ns=self.ns)
        unsubscribe_all(self, ns=self.ns)

    def node_move(self, event):
        items = self.canvas.find_withtag(self.get_tag())
        for i in items:
            self.canvas.move(i, (event.x - self.node.x),
                                (event.y - self.node.y))
        self.node.x = event.x
        self.node.y = event.y
        notify(NODE_CHANGED.format(self.node.n_id), None, ns=self.ns)

    def start_connecting(self, event):
        notify(CONNECT_START, self.node.n_id, ns=self.ns)

    def get_weight_tag(self):
        return self.get_tag() + "_w"

    def bind_events(self):
        self.canvas.tag_bind(self.get_tag(), "<ButtonPress-3>", self.start_connecting)
        self.canvas.tag_bind(self.get_tag(), "<B3-Motion>", self.arrow_drag)
        self.canvas.tag_bind(self.get_tag(), "<B1-Motion>", self.node_move)
        self.canvas.tag_bind(self.get_weight_tag(), "<ButtonPress-1>", self.on_weight_click)

    def animate_showing(self):
        if self.x_rad >= NODE_RADIUS:
            self.draw_info()

            self.bind_events()
            return
        shape = self.canvas.find_withtag(self.get_tag_shape())
        self.x_rad += NODE_RADIUS * ANIMATION_STEP_FACTOR
        x, y, rad = self.node.x, self.node.y, NODE_RADIUS
        self.canvas.coords(shape, (x-self.x_rad, y-rad, x+self.x_rad, y+rad))
        self.canvas.after(ANIMATION_TIME, self.animate_showing)

    def draw_info(self):
        raise NotImplemented()

    def node_changed(self, event):
        self.canvas.itemconfig(self._weight, text=str(self.node.weight))

    def deselect(self):
        shape = self.canvas.find_withtag(self.get_tag_shape())
        self.canvas.itemconfig(shape, outline="black")

    def select(self):
        shape = self.canvas.find_withtag(self.get_tag_shape())
        self.canvas.itemconfig(shape, outline="blue")

    def reset_mark(self):
        shape = self.canvas.find_withtag(self.get_tag_shape())
        self.canvas.itemconfig(shape, outline="black")

    def mark(self):
        shape = self.canvas.find_withtag(self.get_tag_shape())
        self.canvas.itemconfig(shape, outline="red")


class DAGNodeDrawController(NodeDrawController):
    def create_shape(self):
        x, y, rad = self.node.x, self.node.y, NODE_RADIUS
        tag = self.get_tag()
        self._shape = self.canvas.create_oval(x-self.x_rad, y-rad, x+self.x_rad, y+rad,
                                              width=2, fill='white',
                                              tags=(tag, self.get_tag_shape(), "node", "node_shape"))

        self.canvas.after(ANIMATION_TIME, self.animate_showing)

    def draw_info(self):
        x, y, rad = self.node.x, self.node.y, NODE_RADIUS
        tag = self.get_tag()
        self._identifier = self.canvas.create_text(x, y-rad/2,
                                                   text=str(self.node.n_id[:3]),
                                                   tags=(tag, tag+"_n", "node"))
        self._separator = self.canvas.create_line(x-rad, y, x+rad, y,
                                                  width=2, fill='black',
                                                  tags=(tag, tag+"_l", "node"))
        self._weight = self.canvas.create_text(x, y+rad/2,
                                               text=str(self.node.weight),
                                               activefill='blue',
                                               tags=(tag, self.get_weight_tag(), "node"))


class GraphNodeDrawController(NodeDrawController):
    def create_shape(self):
        x, y, rad = self.node.x, self.node.y, NODE_RADIUS
        tag = self.get_tag()
        self._shape = self.canvas.create_rectangle(x-self.x_rad, y-rad, x+self.x_rad, y+rad,
                                                   width=2, fill='white',
                                                   tags=(tag, self.get_tag_shape(), "node", "node_shape"))

        self.canvas.after(ANIMATION_TIME, self.animate_showing)

    def draw_info(self):
        x, y, rad = self.node.x, self.node.y, NODE_RADIUS
        tag = self.get_tag()
        self._identifier = self.canvas.create_text(x, y-rad/4,
                                                   text=str(self.node.n_id[:3]),
                                                   tags=(tag, tag+"_n", "node"))
        self._weight = self.canvas.create_text(x, y+rad/2,
                                               text=str(self.node.weight),
                                               activefill='blue',
                                               tags=(tag, self.get_weight_tag(), "node"))
