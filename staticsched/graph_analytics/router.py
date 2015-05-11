from staticsched.graph_analytics.gantt import System
from staticsched.graph_analytics.raw_graph import Graph


class Router:
    def __init__(self, graph: Graph):
        self._graph = graph

    def route(self, m_time, source, target):
        raise NotImplemented()


class SystemAwareRouter(Router):
    def __init__(self, graph: Graph, system: System):
        super().__init__(graph)
        self._system = system


class AnyPathRouter(Router):
    def route(self, m_time, source, target):
        source = self._graph.nodes[source]
        target = self._graph.nodes[target]
        return self.find_path(source, target)

    def find_path(self, source, target, path=None):
        if not path:
            path = list()

        path = path + [source]
        if source == target:
            return path

        for vertex in self._graph.get_neighbours(source):
            if vertex not in path:
                extended_path = self.find_path(vertex,
                                               target,
                                               path)
                if extended_path:
                    return extended_path
        return None


class DFSRouter(Router):
    def route(self, m_time, source, target):
        source = self._graph.nodes[source]
        target = self._graph.nodes[target]
        return self.find_shortest_path(source, target)

    def find_shortest_path(self, start, end, path=None):
        if not path:
            path = list()

        path = path + [start]
        if start == end:
            return path

        shortest = None
        for node in self._graph.get_neighbours(start):
            if node not in path:
                newpath = self.find_shortest_path(node, end, path)
                if newpath:
                    if not shortest or len(newpath) < len(shortest):
                        shortest = newpath
        return shortest
