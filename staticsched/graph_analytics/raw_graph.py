from random import randint, sample, normalvariate
import uuid
import warnings


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
        if isinstance(source, str):
            source = self.nodes[source]
        assert isinstance(source, Node)
        if isinstance(target, str):
            target = self.nodes[target]
        assert isinstance(target, Node)

        edge = Edge(source, target, weight)
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
    def deserialize(target_graph, graph_info, override_node={}):
        for node in graph_info["nodes"]:
            node.update(override_node)
            target_graph.add_node(**node)
        for edge in graph_info["edges"]:
            target_graph.add_edge(**edge)

    def is_directed(self):
        raise NotImplemented()

    def re_enumerate(self):
        y_sorted_nodes = sorted(self.nodes.values(), key=lambda node: (node.y, node.x))
        for i, node in enumerate(y_sorted_nodes):
            node.n_id = str(i)


def norm_weight(weight, min_w, max_w, avg):
    if weight < min_w:
        return min_w
    elif avg > max_w:
        return weight
    elif weight > max_w:
        return max_w
    else:
        return weight


class DAG(GeneralGraph):
    def get_neighbours(self, node, forward=True):
        neighbours = []
        for edge in self.edges:
            if forward:
                if edge.source.n_id == node.n_id:
                    neighbours.append(self.nodes[edge.target.n_id])
            else:
                if edge.target.n_id == node.n_id:
                    neighbours.append(self.nodes[edge.source.n_id])
        return neighbours

    def edges_to_node(self, node):
        edges = []
        for edge in self.edges:
            if edge.target.n_id == node.n_id:
                edges.append(edge)
        return edges

    def is_directed(self):
        return True

    def levels(self):
        levels = []
        ready = []

        while len(ready) < len(self.nodes):
            level = []
            for node in self.nodes.values():
                if node.n_id in ready:
                    continue
                inputs = [inp.source for inp in self.edges if inp.target.n_id == node.n_id]
                if all((source.n_id in ready) for source in inputs):
                    level.append(node.n_id)
            levels.append(level)
            ready += level
        return levels

    def arrange(self):
        width = 600
        levels = self.levels()
        y = 40
        for level in levels:
            x = 50 #150 - len(level)*20
            for n_id in level:
                self.nodes[n_id].x = x
                self.nodes[n_id].y = y
                x += width / len(level)
            y += 130

    def correlatio(self):
        w_nodes = 0
        for node in self.nodes.values():
            w_nodes += node.weight

        w_edges = 0
        for edge in self.edges:
            w_edges += edge.weight

        return w_nodes/(w_edges + w_nodes)

    @classmethod
    def generate(cls,
                 min_weight, max_weight,
                 count, connectivity, connections_percent,
                 min_edge_weight=1, max_edge_weight=9999):
        graph = DAG()
        sum_weight = 0
        for i in range(count):
            weight = randint(min_weight, max_weight)
            graph.add_node(randint(0, 300), randint(0, 300), weight, str(i))
            sum_weight += weight

        sum_edges_weight = (sum_weight - connectivity*sum_weight) / connectivity

        max_edges_count = (count*(count-1)) / 2
        edges_count = int(connections_percent/100*max_edges_count)

        pairs = [(str(i), str(j)) for i in range(count) for j in range(i+1, count)]
        # 1 1 30 0.1 10 1 500
        sum_edges_weight_actual = 0
        last_edge = None
        added_edges_count = 0
        average_edge_weight = sum_edges_weight / edges_count
        for source, target in sample(pairs, edges_count):
            average_edge_weight = max(1, ((sum_edges_weight - sum_edges_weight_actual) / (edges_count - added_edges_count)))
            weight = int(normalvariate(average_edge_weight, average_edge_weight/4))
            weight = norm_weight(weight, min_edge_weight, max_edge_weight, average_edge_weight)
            if sum_edges_weight - (sum_edges_weight_actual + weight) < 0:
                weight = max(1, int(sum_edges_weight - sum_edges_weight_actual))
                last_edge = graph.add_edge(source, target, weight)
                sum_edges_weight_actual += weight
                warnings.warn("Stopped, maximum reached: last edge weight was {} < {} < {}".
                              format(min_edge_weight, weight, max_edge_weight))
                break
            last_edge = graph.add_edge(source, target, weight)
            sum_edges_weight_actual += weight
            added_edges_count += 1
        else:
            weight = int(sum_edges_weight - sum_edges_weight_actual)
            if weight <= 0:
                weight = 1
            last_edge.weight = weight
            expected_weight = norm_weight(weight, min_edge_weight, max_edge_weight, average_edge_weight)
            if expected_weight != weight:
                warnings.warn("Last edge weight was out of bounds {} < {} < {}".
                              format(min_edge_weight, weight, max_edge_weight))

        graph.arrange()
        return graph

    def duration_on_one_cpu(self):
        return sum(node.weight for node in self.nodes.values())


class Graph(GeneralGraph):
    def get_neighbours(self, node, forward=None):
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
