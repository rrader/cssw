import uuid


class GeneralGraph:
    def __init__(self):
        self.nodes = {}
        self.edges = []
        self.graph_id = uuid.uuid4().hex[:8]

    def add_node(self, x, y, weight, n_id=None, **kwargs):
        if not n_id:
            n_id = uuid.uuid4().hex[:8]
        node = Node(n_id, x, y, weight)
        self.nodes[n_id] = node
        return node

    def add_edge(self, source, target, weight, **kwargs):
        edge = Edge(self.nodes[source], self.nodes[target], weight)
        self.edges.append(edge)
        return edge

    def delete_node(self, node_id):
        if node_id in self.nodes:
            del self.nodes[node_id]

    def delete_edge(self, edge):
        if edge in self.edges:
            self.edges.remove(edge)

    def serialize(self):
        return {"nodes": [node.serialize_node() for node in self.nodes.values()],
                "edges": [edge.serialize_edge() for edge in self.edges]}

    @staticmethod
    def deserialize(target_graph, graph_info):
        for node in graph_info["nodes"]:
            target_graph.add_node(**node)
        for edge in graph_info["edges"]:
            target_graph.add_edge(**edge)

    def is_directed(self):
        raise NotImplemented()


class DAG(GeneralGraph):
    def get_neighbours(self, node, forward):
        neighbours = []
        for edge in self.edges:
            if forward:
                if edge.source.n_id == node.n_id:
                    neighbours.append(self.nodes[edge.target.n_id])
            else:
                if edge.target.n_id == node.n_id:
                    neighbours.append(self.nodes[edge.source.n_id])
        return neighbours

    def is_directed(self):
        return True


class Graph(GeneralGraph):
    def get_neighbours(self, node, forward):
        neighbours = []
        for edge in self.edges:
            if edge.source.n_id == node.n_id:
                neighbours.append(self.nodes[edge.target.n_id])
            if edge.target.n_id == node.n_id:
                neighbours.append(self.nodes[edge.source.n_id])
        return neighbours

    def is_directed(self):
        return False


class Node:
    def __init__(self, n_id, x, y, w):
        self.n_id = n_id
        self.y = y
        self.x = x
        self.weight = w

    def serialize_node(self):
        return {"x": self.x,
                "y": self.y,
                "weight": self.weight,
                "n_id": self.n_id
                }


class Edge:
    def __init__(self, source, target, w):
        self.source = source
        self.target = target
        self.weight = w

    def serialize_edge(self):
        return {"source": self.source.n_id,
                "target": self.target.n_id,
                "weight": self.weight}
