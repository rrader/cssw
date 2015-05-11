from unittest import TestCase
from staticsched.graph_analytics.cpu_priorities import CohesionCPUPrioritizationPolicy
from staticsched.graph_analytics.raw_graph import Graph


class TestCohesionCPUPrioritizationPolicy(TestCase):
    def test_get_priorities(self):
        #        id1
        #      /  |  \
        #   id0   |  id2
        #      \  |  /
        #        id3
        graph = Graph()
        n0 = graph.add_node(0, 0, 1, "id0")
        n1 = graph.add_node(0, 0, 1, "id1")
        n2 = graph.add_node(0, 0, 1, "id2")
        n3 = graph.add_node(0, 0, 1, "id3")

        graph.add_edge("id0", "id1", 1)
        graph.add_edge("id0", "id3", 1)
        graph.add_edge("id2", "id1", 1)
        graph.add_edge("id2", "id3", 1)
        graph.add_edge("id1", "id3", 1)

        policy = CohesionCPUPrioritizationPolicy()
        priorities = policy.get_priorities(graph)

        self.assertIn(n1.n_id, priorities[:2])
        self.assertIn(n3.n_id, priorities[:2])
        self.assertIn(n0.n_id, priorities[2:])
        self.assertIn(n2.n_id, priorities[2:])
