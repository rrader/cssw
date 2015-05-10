def _find_cycle_to_ancestor(spanning_tree, node, ancestor):
    path = []
    while node.n_id != ancestor.n_id:
        path.append(node.n_id)
        node = spanning_tree[node.n_id]
        if node is None:
            return []
    path.append(node.n_id)
    path.reverse()
    return path


def find_all_cycles(graph):
    def dfs(node):
        visited.add(node.n_id)
        for each in graph.get_neighbours(node):
            if each.n_id not in visited:
                spanning_tree[each.n_id] = node
                dfs(each)
            else:
                if spanning_tree[node.n_id] != each:
                    cycle = _find_cycle_to_ancestor(spanning_tree, node, each)
                    if cycle:
                        cycles.append(cycle)

    visited = set()
    spanning_tree = {}
    cycles = []

    for each in graph.nodes.values():
        if each.n_id not in visited:
            spanning_tree[each.n_id] = None
            dfs(each)

    return cycles


def is_connected(graph):
    def dfs(node):
        visited.add(node.n_id)
        for each in graph.get_neighbours(node):
            if each.n_id not in visited:
                dfs(each)

    visited = set()
    nodes = list(graph.nodes.values())
    dfs(nodes[0])
    return len(visited) == len(nodes)


def dfs_caching(graph, aggregator, transformator, forward):
    def dfs(start_node):
        if start_node.n_id in result:
            return result[start_node.n_id]

        if forward:
            ways = [dfs(each) for each in graph.get_neighbours(start_node, forward=forward)]
            way = aggregator(ways)
            calculated = transformator(start_node, way)
        else:
            ways = [transformator(each, dfs(each)) for each in graph.get_neighbours(start_node, forward=forward)]
            way = aggregator(ways)
            calculated = way
        result[node.n_id] = calculated
        return calculated

    result = {}
    for node in graph.nodes.values():
        result[node.n_id] = dfs(node)
    return result


def find_all_critical_paths(graph, forward, weight_based):
    if forward:
        def aggregation(ways):
            return max(ways, key=lambda x: x[0], default=(0, []))
    else:
        def aggregation(ways):
            return max(ways, key=lambda x: x[0], default=(0, []))

    if weight_based:
        def transformation(current_node, length):
            return length[0] + current_node.weight, [current_node.n_id] + length[1]
    else:
        def transformation(current_node, length):
            return length[0] + 1, [current_node.n_id] + length[1]

    all_paths = dfs_caching(graph, aggregation, transformation, forward)
    return all_paths


def generate_queue_3(graph):
    paths = find_all_critical_paths(graph, forward=True, weight_based=True)

    def get_weight(item):
        node_id, (weight, path) = item
        return weight
    return [path[0] for path in sorted(paths.items(), key=get_weight, reverse=True)]


def generate_queue_4(graph):
    paths = find_all_critical_paths(graph, forward=True, weight_based=False)

    def get_weight(item):
        node_id, (weight, path) = item
        node = graph.nodes[node_id]
        return weight, len(graph.get_neighbours(node, forward=True) + graph.get_neighbours(node, forward=False))
    return [path[0] for path in sorted(paths.items(), key=get_weight, reverse=True)]


def generate_queue_16(graph):
    paths = find_all_critical_paths(graph, forward=False, weight_based=True)

    def get_weight(item):
        node_id, (weight, path) = item
        return weight
    return [path[0] for path in sorted(paths.items(), key=get_weight)]


def find_critical_path(graph, forward=True, weight_based=True):
    all_paths = find_all_critical_paths(graph, forward, weight_based)
    return max(all_paths.values())
