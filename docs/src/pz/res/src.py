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


def find_critical_path(graph, forward=True, weight_based=True):
    all_paths = find_all_critical_paths(graph, forward, weight_based)
    return max(all_paths.values())




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






from collections import namedtuple
from itertools import chain
from staticsched.graph_analytics.raw_graph import Graph


class ScheduledTask:
    def __init__(self, task_name, start, end, cpu):
        self.range = start, end
        self.task_name = task_name
        self.cpu = cpu

    def cancel(self):
        self.cpu.cancel_calculation(self)


SegmentMeta = namedtuple("SegmentMeta", ["source", "out_task", "target", "in_task"])


class ScheduledTransmission:
    def __init__(self, source, target, duration, route):
        self.source = source
        self.target = target
        self.duration = duration
        self.route = route
        self._segments = []
        self._segment_meta = {}
        self.source_cpu, self.target_cpu = route[0][0], route[-1][-1],

    def add_segment(self, source, task_outgoing, target, task_incoming):
        self._segments.append(task_incoming)
        self._segments.append(task_outgoing)

        segment_info = SegmentMeta(source, task_outgoing, target, task_incoming)
        self._segment_meta[task_outgoing] = segment_info
        self._segment_meta[task_incoming] = segment_info

    def get_task_meta(self, task):
        return self._segment_meta[task]

    def end_time(self):
        return max((segment.range[1] for segment in self._segments))

    def cancel(self):
        for segment in self._segments:
            segment.cancel()


class ScheduledEmptyTransmission(ScheduledTransmission):
    def __init__(self, source_task, target_task, source_cpu, target_cpu, prev_task_ready_time):
        super().__init__(source_task, target_task, 0, [(source_cpu, target_cpu)])
        self.ready_time = prev_task_ready_time

    def end_time(self):
        return self.ready_time


class ScheduledTransmissionSegment:
    INGOING = 0
    OUTGOING = 1

    def __init__(self, transmission, start, end, communication_cpu, direction, link):
        self.range = start, end
        self.transmission = transmission
        self.direction = direction
        self.communication_cpu = communication_cpu
        self.link = link

    def meta(self):
        return self.transmission.get_task_meta(self)

    def cancel(self):
        self.link.cancel_transmission(self)


class Link:
    def __init__(self, cpu, link_id, duplex):
        self.cpu = cpu
        self.duplex = duplex
        self.link_id = link_id
        self._io_tasks = []

    def schedule_transmission(self, transmission, m_time, duration, direction, communication_cpu):
        task = ScheduledTransmissionSegment(transmission, m_time, m_time + duration,
                                            communication_cpu, direction, self)
        self._io_tasks.append(task)
        return task

    def cancel_transmission(self, task):
        self._io_tasks.remove(task)

    def is_link_free(self, m_time, direction=None, communication_cpu=None):
        link_with_com_cpu = self.cpu.get_link_with_cpu_at_time(m_time, communication_cpu)
        if link_with_com_cpu and link_with_com_cpu != self:
            return False

        for segment in self._io_tasks:
            start, end = segment.range
            if start <= m_time < end:
                if direction is None:
                    # disrespect direction/duplex
                    return False

                if not self.duplex:
                    return False
                else:
                    # same direction is forbidden
                    if segment.direction == direction:
                        return False
                    else:
                        if segment.communication_cpu != communication_cpu:
                            # duplex only for bi-directional communication
                            # between same CPUs
                            return False
        return True

    def is_link_free_duration(self, m_time, duration, direction, communication_cpu):
        return all(self.is_link_free(time, direction, communication_cpu)
                   for time in range(m_time, m_time + duration)
                   )

    def get_connected_cpu_at_time(self, m_time):
        for segment in self._io_tasks:
            start, end = segment.range
            if start <= m_time < end:
                return segment.communication_cpu


class CPU:
    def __init__(self, cpu_id, links, duplex, has_io_cpu):
        self.cpu_id = cpu_id
        self._links = [Link(self, link_id, duplex) for link_id in range(links)]
        self._alu_tasks = []
        self._has_io_cpu = has_io_cpu

    def is_task_scheduled(self, task_name):
        return any(task.task_name == task_name for task in self._alu_tasks)

    def is_alu_free(self, m_time):
        if not self._has_io_cpu and any(not link.is_link_free(m_time) for link in self._links):
            return False

        for task in self._alu_tasks:
            start, end = task.range
            if start <= m_time < end:
                return False
        return True

    def is_alu_free_duration(self, m_time, duration):
        return all(self.is_alu_free(time)
                   for time in range(m_time, m_time + duration)
                   )

    def has_free_link(self, m_time, duration, direction, communication_cpu):
        if not self._has_io_cpu and not self.is_alu_free_duration(m_time, duration):
            return False

        return any(link.is_link_free_duration(m_time, duration, direction, communication_cpu)
                   for link in self._links)

    def any_free_link(self, m_time, duration, direction, communication_cpu):
        if not self._has_io_cpu and not self.is_alu_free_duration(m_time, duration):
            return []

        return [link for link in self._links
                if link.is_link_free_duration(m_time, duration, direction, communication_cpu)]

    def get_link_with_cpu_at_time(self, m_time, communication_cpu):
        for link in self._links:
            if link.get_connected_cpu_at_time(m_time) == communication_cpu:
                return link

    def schedule_calculation(self, task_name, m_time, duration):
        task = ScheduledTask(task_name, m_time, m_time + duration, self)
        self._alu_tasks.append(task)
        return task

    def cancel_calculation(self, task):
        self._alu_tasks.remove(task)

    def get_scheduled_task(self, task_name):
        return [task for task in self._alu_tasks if task.task_name == task_name][0]

    def schedule_transmission(self, transmission, m_time, duration, direction, communication_cpu):
        link = self.any_free_link(m_time, duration, direction, communication_cpu)[0]
        return link.schedule_transmission(transmission, m_time, duration, direction, communication_cpu)

    def finished_tasks(self, m_time):
        return [task.task_name for task in self._alu_tasks if m_time >= task.range[1]]

    def scheduled_tasks(self):
        return [task.task_name for task in self._alu_tasks]

    def last_tick(self):
        return max((task.range[1] for task in self._alu_tasks), default=0)


class System:
    def __init__(self, graph: Graph, duplex, has_io_cpu):
        self._graph = graph
        self._cpus = {}
        self._transmission_sessions = []
        self._current_session = []
        for node in graph.nodes.values():
            links_count = min(node.weight, len(self._graph.get_neighbours(node)))
            cpu = CPU(cpu_id=node.n_id, links=node.weight, duplex=duplex, has_io_cpu=has_io_cpu)
            self._cpus[node.n_id] = cpu

    def free_alu_cpus(self, m_time):
        return [cpu.cpu_id for cpu in self._cpus.values() if cpu.is_alu_free(m_time)]

    def finished_tasks(self, m_time):
        return list(chain(*[cpu.finished_tasks(m_time) for cpu in self._cpus.values()]))

    def scheduled_tasks(self):
        return list(chain(*[cpu.scheduled_tasks() for cpu in self._cpus.values()]))

    def cpus_by_scheduled_task(self, task_name):
        return [cpu for cpu in self._cpus.values() if cpu.is_task_scheduled(task_name)]

    def schedule_calculation(self, task_name, m_time, duration, cpu_id):
        cpu = self._cpus[cpu_id]
        m_time = self.find_calculation_time_range(m_time, duration, cpu)
        scheduled_task = cpu.schedule_calculation(task_name, m_time, duration)
        self._current_session.append(scheduled_task)
        return scheduled_task

    def new_session(self):
        if self._current_session:
            self._transmission_sessions.append(self._current_session)
        self._current_session = []

    def cancel_session(self):
        for transmission in self._current_session:
            transmission.cancel()

    def schedule_transmission(self, route, source_cpu, target_cpu, m_time, source_task, target_task, duration):
        if not route:
            return ScheduledEmptyTransmission(source_task, target_task, source_cpu, target_cpu, m_time)

        transmission = ScheduledTransmission(source_task, target_task, duration, route)
        for segment_source, segment_target in route:
            m_time = self.find_transmission_time_range(transmission, m_time,
                                                       self._cpus[segment_source],
                                                       self._cpus[segment_target])
            task_out = self._cpus[segment_source].schedule_transmission(transmission, m_time,
                                                                        duration,
                                                                        ScheduledTransmissionSegment.OUTGOING,
                                                                        segment_target)
            task_in = self._cpus[segment_target].schedule_transmission(transmission, m_time,
                                                                       duration,
                                                                       ScheduledTransmissionSegment.INGOING,
                                                                       segment_source)

            transmission.add_segment(segment_source, task_in, segment_target, task_out)
            m_time += duration
            assert transmission.end_time() == m_time

        self._current_session.append(transmission)
        return transmission

    @staticmethod
    def find_transmission_time_range(transmission, m_time, segment_source_cpu, segment_target_cpu):
        outgoing_time_found = False
        ingoing_time_found = False
        while (not ingoing_time_found) or (not outgoing_time_found):
            while not segment_source_cpu.has_free_link(m_time, transmission.duration,
                                                       ScheduledTransmissionSegment.OUTGOING,
                                                       segment_target_cpu.cpu_id):
                m_time += 1
            outgoing_time_found = True
            while not segment_target_cpu.has_free_link(m_time, transmission.duration,
                                                       ScheduledTransmissionSegment.INGOING,
                                                       segment_source_cpu.cpu_id):
                m_time += 1
                outgoing_time_found = False
            ingoing_time_found = True
        return m_time

    @staticmethod
    def find_calculation_time_range(m_time, duration, cpu):
        while not cpu.is_alu_free_duration(m_time, duration):
            m_time += 1
        return m_time

    def duration(self):
        return max((cpu.last_tick() for cpu in self._cpus.values()), default=0)




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







def cpu_by_priority(cpus, cpu_priorities):
    return sorted(cpus, key=lambda cpu: cpu_priorities.index(cpu))[0]


class PriorityCPUSelector:
    def choose_cpu(self, m_time, task):
        cpus = self._system.free_alu_cpus(m_time)
        if cpus:
            return cpu_by_priority(cpus, self.cpu_priorities())


class NearestTransferCPUSelector:
    def choose_cpu(self, m_time, task):
        free_cpus = self._system.free_alu_cpus(m_time)
        if free_cpus:
            # parent_tasks = self._dag.get_neighbours(task, forward=False)
            transfers = self._dag.edges_to_node(task)

            cpus_transfer_time = {}
            for target_cpu in free_cpus:
                transfer_times = {}
                for edge in transfers:
                    source_cpu = self._system.cpus_by_scheduled_task(edge.source.n_id)[0].cpu_id
                    route = self.get_route(m_time, source_cpu, target_cpu)

                    transfer_time_from_cpu = transfer_times.get(source_cpu, 0)
                    transfer_times[source_cpu] = transfer_time_from_cpu + len(route) * edge.weight
                cpus_transfer_time[target_cpu] = sum(transfer_times.values())

            min_transfer_time = min(cpus_transfer_time.values())
            cpus_with_min_transfer_time = [cpu_id for cpu_id, transfer_time in cpus_transfer_time.items()
                                           if transfer_time == min_transfer_time]

            return cpu_by_priority(cpus_with_min_transfer_time, self.cpu_priorities())


class ModellingTransferCPUSelector:
    def choose_cpu(self, m_time, task):
        cpu_times = {}
        for cpu in self._system._cpus:
            ready_time = self.schedule_transmits(task, m_time, cpu)
            scheduled_task = self._system.schedule_calculation(task.n_id, ready_time, task.weight, cpu)
            cpu_times[cpu] = scheduled_task.range[0]
            self._system.cancel_session()

        nearest_time = min(cpu_times.values())
        best_cpus = [cpu for cpu in cpu_times.keys() if cpu_times[cpu] == nearest_time]
        return cpu_by_priority(best_cpus, self.cpu_priorities())
