from staticsched.graph_analytics.analyse import find_all_critical_paths


class BaseQueueGenerationPolicy:
    def get_queue(self, dag):
        raise NotImplemented()


class QueueGenerationPolicy3(BaseQueueGenerationPolicy):
    def get_queue(self, dag):
        paths = find_all_critical_paths(dag, forward=True, weight_based=True)

        def get_weight(item):
            node_id, (weight, path) = item
            return weight, node_id
        return [path[0] for path in sorted(paths.items(), key=get_weight, reverse=True)]


class QueueGenerationPolicy4(BaseQueueGenerationPolicy):
    def get_queue(self, dag):
        paths = find_all_critical_paths(dag, forward=True, weight_based=False)

        def get_weight(item):
            node_id, (weight, path) = item
            node = dag.nodes[node_id]
            return weight, len(dag.get_neighbours(node, forward=True) + dag.get_neighbours(node, forward=False))
        return [path[0] for path in sorted(paths.items(), key=get_weight, reverse=True)]


class QueueGenerationPolicy16(BaseQueueGenerationPolicy):
    def get_queue(self, dag):
        paths = find_all_critical_paths(dag, forward=False, weight_based=True)

        def get_weight(item):
            node_id, (weight, path) = item
            return weight
        return [path[0] for path in sorted(paths.items(), key=get_weight)]
