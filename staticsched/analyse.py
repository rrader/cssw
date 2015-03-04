def find_cycle_to_ancestor(spanning_tree, node, ancestor):
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
                    cycle = find_cycle_to_ancestor(spanning_tree, node, each)
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
