from staticsched.graph_analytics.analyse import find_all_critical_paths


class BaseQueueGenerationPolicy:
    def get_queue(self, dag):
        raise NotImplemented()


class QueueGenerationPolicy2(BaseQueueGenerationPolicy):
    def get_queue(self, dag):
        paths_down = find_all_critical_paths(dag, forward=True, weight_based=True)
        paths_up = find_all_critical_paths(dag, forward=False, weight_based=True)

        def get_weight(item):
            node_id, (weight, path) = item
            return weight, node_id

        _, (max_critical_path_weight, _) = max(paths_down.items(), key=get_weight)

        def difference(node_id):
            early_time, _ = paths_up[node_id]
            later_time, _ = paths_down[node_id]
            return max_critical_path_weight - early_time - later_time

        return [node for node in sorted(dag.nodes.keys(), key=difference)]


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
