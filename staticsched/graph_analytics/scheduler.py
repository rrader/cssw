from staticsched.graph_analytics.cpu_priorities import BaseCPUPrioritizationPolicy
from staticsched.graph_analytics.raw_graph import DAG, Graph
from staticsched.graph_analytics.task_queues import BaseQueueGenerationPolicy


class BaseScheduler:
    def __init__(self, dag: DAG, system: Graph,
                 queue_generation_policy: BaseQueueGenerationPolicy,
                 cpu_priorities_policy: BaseCPUPrioritizationPolicy):
        self.system = system
        self.dag = dag
        self.queue_generation_policy = queue_generation_policy
        self.cpu_priorities_policy = cpu_priorities_policy

    def schedule(self):
        task_queue = self.task_queue()
        cpu_priorities = self.cpu_priorities()

    def task_queue(self):
        return self.queue_generation_policy.get_queue(self.dag)

    def cpu_priorities(self):
        return self.cpu_priorities_policy.get_priorities(self.system)

# class Scheduler(BaseScheduler):
#     def schedule(self):
#         pass
