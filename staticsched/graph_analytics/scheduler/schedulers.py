from staticsched.graph_analytics.cpu_priorities import BaseCPUPrioritizationPolicy
from staticsched.graph_analytics.gantt import System
from staticsched.graph_analytics.raw_graph import DAG, Graph
from staticsched.graph_analytics.router import Router
from staticsched.graph_analytics.scheduler.cpu_selectors import PriorityCPUSelector, NearestTransferCPUSelector, \
    ModellingTransferCPUSelector
from staticsched.graph_analytics.scheduler.transmit_schedulers import NoAdvanceTransmissionScheduler, \
    AdvanceTransmissionScheduler
from staticsched.graph_analytics.task_queues import BaseQueueGenerationPolicy


class TasksQueueController:
    def __init__(self, dag: DAG, tasks_queue, system):
        self._dag = dag
        self._queue = tasks_queue

        self._system = system

    def ready(self, m_time):
        finished = self._system.finished_tasks(m_time)
        scheduled = self._system.scheduled_tasks()
        ready_nodes = []
        for node in self._dag.nodes.values():
            if node.n_id in scheduled:
                continue

            parents = self._dag.get_neighbours(node, forward=False)
            if all((node.n_id in finished) for node in parents):
                ready_nodes.append(node)
        ready_nodes_sorted = sorted(ready_nodes,
                                    key=lambda node: self._queue.index(node.n_id))
        return ready_nodes_sorted

    def done(self, m_time):
        finished = self._system.finished_tasks(m_time)
        return len(self._queue) <= len(finished)


class BaseScheduler:
    def __init__(self, dag: DAG, system_graph: Graph,
                 queue_generation_policy: BaseQueueGenerationPolicy,
                 cpu_priorities_policy: BaseCPUPrioritizationPolicy,
                 system: System,
                 router: Router):
        self._system_graph = system_graph
        self._dag = dag
        self._queue_generation_policy = queue_generation_policy
        self._cpu_priorities_policy = cpu_priorities_policy
        self._system = system
        self._router = router

    def schedule_dag(self):
        m_time = 0
        task_queue = self.task_queue()

        while not task_queue.done(m_time):
            ready_tasks = task_queue.ready(m_time)
            while ready_tasks:
                for task in ready_tasks:
                    if self.schedule_task(m_time, task):
                        break
                else:
                    break
                ready_tasks = task_queue.ready(m_time)

            m_time += 1

    def schedule_task(self, m_time, task):
        chosen_cpu = self.choose_cpu(m_time, task)
        if chosen_cpu:
            m_time = self.schedule_transmits(task, m_time, chosen_cpu)
            self._system.schedule_calculation(task.n_id, m_time, task.weight, chosen_cpu)
            return True
        return False

    def choose_cpu(self, m_time, task):
        raise NotImplemented()

    def schedule_transmits(self, task, m_time, target_cpu):
        raise NotImplemented()

    def task_queue(self):
        return TasksQueueController(self._dag,
                                    self._queue_generation_policy.get_queue(self._dag),
                                    self._system)

    def cpu_priorities(self):
        return self._cpu_priorities_policy.get_priorities(self._system_graph)

    def get_route(self, m_time, source_cpu, target_cpu):
        route = self._router.route(m_time, source_cpu, target_cpu)
        route = [node.n_id for node in route]
        route = list(zip(route, route[1:]))
        return route


class DummyScheduler(PriorityCPUSelector, NoAdvanceTransmissionScheduler,
                     BaseScheduler):
    """
    Schedules DAG by CPU priorities
    """
    pass


class NeighbourScheduler(NearestTransferCPUSelector,
                         NoAdvanceTransmissionScheduler,
                         BaseScheduler):
    """
    Schedules DAG by neighbour appointment (no advance transmits)
    """
    pass


class AdvanceNeighbourScheduler(NearestTransferCPUSelector,
                                AdvanceTransmissionScheduler,
                                BaseScheduler):
    """
    Schedules DAG by neighbour appointment (advance transmits)
    """
    pass


class ModellingNeighbourScheduler(ModellingTransferCPUSelector,
                                  AdvanceTransmissionScheduler,
                                  BaseScheduler):
    """
    Schedules DAG by neighbour appointment (advance transmits)
    Tries to schedule on any CPU to get the best time
    """
    pass
