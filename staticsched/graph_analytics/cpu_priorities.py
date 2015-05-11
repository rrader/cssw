class BaseCPUPrioritizationPolicy:
    def get_priorities(self, graph):
        raise NotImplemented()


class CohesionCPUPrioritizationPolicy(BaseCPUPrioritizationPolicy):
    def get_priorities(self, graph):
        nodes = graph.nodes.values()
        sorted_nodes = sorted(nodes, key=lambda node: len(graph.get_neighbours(node)), reverse=True)
        return [node.n_id for node in sorted_nodes]
