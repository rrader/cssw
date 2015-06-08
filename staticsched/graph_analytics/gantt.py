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


class System:
    def __init__(self, graph: Graph, duplex, has_io_cpu):
        self._graph = graph
        self._cpus = {}
        self._transmission_sessions = []
        self._current_session = []
        for node in graph.nodes.values():
            links_count = min(node.weight, len(self._graph.get_neighbours(node)))
            print(node.weight, "->", links_count)
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
