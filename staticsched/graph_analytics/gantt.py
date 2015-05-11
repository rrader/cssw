from collections import namedtuple
from itertools import chain
from staticsched.graph_analytics.raw_graph import Graph


class ScheduledTask:
    def __init__(self, task_name, start, end):
        self.range = start, end
        self.task_name = task_name


SegmentMeta = namedtuple("SegmentMeta", ["source", "out_task", "target", "in_task"])


class ScheduledTransmission:
    def __init__(self, source, target, duration, route):
        self.source = source
        self.target = target
        self.duration = duration
        self.route = route
        self._segments = []
        self._segment_meta = {}
        self.source_cpu, self.target_cpu = route[0][0], route[-1][-1]

    def add_segment(self, source, task_outgoing, target, task_incoming):
        self._segments.append(task_incoming)
        self._segments.append(task_outgoing)

        segment_info = SegmentMeta(source, task_outgoing, target, task_incoming)
        self._segment_meta[task_outgoing] = segment_info
        self._segment_meta[task_incoming] = segment_info

    def get_task_meta(self, task):
        return self._segment_meta[task]


class ScheduledTransmissionSegment:
    INGOING = 0
    OUTGOING = 1

    def __init__(self, transmission, start, end, direction):
        self.range = start, end
        self.transmission = transmission
        self.direction = direction

    def meta(self):
        return self.transmission.get_task_meta(self)


class Link:
    def __init__(self, link_id, duplex):
        self.duplex = duplex
        self.link_id = link_id
        self._io_tasks = []

    def schedule_transmission(self, transmission, m_time, duration, direction):
        task = ScheduledTransmissionSegment(transmission, m_time, m_time + duration, direction)
        self._io_tasks.append(task)
        return task

    def is_link_free(self, m_time, direction):
        for segment in self._io_tasks:
            start, end = segment.range
            if start <= m_time < end:
                if not self.duplex:
                    return False
                else:
                    if segment.direction == direction:
                        return False
        return True

    def is_link_free_duration(self, m_time, duration, direction):
        return all(self.is_link_free(time, direction)
                   for time in range(m_time, m_time + duration)
                   )


class CPU:
    def __init__(self, cpu_id, links, duplex, has_io_cpu):
        self.cpu_id = cpu_id
        self._links = [Link(link_id, duplex) for link_id in range(links)]
        self._alu_tasks = []
        self._has_io_cpu = has_io_cpu

    def is_task_scheduled(self, task_name):
        return any(task.task_name == task_name for task in self._alu_tasks)

    def is_alu_free(self, m_time):
        for task in self._alu_tasks:
            start, end = task.range
            if start <= m_time < end:
                return False
        return True

    def has_free_link(self, m_time, duration, direction):
        return any(link.is_link_free_duration(m_time, duration, direction) for link in self._links)

    def any_free_link(self, m_time, duration, direction):
        return [link for link in self._links if link.is_link_free_duration(m_time, duration, direction)]

    def schedule_calculation(self, task_name, m_time, duration):
        task = ScheduledTask(task_name, m_time, m_time + duration)
        self._alu_tasks.append(task)

    def schedule_transmission(self, transmission, m_time, duration, direction):
        link = self.any_free_link(m_time, duration, direction)[0]
        return link.schedule_transmission(transmission, m_time, duration, direction)

    def finished_tasks(self, m_time):
        return [task.task_name for task in self._alu_tasks if m_time >= task.range[1]]

    def scheduled_tasks(self):
        return [task.task_name for task in self._alu_tasks]


class System:
    def __init__(self, graph: Graph, duplex, has_io_cpu):
        self._graph = graph
        self._cpus = {}
        for node in graph.nodes.values():
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

    def schedule_calculation(self, task_name, m_time, duration, cpu):
        self._cpus[cpu].schedule_calculation(task_name, m_time, duration)

    def schedule_transmission(self, route, m_time, source_task, target_task, duration):
        transmission = ScheduledTransmission(source_task, target_task, duration, route)
        for segment_source, segment_target in route:
            m_time = self.find_transmission_time_range(transmission, m_time,
                                                       self._cpus[segment_source],
                                                       self._cpus[segment_target])
            task_out = self._cpus[segment_source].schedule_transmission(transmission, m_time,
                                                                        duration,
                                                                        ScheduledTransmissionSegment.OUTGOING)
            task_in = self._cpus[segment_target].schedule_transmission(transmission, m_time,
                                                                       duration,
                                                                       ScheduledTransmissionSegment.INGOING)

            transmission.add_segment(segment_source, task_in, segment_target, task_out)
            m_time += duration
        return m_time

    @staticmethod
    def find_transmission_time_range(transmission, m_time, segment_source_cpu, segment_target_cpu):
        outgoing_time_found = False
        ingoing_time_found = False
        while (not ingoing_time_found) or (not outgoing_time_found):
            while not segment_source_cpu.has_free_link(m_time, transmission.duration,
                                                       ScheduledTransmissionSegment.OUTGOING):
                m_time += 1
            outgoing_time_found = True
            while not segment_target_cpu.has_free_link(m_time, transmission.duration,
                                                       ScheduledTransmissionSegment.INGOING):
                m_time += 1
                outgoing_time_found = False
            ingoing_time_found = True
        return m_time
